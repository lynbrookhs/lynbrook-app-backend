"""Release senior memories to their recipients. Deliberately terminal-only:

    python manage.py release_memories 2027            # dry run: shows what would happen
    python manage.py release_memories 2027 --confirm  # releases + notifies recipients
"""
import getpass
import socket

from django.core.management.base import BaseCommand, CommandError

from core.models import ExpoPushToken, Memory, MemoryRelease
from core.notifications import send_notifications


class Command(BaseCommand):
    help = "Release a senior class's memories to everyone tagged in them (irreversible-ish; --confirm required)."

    def add_arguments(self, parser):
        parser.add_argument("grad_year", type=int)
        parser.add_argument("--confirm", action="store_true", help="Actually release (otherwise dry run).")

    def handle(self, *args, **options):
        year = options["grad_year"]
        if MemoryRelease.is_released(year):
            raise CommandError(f"Class of {year} memories were already released.")

        memories = Memory.objects.filter(grad_year=year)
        recipient_ids = set(
            Memory.recipients.through.objects.filter(memory__in=memories).values_list(
                "user_id", flat=True
            )
        )
        tokens = list(
            ExpoPushToken.objects.filter(user_id__in=recipient_ids)
            .values_list("token", flat=True)
            .distinct()
        )

        self.stdout.write(f"Class of {year}: {memories.count()} memories, "
                          f"{len(recipient_ids)} distinct recipients, {len(tokens)} push tokens.")

        if not options["confirm"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --confirm to release."))
            return

        MemoryRelease.objects.create(
            grad_year=year, released_by=f"{getpass.getuser()}@{socket.gethostname()}"
        )
        self.stdout.write(self.style.SUCCESS(f"Released! Class of {year} memories are now visible."))

        if tokens:
            send_notifications(
                tokens,
                "Senior Memories",
                "Photos and notes from the Class of %d are waiting for you in the app!" % year,
            )
            self.stdout.write(f"Notified {len(tokens)} devices.")
