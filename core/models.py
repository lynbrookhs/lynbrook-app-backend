import random
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import *
from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.models.fields import ArrayField

from core import wordle
from core.notifications import send_notifications

USER_MODEL = settings.AUTH_USER_MODEL


def random_code():
    return random.randint(100000, 999999)


class UserType(IntegerChoices):
    STUDENT = 1
    STAFF = 2
    GUEST = 3


class DayOfWeek(IntegerChoices):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class OrganizationType(IntegerChoices):
    GLOBAL = 1
    CLASS = 2
    CLUB = 3


class ClubCategory(IntegerChoices):
    SERVICE = 1
    COMPETITION = 2
    INTEREST = 3


class PollType(IntegerChoices):
    SELECT = 1
    SHORT_ANSWER = 2


class EventSubmissionType(IntegerChoices):
    CODE = 1
    FILE = 2


class LowercaseEmailField(EmailField):
    def to_python(self, value):
        value = super().to_python(value)
        if isinstance(value, str):
            return value.lower()
        return value


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["type"]
    objects = UserManager()

    username = None
    email = LowercaseEmailField(_("email address"), unique=True)
    type = IntegerField(choices=UserType.choices)
    grad_year = IntegerField(choices=[(x, x) for x in range(2022, 2029)], null=True, blank=True)

    organizations = ManyToManyField("Organization", through="Membership", related_name="users")
    picture_url = URLField(
        default="https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png"
    )

    wordle_streak = IntegerField(default=0)

    def __str__(self):
        if self.grad_year is None:
            return f"{self.first_name} {self.last_name} ({self.email})"
        return f"{self.first_name} {self.last_name}, {self.grad_year} ({self.email})"

    def to_json(self):
        return dict(
            id=self.pk,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            grad_year=self.grad_year,
        )


class ExpoPushToken(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="expo_push_tokens")
    token = CharField(max_length=200, unique=True)


class Organization(Model):
    class Meta:
        ordering = ("type", "name")
        constraints = [
            CheckConstraint(
                name="%(app_label)s_%(class)s_type",
                check=(
                    Q(
                        type=OrganizationType.GLOBAL,
                        required=True,
                        required_grad_year__isnull=True,
                        category__isnull=True,
                    )
                    | Q(
                        type=OrganizationType.CLASS,
                        required=False,
                        required_grad_year__isnull=False,
                        category__isnull=True,
                    )
                    | Q(
                        type=OrganizationType.CLUB,
                        required=False,
                        required_grad_year__isnull=True,
                        category__isnull=False,
                    )
                ),
            )
        ]

    type = IntegerField(choices=OrganizationType.choices)
    advisors = ManyToManyField(USER_MODEL, related_name="advisor_organizations", blank=True)
    admins = ManyToManyField(USER_MODEL, related_name="admin_organizations", blank=True)

    required = BooleanField(default=False)
    required_grad_year = IntegerField(null=True, blank=True)

    name = CharField(max_length=200)
    description = TextField(blank=True)
    category = IntegerField(choices=ClubCategory.choices, null=True, blank=True)

    day = IntegerField(choices=DayOfWeek.choices, null=True, blank=True)
    location = CharField(max_length=200, blank=True)
    time = CharField(max_length=200, blank=True)
    link = URLField(null=True, blank=True)

    ical_links = ArrayField(URLField(), blank=True, default=list)

    def is_admin(self, user):
        return self.admins.filter(id=user.id).exists()

    def is_advisor(self, user):
        return self.advisors.filter(id=user.id).exists()

    def __str__(self):
        return self.name


class OrganizationLink(Model):
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="links")
    title = CharField(max_length=200)
    url = URLField()


class Membership(Model):
    class Meta:
        ordering = ("organization__type", "organization__name")
        constraints = [
            UniqueConstraint(name="%(app_label)s_%(class)s_user_organization", fields=("user", "organization"))
        ]

    user = ForeignKey(User, on_delete=CASCADE, related_name="memberships")
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="memberships")
    active = BooleanField(default=True)
    points = PositiveIntegerField(default=0)
    points_spent = PositiveIntegerField(default=0)


