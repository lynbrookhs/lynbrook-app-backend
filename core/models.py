import random
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db.models import *
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.models.fields import ArrayField

USER_MODEL = settings.AUTH_USER_MODEL


def random_code():
    return random.randint(100000, 999999)


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
    REQUIRED_FIELDS = []
    objects = UserManager()

    username = None
    email = EmailField(_("email address"), unique=True)
    grad_year = IntegerField(null=True, blank=True)
    organizations = ManyToManyField("Organization", through="Membership", related_name="users")
    picture_url = URLField(
        default="https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.grad_year} ({self.email})"


class Organization(Model):
    class Meta:
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
    description = TextField(null=True, blank=True)
    category = IntegerField(choices=ClubCategory.choices, null=True, blank=True)

    day = IntegerField(choices=DayOfWeek.choices, null=True, blank=True)
    time = TimeField(null=True, blank=True)
    link = URLField(null=True, blank=True)

    ical_links = ArrayField(URLField(), blank=True, default=list)

    def __str__(self):
        return self.name


class OrganizationLink(Model):
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="links")
    title = CharField(max_length=200)
    url = URLField()


class Membership(Model):
    class Meta:
        constraints = [
            UniqueConstraint(
                name="%(app_label)s_%(class)s_user_organization", fields=("user", "organization")
            )
        ]

    user = ForeignKey(User, on_delete=CASCADE, related_name="memberships")
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="memberships")
    active = BooleanField(default=True)
    points = PositiveIntegerField(default=0)


class Event(Model):
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="events")

    name = CharField(max_length=200)
    description = TextField()
    start = DateTimeField()
    end = DateTimeField()

    points = PositiveIntegerField()
    code = PositiveIntegerField(default=random_code)
    users = ManyToManyField(USER_MODEL, blank=True, related_name="events")

    def __str__(self):
        return self.name


class Post(Model):
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


class Prize(Model):
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="prizes")

    name = CharField(max_length=200)
    description = TextField()
    points = PositiveIntegerField()

    def __str__(self):
        return self.name


class Schedule(Model):
    name = CharField(max_length=200)
    start = DateField()
    end = DateField()
    weekday = ArrayField(IntegerField(choices=DayOfWeek.choices))
    priority = IntegerField()

    @classmethod
    def get_for_day(cls, day: date):
        print(day)
        qs = cls.objects.filter(start__lte=day, end__gte=day, weekday__contains=[day.weekday()])
        try:
            return qs.order_by("-priority")[0]
        except IndexError:
            return cls(name="No Schedule")


class Period(Model):
    id = CharField(max_length=200, primary_key=True)
    name = CharField(max_length=200)
    customizable = BooleanField()

    def __str__(self):
        return self.name


class SchedulePeriod(Model):
    schedule = ForeignKey(Schedule, on_delete=CASCADE, related_name="periods")
    period = ForeignKey(Period, on_delete=CASCADE, related_name="+")

    start = TimeField()
    end = TimeField()


@receiver(post_save, sender=USER_MODEL)
def add_required_orgs(*, sender, instance=None, **kwargs):
    q = Q(required=True) | Q(required_grad_year__isnull=False, required_grad_year=instance.grad_year)
    orgs = Organization.objects.filter(q)
    instance.organizations.add(*orgs)

    remove_orgs = Organization.objects.exclude(required_grad_year__isnull=True)
    remove_orgs = remove_orgs.exclude(required_grad_year=instance.grad_year)
    instance.organizations.remove(*remove_orgs)


@receiver(post_save, sender=Organization)
def add_required_users(*, sender, instance=None, **kwargs):
    if instance.required:
        users = get_user_model().objects.all()
    elif instance.required_grad_year is not None:
        users = get_user_model().objects.filter(grad_year=instance.required_grad_year)
    else:
        return

    instance.users.add(*users)
