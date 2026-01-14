"""
Analytics Helper Functions
Utility functions for analytics calculations and data processing
"""

from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, F, Q


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if not old_value or old_value == 0:
        return 100.0 if new_value and new_value > 0 else 0.0
    return round(((new_value - old_value) / old_value) * 100, 2)


def calculate_avg_order_value(school_id, school_type):
    """Calculate average order value for a school"""
    from ..models import Order

    avg = Order.objects.filter(
        **{f'{school_type}_school_id': school_id}
    ).aggregate(avg_price=Avg('total_price'))

    return round(float(avg['avg_price'] or 0), 2)


def get_week_date_range(week_number, year):
    """Get start and end date for a given week number"""
    jan_1 = datetime(year, 1, 1)
    week_start = jan_1 + timedelta(weeks=week_number - 1)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start.date(), week_end.date()


def aggregate_by_week(queryset, start_date, end_date):
    """Aggregate queryset by week"""
    from ..models import Order

    weeks = []
    current = start_date
    week_num = 1

    while current <= end_date:
        week_end = min(current + timedelta(days=6), end_date)

        week_orders = queryset.filter(
            order_date__date__gte=current,
            order_date__date__lte=week_end
        )

        week_data = week_orders.aggregate(
            count=Count('id'),
            revenue=Sum('total_price')
        )

        weeks.append({
            'week_number': week_num,
            'start_date': str(current),
            'end_date': str(week_end),
            'count': week_data['count'] or 0,
            'revenue': float(week_data['revenue'] or 0)
        })

        current = week_end + timedelta(days=1)
        week_num += 1

    return weeks


def aggregate_by_day_of_week(queryset):
    """Aggregate orders by day of week"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    day_stats = queryset.values('selected_day').annotate(
        count=Count('id'),
        revenue=Sum('total_price')
    ).order_by('selected_day')

    result = {day: {'count': 0, 'revenue': 0.0} for day in days}

    for stat in day_stats:
        if stat['selected_day'] in result:
            result[stat['selected_day']] = {
                'count': stat['count'],
                'revenue': float(stat['revenue'] or 0)
            }

    return result


def calculate_completion_rate(orders):
    """Calculate order completion rate"""
    total = orders.count()
    if total == 0:
        return 0.0

    completed = orders.filter(status='collected').count()
    return round((completed / total) * 100, 2)


def calculate_repeat_customers(school_id, school_type, start_date=None, end_date=None):
    """Calculate number of repeat customers"""
    from ..models import Order

    filters = {f'{school_type}_school_id': school_id}

    if start_date and end_date:
        filters['order_date__date__gte'] = start_date
        filters['order_date__date__lte'] = end_date

    if school_type == 'primary':
        user_field = 'user_id'
    else:
        user_field = 'user_id'

    # Count users with more than 1 order
    user_order_counts = Order.objects.filter(**filters).values(user_field).annotate(
        order_count=Count('id')
    ).filter(order_count__gt=1)

    return user_order_counts.count()


def get_category_breakdown(order_items):
    """Get breakdown of orders by category"""
    from ..models import MenuItems

    category_stats = []

    # Group by menu item and get category
    item_stats = order_items.values('_menu_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('_menu_price'))
    )

    # TODO: Join with MenuItems to get category
    # For now, return simple stats
    return list(item_stats)


def get_trend_direction(data_points):
    """Determine trend direction from data points"""
    if len(data_points) < 2:
        return 'stable'

    first_half_avg = sum(data_points[:len(data_points)//2]) / (len(data_points)//2)
    second_half_avg = sum(data_points[len(data_points)//2:]) / (len(data_points) - len(data_points)//2)

    if second_half_avg > first_half_avg * 1.1:
        return 'up'
    elif second_half_avg < first_half_avg * 0.9:
        return 'down'
    else:
        return 'stable'


def format_currency(amount):
    """Format amount as currency"""
    return f"€{amount:,.2f}"


def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.1f}%"
