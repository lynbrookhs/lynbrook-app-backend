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
    REQUIRED_FIELDS = ["grad_year"]
    objects = UserManager()

    username = None
    email = EmailField(_("email address"), unique=True)
    grad_year = IntegerField()
    organizations = ManyToManyField("Organization", through="Membership", related_name="users")


class Organization(Model):
    name = CharField(max_length=200)
    type = IntegerField(choices=OrganizationType.choices)
    advisors = ManyToManyField(USER_MODEL, related_name="advisor_organizations", blank=True)
    admins = ManyToManyField(USER_MODEL, related_name="admin_organizations", blank=True)

    required = BooleanField(default=False)
    required_grad_year = IntegerField(null=True, blank=True)

    day = IntegerField(choices=DayOfWeek.choices, null=True, blank=True)
    time = TimeField(null=True, blank=True)
    link = URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Membership(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="memberships")
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="memberships")
    points = PositiveIntegerField(default=0)


class Event(Model):
    organization = ForeignKey(Organization, on_delete=CASCADE, related_name="events")

    name = CharField(max_length=200)
    description = TextField()
    start = DateTimeField()
    end = DateTimeField()

    points = PositiveIntegerField()
    code = PositiveIntegerField()
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
    start = DateField()
    end = DateField()
    weekday = ArrayField(IntegerField(choices=DayOfWeek.choices))
    # periods = ManyToManyField("Period", through="SchedulePeriod", related_name="+")
    priority = IntegerField()


class Period(Model):
    id = CharField(max_length=200, primary_key=True)
    name = CharField(max_length=200)
    customizable = BooleanField()


class SchedulePeriod(Model):
    schedule = ForeignKey(Schedule, on_delete=CASCADE, related_name="periods")
    period = ForeignKey(Period, on_delete=CASCADE, related_name="+")

    start = TimeField()
    end = TimeField()


@receiver(post_save, sender=USER_MODEL)
def add_required_orgs(sender, instance=None, **kwargs):
    orgs = Organization.objects.filter(Q(required=True) | Q(required_grad_year=instance.grad_year))
    remove_orgs = Organization.objects.exclude(required_grad_year__isnull=True)
    remove_orgs = remove_orgs.exclude(required_grad_year=instance.grad_year)
    instance.organizations.add(*orgs)
    instance.organizations.remove(*remove_orgs)


@receiver(post_save, sender=Organization)
def add_required_users(sender, org=None, **kwargs):
    if org.required:
        users = get_user_model().objects.all()
    elif org.required_grad_year is not None:
        users = get_user_model().objects.filter(grad_year=org.required_grad_year)
    else:
        return

    org.users.add(*users)
