from django.core.management.base import BaseCommand
from django.utils import timezone
from admin_section.models import Order  


class Command(BaseCommand):
    help = "Auto-complete all past orders up to today at 20:00 UTC"

    def handle(self, *args, **options):
        today = timezone.localdate()
        updated_count = (
            Order.objects
            .filter(order_date__date__lte=today, is_delivered=False)
            .update(is_delivered=True, status="collected")
        )
        self.stdout.write(self.style.SUCCESS(
            f"[CRON] {updated_count} past orders (up to {today}) marked as collected"
        ))
