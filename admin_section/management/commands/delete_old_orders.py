from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from admin_section.models import Order


class Command(BaseCommand):
    help = "Delete all orders older than 4 weeks (keeps the last 4 weeks)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview how many orders would be deleted without actually deleting them.",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            default=4,
            help="Number of weeks to keep (default: 4).",
        )

    def handle(self, *args, **options):
        weeks = options["weeks"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(weeks=weeks)

        old_orders = Order.objects.filter(order_date__lt=cutoff)
        count = old_orders.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"No orders found older than {weeks} weeks. Nothing to delete."
            ))
            return

        self.stdout.write(
            f"Cutoff date : {cutoff.strftime('%Y-%m-%d %H:%M')} "
            f"({weeks} weeks ago)"
        )
        self.stdout.write(
            f"Orders to delete: {count}"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Dry run — no orders were deleted."
            ))
            return

        # Confirm before deleting
        confirm = input(
            f"\nAre you sure you want to permanently delete {count} order(s)? "
            "This cannot be undone. [yes/no]: "
        )
        if confirm.strip().lower() != "yes":
            self.stdout.write(self.style.WARNING("Aborted. No orders were deleted."))
            return

        deleted, _ = old_orders.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Successfully deleted {deleted} order(s) older than {weeks} weeks."
        ))