class Event(Model):
    class Meta:
        constraints = [
            CheckConstraint(
                name="%(app_label)s_%(class)s_submission_type_code",
                check=(
                    Q(submission_type=EventSubmissionType.CODE, code__isnull=False)
                    | (~Q(submission_type=EventSubmissionType.CODE) & Q(code__isnull=True))
                ),
            )
        ]

    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="events")

    name = CharField(max_length=200)
    description = TextField(blank=True)
    start = DateTimeField()
    end = DateTimeField()

    points = PositiveIntegerField()
    submission_type = IntegerField(choices=EventSubmissionType.choices, default=EventSubmissionType.CODE)
    code = PositiveIntegerField(null=True, blank=True)

    users = ManyToManyField(USER_MODEL, blank=True, through="Submission", related_name="events")

    def __str__(self):
        return f"{self.organization.name} • {self.name}"


class Submission(Model):
    class Meta:
        constraints = [UniqueConstraint(name="%(app_label)s_%(class)s_user_event", fields=("user", "event"))]

    user = ForeignKey(User, on_delete=CASCADE, related_name="+")
    event = ForeignKey(Event, on_delete=CASCADE, related_name="submissions")
    points = PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Only set if the number of points needs to be overriden for this user. If blank, defaults to the number of points the event is worth.",
    )
    created_at = DateTimeField(auto_now_add=True)
    file = FileField(null=True, blank=True)

    def __str__(self):
        return f"{self.event} — {self.user}"

    def get_points(self):
        return self.event.points if self.points is None else self.points


class Post(Model):
    class Meta:
        ordering = ("-date",)

    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="posts")
    title = CharField(max_length=200)
    date = DateTimeField(auto_now=True)
    content = TextField()
    published = BooleanField(default=False)

    def __str__(self):
        return self.title


class Poll(Model):
    class Meta:
        constraints = [
            CheckConstraint(
                name="%(app_label)s_%(class)s_type",
                check=(
                    Q(
                        type=PollType.SHORT_ANSWER,
                        choices__isnull=True,
                        min_values__isnull=True,
                        max_values__isnull=True,
                    )
                    | Q(
                        type=PollType.SELECT,
                        choices__isnull=False,
                        min_values__isnull=False,
                        max_values__isnull=False,
                    )
                ),
            )
        ]

    post = ForeignKey(Post, on_delete=CASCADE, related_name="polls")
    type = IntegerField(choices=PollType.choices)
    description = TextField()

    choices = ArrayField(TextField(), null=True, blank=True)
    min_values = IntegerField(validators=[MinValueValidator(1)], default=1, null=True, blank=True)
    max_values = IntegerField(validators=[MinValueValidator(1)], default=1, null=True, blank=True)

    def __str__(self):
        return self.description


class PollSubmission(Model):
    poll = ForeignKey(Poll, on_delete=CASCADE, related_name="submissions")
    user = ForeignKey(USER_MODEL, on_delete=CASCADE, related_name="+")
    responses = ArrayField(TextField())


class Prize(Model):
    class Meta:
        ordering = ("points",)

    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="prizes")

    name = CharField(max_length=200)
    description = TextField()
    points = PositiveIntegerField()

    def __str__(self):
        return self.name


class Schedule(Model):
    class Meta:
        ordering = ("-priority",)

    name = CharField(max_length=200)
    start = DateField()
    end = DateField()
    weekday = ArrayField(IntegerField(choices=DayOfWeek.choices))
    priority = IntegerField()

    @classmethod
    def get_for_day(cls, day: date):
        qs = cls.objects.filter(start__lte=day, end__gte=day, weekday__contains=[day.weekday()])
        try:
            return qs[0]
        except IndexError:
            return cls(name="No Schedule")


class Period(Model):
    id = CharField(max_length=200, primary_key=True)
    name = CharField(max_length=200)
    customizable = BooleanField()

    def __str__(self):
        return self.name


class SchedulePeriod(Model):
    class Meta:
        ordering = ("start",)

    schedule = ForeignKey(Schedule, on_delete=CASCADE, related_name="periods")
    period = ForeignKey(Period, on_delete=CASCADE, related_name="+")

    start = TimeField()
    end = TimeField()


def validate_guess(value):
    if value not in wordle.VALID_GUESSES:
        raise ValidationError("Invalid guess")

