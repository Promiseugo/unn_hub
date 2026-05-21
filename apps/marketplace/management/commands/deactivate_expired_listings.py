from django.core.management.base import BaseCommand

from apps.marketplace.utils import deactivate_expired_listings


class Command(BaseCommand):
    help = "Deactivate marketplace listings after their 30-day expiry window."

    def handle(self, *args, **options):
        count = deactivate_expired_listings()
        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} expired listing(s)."))
