from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_better_admin_arrayfield.models.fields import ArrayField
from rest_framework.authtoken.models import Token


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class OrganizationType(models.IntegerChoices):
    GLOBAL = 1
    CLASS = 2
    CLUB = 3


class PollType(models.IntegerChoices):
    SELECT = 1
    SHORT_ANSWER = 2


class User(AbstractUser):
    organizations = models.ManyToManyField("Organization", through="Membership")


class Organization(models.Model):
    name = models.CharField(max_length=200)
    type = models.IntegerField(choices=OrganizationType.choices)
    advisors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="advisor_organization_set")
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="admin_organization_set")

    day = models.IntegerField(choices=DayOfWeek.choices, null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    points = models.PositiveIntegerField()


class Event(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    points = models.PositiveIntegerField()
    code = models.PositiveIntegerField()
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.name


class Post(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now=True)
    content = models.TextField()
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Poll(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_type",
                check=(
                    models.Q(
                        type=PollType.SHORT_ANSWER,
                        choices__isnull=True,
                        min_values__isnull=True,
                        max_values__isnull=True,
                    )
                    | models.Q(
                        type=PollType.SELECT,
                        choices__isnull=False,
                        min_values__isnull=False,
                        max_values__isnull=False,
                    )
                ),
            )
        ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    type = models.IntegerField(choices=PollType.choices)
    description = models.TextField()

    choices = ArrayField(models.TextField(), null=True, blank=True)
    min_values = models.IntegerField(validators=[MinValueValidator(1)], default=1, null=True, blank=True)
    max_values = models.IntegerField(validators=[MinValueValidator(1)], default=1, null=True, blank=True)

    def __str__(self):
        return self.description


class Prize(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    description = models.TextField()
    points = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Schedule(models.Model):
    start = models.DateField()
    end = models.DateField()
    weekday = ArrayField(models.IntegerField(choices=DayOfWeek.choices))
    periods = models.ManyToManyField("Period", through="SchedulePeriod")
    priority = models.IntegerField()


class Period(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    customizable = models.BooleanField()


class SchedulePeriod(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)

    start = models.TimeField()
    end = models.TimeField()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
