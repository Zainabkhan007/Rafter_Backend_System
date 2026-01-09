from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, time
from admin_section.models import Order


class Command(BaseCommand):
    help = "Auto-complete all past orders - marks orders as collected after 9pm"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Get current time
        now = timezone.now()
        today = timezone.localdate()

        # Log the execution time
        self.stdout.write(f"Running at: {now}")
        self.stdout.write(f"Today's date: {today}")

        # Filter orders that should be marked as collected:
        # - order_date is today or earlier (order_date__date__lte=today)
        # - not yet delivered (is_delivered=False)
        # - status is not already 'collected' or 'cancelled'
        orders_to_update = Order.objects.filter(
            order_date__date__lte=today,
            is_delivered=False
        ).exclude(status__in=['collected', 'cancelled'])

        count = orders_to_update.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[DRY RUN] Would update {count} orders to 'collected' status"
            ))
            if count > 0:
                self.stdout.write("Orders that would be updated:")
                for order in orders_to_update[:10]:  # Show first 10
                    self.stdout.write(
                        f"  - Order #{order.id}: {order.user_name} - {order.order_date}"
                    )
                if count > 10:
                    self.stdout.write(f"  ... and {count - 10} more")
        else:
            updated_count = orders_to_update.update(
                is_delivered=True,
                status="collected"
            )
            self.stdout.write(self.style.SUCCESS(
                f"[CRON] {updated_count} past orders (up to {today}) marked as collected"
            ))
