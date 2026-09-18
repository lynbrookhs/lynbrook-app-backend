import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    ClubCategory,
    Event,
    Membership,
    Organization,
    OrganizationType,
    Submission,
    User,
    UserType,
)


def make_user(email, **kwargs):
    return User.objects.create_user(email=email, password="pw", type=UserType.STUDENT, **kwargs)


def make_club(name):
    return Organization.objects.create(type=OrganizationType.CLUB, name=name, category=ClubCategory.INTEREST)


def make_event(org, name, points):
    now = timezone.now()
    return Event.objects.create(
        organization=org, name=name, start=now, end=now + timedelta(hours=1), points=points, code=1234
    )


class OrganizationPointsAdminTests(TestCase):
    def setUp(self):
        self.club = make_club("Chess Club")
        self.other_club = make_club("Robotics")

        self.officer = make_user("officer@example.com", first_name="Olivia", last_name="Officer")
        self.club.admins.add(self.officer)
        self.other_officer = make_user("other@example.com")
        self.other_club.admins.add(self.other_officer)
        self.superuser = User.objects.create_superuser(email="root@example.com", password="pw", type=UserType.STAFF)

        self.member = make_user("member@example.com", first_name="Mia", last_name="Member")
        self.membership = Membership.objects.create(user=self.member, organization=self.club, points=5)
        self.event = make_event(self.club, "Meeting 1", points=10)
        self.other_event = make_event(self.other_club, "Robotics meeting", points=3)

        self.points_url = reverse("admin:core_organization_points", args=[self.club.id])
        self.csv_url = reverse("admin:core_organization_points_csv", args=[self.club.id])
        self.update_url = reverse("admin:core_organization_points_update", args=[self.club.id])

    def post_update(self, **body):
        return self.client.post(self.update_url, data=json.dumps(body), content_type="application/json")

    # --- viewing ---

    def test_points_page_requires_login(self):
        for url in (self.points_url, self.csv_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/admin/login/", response.url)

    def test_officer_of_another_club_cannot_view_points(self):
        self.client.force_login(self.other_officer)
        self.assertEqual(self.client.get(self.points_url).status_code, 302)
        self.assertEqual(self.client.get(self.csv_url).status_code, 404)
        self.assertEqual(self.post_update(user=self.member.id, points=99).status_code, 404)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.points, 5)

    def test_officer_can_view_own_club_points_and_edit_flag_is_set(self):
        self.client.force_login(self.officer)
        response = self.client.get(self.points_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_edit"])
        self.assertEqual(response.context["event_ids"], [self.event.id])
        self.assertEqual(response.context["members"][0]["id"], self.member.id)
        self.assertEqual(self.client.get(self.csv_url).status_code, 200)

    def test_superuser_can_view_any_club(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.points_url).status_code, 200)

    # --- editing ---

    def test_officer_can_set_total_points(self):
        self.client.force_login(self.officer)
        response = self.post_update(user=self.member.id, event=None, points=42)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"points": 42})
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.points, 42)

    def test_officer_can_set_event_points_which_creates_submission_and_updates_total(self):
        self.client.force_login(self.officer)
        response = self.post_update(user=self.member.id, event=self.event.id, points=7)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"points": 12, "event_points": 7})
        submission = Submission.objects.get(user=self.member, event=self.event)
        self.assertEqual(submission.points, 7)

        # Editing again replaces the override and re-adjusts the total by the difference.
        response = self.post_update(user=self.member.id, event=self.event.id, points=2)
        self.assertEqual(response.json(), {"points": 7, "event_points": 2})

        # Clearing the cell deletes the submission and removes its points.
        response = self.post_update(user=self.member.id, event=self.event.id, points=None)
        self.assertEqual(response.json(), {"points": 5, "event_points": None})
        self.assertFalse(Submission.objects.filter(user=self.member, event=self.event).exists())

    def test_rejects_bad_input(self):
        self.client.force_login(self.officer)
        cases = [
            dict(user=self.member.id, points=-1),
            dict(user=self.member.id, points=None),
            dict(user=self.member.id, points="abc"),
            dict(user=self.other_officer.id, points=3),  # not a member of this club
            dict(user=self.member.id, event=self.other_event.id, points=3),  # event belongs to another club
        ]
        for body in cases:
            response = self.post_update(**body)
            self.assertEqual(response.status_code, 400, body)
        self.assertEqual(self.client.get(self.update_url).status_code, 405)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.points, 5)
        self.assertFalse(Submission.objects.exists())

    def test_advisor_can_edit_and_plain_member_cannot(self):
        advisor = make_user("advisor@example.com")
        self.club.advisors.add(advisor)
        self.client.force_login(advisor)
        self.assertEqual(self.post_update(user=self.member.id, points=8).status_code, 200)

        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.points_url).status_code, 302)
        self.assertEqual(self.post_update(user=self.member.id, points=1000).status_code, 404)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.points, 8)