class WordleTheme(Model):
    date = DateField()
    word = CharField(max_length=5)

def wordle_key():
    try:
        theme = WordleTheme.objects.get(date=date.today())
        return theme.word
    except WordleTheme.DoesNotExist:
        return wordle.random_answer()

class WordleEntry(Model):
    class Meta:
        verbose_name_plural = "Wordle entries"
        constraints = [UniqueConstraint(name="%(app_label)s_%(class)s_user_date", fields=("user", "date"))]

    user = ForeignKey(User, on_delete=CASCADE, related_name="wordle_entries")
    date = DateField()
    word = CharField(max_length=5, default=wordle_key)
    guesses = ArrayField(CharField(max_length=5, validators=[validate_guess]), blank=True, default=list)
    solved = BooleanField(default=False)


@receiver(pre_save, sender=Post)
def before_send_post_notifications(*, instance, **kwargs):
    try:
        instance._pre_save_instance = Post.objects.get(pk=instance.pk)
    except Post.DoesNotExist:
        instance._pre_save_instance = None


@receiver(post_save, sender=Post)
def send_post_notifications(*, instance, created, **kwargs):
    if instance._pre_save_instance and instance._pre_save_instance.published:
        return
    if not instance.published:
        return

    tokens = instance.organization.memberships.filter(active=True).values("user__expo_push_tokens__token")
    tokens = [token for x in tokens if (token := x["user__expo_push_tokens__token"])]

    send_notifications(tokens, instance.title, instance.content[:300])


@receiver(pre_save, sender=Event)
def add_code(*, instance, **kwargs):
    if instance.submission_type == EventSubmissionType.CODE and instance.code is None:
        instance.code = random_code()


@receiver(post_save, sender=USER_MODEL)
def add_required_orgs(*, instance, **kwargs):
    q = Q(required=True) | Q(required_grad_year__isnull=False, required_grad_year=instance.grad_year)
    orgs = Organization.objects.filter(q)
    instance.organizations.add(*orgs)

    remove_orgs = Organization.objects.exclude(required_grad_year__isnull=True)
    remove_orgs = remove_orgs.exclude(required_grad_year=instance.grad_year)
    instance.organizations.remove(*remove_orgs)


@receiver(post_save, sender=Organization)
def add_required_users(*, instance, **kwargs):
    if instance.required:
        users = get_user_model().objects.all()
    elif instance.required_grad_year is not None:
        users = get_user_model().objects.filter(grad_year=instance.required_grad_year)
    else:
        return

    instance.users.add(*users)


@receiver(pre_save, sender=Event)
def before_add_all_points_(*, instance, **kwargs):
    try:
        instance._pre_save_instance = Event.objects.get(pk=instance.pk)
    except Event.DoesNotExist:
        instance._pre_save_instance = None


@receiver(post_save, sender=Event)
def add_all_points(*, instance, created, **kwargs):
    if instance._pre_save_instance:
        diff = instance.points - instance._pre_save_instance.points
        Membership.objects.filter(organization=instance.organization, user__in=instance.users.all()).update(
            points=F("points") + diff
        )


@receiver(post_delete, sender=Event)
def delete_all_points(*, instance, **kwargs):
    Membership.objects.filter(organization=instance.organization, user__in=instance.users.all()).update(
        points=F("points") - instance.points
    )


@receiver(pre_save, sender=Submission)
def before_add_points(*, instance, **kwargs):
    try:
        instance._pre_save_instance = Submission.objects.get(pk=instance.pk)
    except Submission.DoesNotExist:
        instance._pre_save_instance = None


@receiver(post_save, sender=Submission)
def add_points(*, instance, created, **kwargs):
    membership, _ = Membership.objects.get_or_create(user=instance.user, organization=instance.event.organization)
    membership.active = True
    if instance._pre_save_instance:
        membership.points -= instance._pre_save_instance.get_points()
    membership.points += instance.get_points()
    membership.save()


@receiver(post_delete, sender=Submission)
def remove_points(*, instance, **kwargs):
    membership, _ = Membership.objects.get_or_create(user=instance.user, organization=instance.event.organization)
    membership.points -= instance.get_points()
    membership.save()
