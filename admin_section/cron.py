from .models import Order
from django.utils import timezone

def auto_complete_orders():
    today = timezone.localdate()
    updated_count = (
        Order.objects
        .filter(order_date__date=today, is_delivered=False)
        .update(is_delivered=True, status="collected")
    )
    print(f"[CRON] {updated_count} orders marked as collected")
