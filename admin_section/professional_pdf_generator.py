"""
Professional PDF Report Generator for School Analytics
Redesigned with modern styling, brand colors, and comprehensive analytics
"""

from io import BytesIO
from datetime import datetime, timedelta
import math
from django.utils import timezone
from weasyprint import HTML, CSS
from .utils.chart_generators import ChartGenerator
from .models import (
    Order, OrderItem, PrimaryStudentsRegister, StaffRegisteration,
    ParentRegisteration, Menu, Transaction
)
from django.db.models import Sum, Count, Avg, F, Q


class ProfessionalPDFGenerator:
    """
    Professional PDF report generator with brand colors and modern design
    """

    # Brand Colors
    COLORS = {
        'off_white': '#EDEDED',
        'dark_forest': '#053F34',
        'pale_mint': '#CAFEC7',
        'sage_green': '#009C5B',
        'mustard_yellow': '#FCCB5E',
        'rose_pink': '#F36487',
        'nude_sand': '#EACBB3',
        'lavender': '#DBD4F4',
        'soft_aqua': '#C7E7EC',
        'white': '#FFFFFF',
        'dark_gray': '#333333',
        'light_gray': '#F5F5F5',
    }

    def __init__(self, school, week_number, year, school_type='primary'):
        self.school = school
        self.week_number = week_number
        self.year = year
        self.school_type = school_type
        self.chart_generator = ChartGenerator()

        # Calculate week dates
        self.week_start, self.week_end = self.get_week_dates(week_number, year)

        # Collect all data
        self.data = self.collect_data()

    @staticmethod
    def safe_float(value, default=0.0):
        """Safely convert value to float, handling NaN and invalid values"""
        if value is None:
            return default
        if isinstance(value, str) and value.lower() in ('nan', 'inf', '-inf', ''):
            return default
        try:
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                return default
            return result
        except (ValueError, TypeError, OverflowError):
            return default

    @staticmethod
    def safe_int(value, default=0):
        """Safely convert value to int, handling NaN and invalid values"""
        if value is None:
            return default
        try:
            float_val = ProfessionalPDFGenerator.safe_float(value, default)
            return int(float_val)
        except (ValueError, TypeError, OverflowError):
            return default

    @staticmethod
    def safe_round(value, decimals=2, default=0.0):
        """Safely round a value, handling NaN and invalid values"""
        safe_val = ProfessionalPDFGenerator.safe_float(value, default)
        try:
            return round(safe_val, decimals)
        except (ValueError, TypeError):
            return default

    def get_week_dates(self, week_number, year):
        """
        Get start and end dates for a week number
        Week logic: Friday is the last day of the week
        """
        # Find the first Friday of the year
        jan_1 = datetime(year, 1, 1).date()
        days_to_friday = (4 - jan_1.weekday()) % 7  # 4 = Friday
        if days_to_friday == 0 and jan_1.weekday() != 4:
            days_to_friday = 7
        first_friday = jan_1 + timedelta(days=days_to_friday)

        # Calculate the Friday of the target week
        target_friday = first_friday + timedelta(weeks=week_number - 1)

        # Week starts on Saturday (day after previous Friday)
        week_start = target_friday - timedelta(days=6)
        week_end = target_friday

        return week_start, week_end

    def format_week_dates(self):
        """Format week dates as '13 Jan - 17 Jan'"""
        if self.week_start.year == self.week_end.year:
            if self.week_start.month == self.week_end.month:
                return f"{self.week_start.day} - {self.week_end.day} {self.week_end.strftime('%b %Y')}"
            else:
                return f"{self.week_start.day} {self.week_start.strftime('%b')} - {self.week_end.day} {self.week_end.strftime('%b %Y')}"
        else:
            return f"{self.week_start.strftime('%d %b %Y')} - {self.week_end.strftime('%d %b %Y')}"

    def collect_data(self):
        """Collect all necessary data for the report"""
        # Base filter for orders
        order_filter = {
            f'{self.school_type}_school': self.school,
            'week_number': self.week_number,
            'year': self.year,
        }

        orders = Order.objects.filter(**order_filter)
        order_items = OrderItem.objects.filter(order__in=orders)

        # Get previous week data - handle Week N-2, N-1, N
        prev_week_start, prev_week_end = self.get_week_dates(self.week_number - 1, self.year)
        prev_orders = Order.objects.filter(
            **{f'{self.school_type}_school': self.school},
            order_date__date__gte=prev_week_start,
            order_date__date__lte=prev_week_end
        )

        # Get Week N-2 data
        week_n2_start, week_n2_end = self.get_week_dates(self.week_number - 2, self.year)
        week_n2_orders = Order.objects.filter(
            **{f'{self.school_type}_school': self.school},
            order_date__date__gte=week_n2_start,
            order_date__date__lte=week_n2_end
        )

        # Calculate metrics
        total_orders = orders.count()

        # Revenue calculation: ONLY count Stripe payments from Transaction model
        stripe_transactions = Transaction.objects.filter(
            order__in=orders,
            payment_method='stripe',
            transaction_type='payment'
        )
        total_revenue = self.safe_float(stripe_transactions.aggregate(Sum('amount'))['amount__sum'])
        avg_order_value = self.safe_float(total_revenue / total_orders) if total_orders > 0 else 0

        prev_total_orders = prev_orders.count()
        prev_stripe_transactions = Transaction.objects.filter(
            order__in=prev_orders,
            payment_method='stripe',
            transaction_type='payment'
        )
        prev_total_revenue = self.safe_float(prev_stripe_transactions.aggregate(Sum('amount'))['amount__sum'])

        # Week N-2 data
        week_n2_total_orders = week_n2_orders.count()
        week_n2_stripe_transactions = Transaction.objects.filter(
            order__in=week_n2_orders,
            payment_method='stripe',
            transaction_type='payment'
        )
        week_n2_total_revenue = self.safe_float(week_n2_stripe_transactions.aggregate(Sum('amount'))['amount__sum'])

        # Calculate changes
        order_change = self.calculate_percentage_change(prev_total_orders, total_orders)
        revenue_change = self.calculate_percentage_change(prev_total_revenue, total_revenue)

        # User counts
        if self.school_type == 'primary':
            total_students = PrimaryStudentsRegister.objects.filter(school=self.school).count()
            total_parents = ParentRegisteration.objects.filter(
                id__in=PrimaryStudentsRegister.objects.filter(school=self.school).values_list('parent_id', flat=True)
            ).count()
            total_staff = StaffRegisteration.objects.filter(primary_school=self.school).count()

            # Active students (CHILDREN): Count distinct children who received orders
            # Orders can be placed by parents (with child_id) OR directly by students (primary_student field)
            active_children_ids = set()

            # Children from parent orders (child_id field)
            parent_orders_with_children = orders.filter(
                user_type='parent',
                child_id__isnull=False
            ).values_list('child_id', flat=True)
            active_children_ids.update(parent_orders_with_children)

            # Children from direct student orders (primary_student field)
            direct_student_orders = orders.filter(
                primary_student__isnull=False
            ).values_list('primary_student_id', flat=True)
            active_children_ids.update(direct_student_orders)

            active_students = len(active_children_ids)
            active_parents = orders.filter(user_type='parent').values('user_id').distinct().count()
            active_staff = orders.filter(user_type='staff').values('user_id').distinct().count()
        else:
            # Secondary school logic - students order directly
            from .models import SecondaryStudent
            total_students = SecondaryStudent.objects.filter(school=self.school).count()
            total_parents = 0  # No parents in secondary
            total_staff = StaffRegisteration.objects.filter(secondary_school=self.school).count()

            active_students = orders.filter(user_type='student').values('user_id').distinct().count()
            active_parents = 0  # No parents in secondary
            active_staff = orders.filter(user_type='staff').values('user_id').distinct().count()

        # Engagement rates
        student_engagement = self.safe_round((active_students / total_students * 100) if total_students > 0 else 0)
        parent_engagement = self.safe_round((active_parents / total_parents * 100) if total_parents > 0 else 0)
        staff_engagement = self.safe_round((active_staff / total_staff * 100) if total_staff > 0 else 0)

        return {
            'orders': orders,
            'order_items': order_items,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'order_change': order_change,
            'revenue_change': revenue_change,
            'total_students': total_students,
            'total_parents': total_parents,
            'total_staff': total_staff,
            'active_students': active_students,
            'active_parents': active_parents,
            'active_staff': active_staff,
            'student_engagement': student_engagement,
            'parent_engagement': parent_engagement,
            'staff_engagement': staff_engagement,
            # Week data for trend analysis
            'week_n2_orders': week_n2_total_orders,
            'week_n2_revenue': week_n2_total_revenue,
            'week_n1_orders': prev_total_orders,
            'week_n1_revenue': prev_total_revenue,
        }

    def calculate_percentage_change(self, old_value, new_value):
        """Calculate percentage change between two values"""
        old = self.safe_float(old_value)
        new = self.safe_float(new_value)

        if old == 0:
            return 100.0 if new > 0 else 0.0

        return self.safe_round(((new - old) / old) * 100)

    def get_inactive_users(self):
        """Get lists of inactive users with detailed information"""
        orders = self.data['orders']

        if self.school_type == 'primary':
            # For primary schools: Show inactive CHILDREN with their parent/staff info in ONE table
            all_children = PrimaryStudentsRegister.objects.filter(school=self.school)

            # Get all children who received orders this week
            active_children_ids = set()

            # Children from parent orders (child_id field)
            parent_orders_with_children = orders.filter(
                user_type='parent',
                child_id__isnull=False
            ).values_list('child_id', flat=True)
            active_children_ids.update(parent_orders_with_children)

            # Children from direct student orders (primary_student field)
            direct_student_orders = orders.filter(
                primary_student__isnull=False
            ).values_list('primary_student_id', flat=True)
            active_children_ids.update(direct_student_orders)

            # Find inactive children
            inactive_children = []
            for child in all_children:
                if child.id not in active_children_ids:
                    # Find last order for this child (either via parent or direct)
                    last_order = Order.objects.filter(
                        Q(child_id=child.id) | Q(primary_student_id=child.id),
                        **{f'{self.school_type}_school': self.school}
                    ).order_by('-order_date').first()

                    # Get parent/staff information
                    parent = child.parent
                    parent_name = f"{parent.first_name} {parent.last_name}" if parent else 'N/A'
                    parent_email = parent.email if parent else 'N/A'

                    inactive_children.append({
                        'child_id': child.id,
                        'child_name': f"{child.first_name} {child.last_name}",
                        'parent_name': parent_name,
                        'parent_email': parent_email,
                        'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                        'last_order_id': last_order.id if last_order else 'N/A',
                    })

            # Get inactive staff
            all_staff = StaffRegisteration.objects.filter(primary_school=self.school)
            ordered_staff_ids = set(orders.filter(user_type='staff').values_list('user_id', flat=True))

            inactive_staff = []
            for staff in all_staff:
                if staff.id not in ordered_staff_ids:
                    last_order = Order.objects.filter(
                        user_type='staff',
                        user_id=staff.id,
                        **{f'{self.school_type}_school': self.school}
                    ).order_by('-order_date').first()

                    inactive_staff.append({
                        'id': staff.id,
                        'name': f"{staff.first_name} {staff.last_name}",
                        'email': staff.email,
                        'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                        'last_order_id': last_order.id if last_order else 'N/A',
                    })

            return {
                'children': inactive_children,
                'staff': inactive_staff,
            }

        else:
            # For secondary schools: Only show students and staff (no parents)
            from .models import SecondaryStudent

            all_students = SecondaryStudent.objects.filter(school=self.school)
            ordered_student_ids = set(orders.filter(user_type='student').values_list('user_id', flat=True))

            inactive_students = []
            for student in all_students:
                if student.id not in ordered_student_ids:
                    last_order = Order.objects.filter(
                        user_type='student',
                        user_id=student.id,
                        **{f'{self.school_type}_school': self.school}
                    ).order_by('-order_date').first()

                    inactive_students.append({
                        'id': student.id,
                        'name': f"{student.first_name} {student.last_name}",
                        'email': student.email if hasattr(student, 'email') else 'N/A',
                        'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                        'last_order_id': last_order.id if last_order else 'N/A',
                    })

            # Get inactive staff
            all_staff = StaffRegisteration.objects.filter(secondary_school=self.school)
            ordered_staff_ids = set(orders.filter(user_type='staff').values_list('user_id', flat=True))

            inactive_staff = []
            for staff in all_staff:
                if staff.id not in ordered_staff_ids:
                    last_order = Order.objects.filter(
                        user_type='staff',
                        user_id=staff.id,
                        **{f'{self.school_type}_school': self.school}
                    ).order_by('-order_date').first()

                    inactive_staff.append({
                        'id': staff.id,
                        'name': f"{staff.first_name} {staff.last_name}",
                        'email': staff.email,
                        'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                        'last_order_id': last_order.id if last_order else 'N/A',
                    })

            return {
                'students': inactive_students,
                'staff': inactive_staff,
            }

    def get_day_wise_analysis(self):
        """Get day-wise analysis excluding Saturday and Sunday"""
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        day_stats = self.data['orders'].filter(
            selected_day__in=weekdays
        ).values('selected_day').annotate(
            count=Count('id'),
            revenue=Sum('total_price')
        )

        result = []
        for day in weekdays:
            stat = next((s for s in day_stats if s['selected_day'] == day), None)
            if stat:
                result.append({
                    'day': day,
                    'orders': stat['count'],
                    'revenue': self.safe_float(stat['revenue']),
                })
            else:
                result.append({
                    'day': day,
                    'orders': 0,
                    'revenue': 0.0,
                })

        return result

    def get_menu_performance(self):
        """Get menu performance statistics - returns dict with top and bottom items"""
        # Get all menu items with their stats
        all_menu_stats = self.data['order_items'].values('_menu_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('_menu_price')),
            order_count=Count('order', distinct=True)
        ).order_by('-total_quantity')

        # Top 10
        top_items = []
        for stat in all_menu_stats[:10]:
            top_items.append({
                'name': stat['_menu_name'],
                'quantity': self.safe_int(stat['total_quantity']),
                'revenue': self.safe_float(stat['total_revenue']),
                'orders': self.safe_int(stat['order_count']),
            })

        # Bottom 10 (least ordered)
        bottom_items = []
        # Get items in ascending order for bottom 10
        bottom_stats = self.data['order_items'].values('_menu_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('_menu_price')),
            order_count=Count('order', distinct=True)
        ).order_by('total_quantity')[:10]

        for stat in bottom_stats:
            bottom_items.append({
                'name': stat['_menu_name'],
                'quantity': self.safe_int(stat['total_quantity']),
                'revenue': self.safe_float(stat['total_revenue']),
                'orders': self.safe_int(stat['order_count']),
            })

        return {
            'top': top_items,
            'bottom': bottom_items
        }

    def get_staff_breakdown(self):
        """Get staff/teacher order breakdown"""
        staff_orders = self.data['orders'].filter(user_type='staff')

        if not staff_orders.exists():
            return []

        # Get individual staff stats
        staff_stats = staff_orders.values('user_id', 'user_name').annotate(
            total_orders=Count('id'),
            total_spent=Sum('total_price')
        ).order_by('-total_orders')

        result = []
        for stat in staff_stats:
            result.append({
                'id': stat['user_id'],
                'name': stat['user_name'] or 'Unknown',
                'orders': self.safe_int(stat['total_orders']),
                'spent': self.safe_float(stat['total_spent']),
            })

        return result

    def get_platform_analytics(self):
        """Get platform usage analytics from user models"""
        from admin_section.models import ParentRegisteration, StaffRegisteration, PrimaryStudentsRegister, SecondaryStudent

        platform_stats = {
            'ios': 0,
            'android': 0,
            'web': 0,
            'total': 0,
            'versions': {
                'ios': {},
                'android': {}
            }
        }

        # Get all users based on school type
        if self.school_type == 'primary':
            students = PrimaryStudentsRegister.objects.filter(school=self.school)
            parents = ParentRegisteration.objects.filter(
                id__in=students.values_list('parent_id', flat=True)
            )
            staff = StaffRegisteration.objects.filter(primary_school=self.school)

            all_users = list(students) + list(parents) + list(staff)
        else:
            students = SecondaryStudent.objects.filter(school=self.school)
            staff = StaffRegisteration.objects.filter(secondary_school=self.school)

            all_users = list(students) + list(staff)

        # Count platforms and versions
        for user in all_users:
            platform = getattr(user, 'platform_type', None)
            if platform:
                platform_stats[platform] += 1
                platform_stats['total'] += 1

                # Track versions
                if platform == 'ios':
                    ios_version = getattr(user, 'ios_version', None)
                    if ios_version:
                        platform_stats['versions']['ios'][ios_version] = \
                            platform_stats['versions']['ios'].get(ios_version, 0) + 1
                elif platform == 'android':
                    android_version = getattr(user, 'android_version', None)
                    if android_version:
                        platform_stats['versions']['android'][android_version] = \
                            platform_stats['versions']['android'].get(android_version, 0) + 1

        # Calculate percentages
        if platform_stats['total'] > 0:
            platform_stats['ios_percent'] = self.safe_round((platform_stats['ios'] / platform_stats['total']) * 100, 1)
            platform_stats['android_percent'] = self.safe_round((platform_stats['android'] / platform_stats['total']) * 100, 1)
            platform_stats['web_percent'] = self.safe_round((platform_stats['web'] / platform_stats['total']) * 100, 1)
        else:
            platform_stats['ios_percent'] = 0
            platform_stats['android_percent'] = 0
            platform_stats['web_percent'] = 0

        return platform_stats if platform_stats['total'] > 0 else None

    def get_recommendations(self):
        """Generate recommendations based on data analysis"""
        recommendations = []

        # Use appropriate terminology based on school type
        student_label = "Child" if self.school_type == 'primary' else "Student"
        students_label = "Children" if self.school_type == 'primary' else "Students"

        # Check engagement rates
        if self.data['student_engagement'] < 50:
            recommendations.append({
                'priority': 'high',
                'category': 'Engagement',
                'message': f"{student_label} engagement is at {self.data['student_engagement']}%. Consider promotional campaigns or surveys to understand barriers."
            })

        if self.data['parent_engagement'] < 40:
            recommendations.append({
                'priority': 'high',
                'category': 'Engagement',
                'message': f"Parent engagement is low at {self.data['parent_engagement']}%. Send reminder emails and improve app notifications."
            })

        if self.data['staff_engagement'] < 60:
            recommendations.append({
                'priority': 'medium',
                'category': 'Engagement',
                'message': f"Staff engagement at {self.data['staff_engagement']}% could be improved through staff meetings or targeted communications."
            })

        # Check order trends
        if self.data['order_change'] < -10:
            recommendations.append({
                'priority': 'high',
                'category': 'Orders',
                'message': f"Orders declined by {abs(self.data['order_change']):.1f}% compared to last week. Investigate menu changes or external factors."
            })
        elif self.data['order_change'] > 20:
            recommendations.append({
                'priority': 'low',
                'category': 'Orders',
                'message': f"Orders increased by {self.data['order_change']:.1f}%! Identify and replicate successful factors."
            })

        # Check revenue
        if self.data['revenue_change'] < -10:
            recommendations.append({
                'priority': 'high',
                'category': 'Revenue',
                'message': f"Revenue dropped by {abs(self.data['revenue_change']):.1f}%. Review pricing strategy and menu offerings."
            })

        # Check average order value
        if self.data['avg_order_value'] < 5:
            recommendations.append({
                'priority': 'medium',
                'category': 'Revenue',
                'message': f"Average order value is €{self.data['avg_order_value']:.2f}. Consider combo deals or upselling strategies."
            })

        # Day-wise analysis
        day_wise = self.get_day_wise_analysis()
        if day_wise:
            orders_by_day = [d['orders'] for d in day_wise]
            min_day = min(orders_by_day)
            max_day = max(orders_by_day)
            if max_day > min_day * 2:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Operations',
                    'message': "Order volume varies significantly by day. Adjust staffing and inventory accordingly."
                })

        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'category': 'Performance',
                'message': "All metrics are performing well. Continue monitoring trends and maintain current strategies."
            })

        return recommendations

    def generate_html(self):
        """Generate HTML content for the PDF"""
        inactive_users = self.get_inactive_users()
        day_wise_stats = self.get_day_wise_analysis()
        menu_performance = self.get_menu_performance()
        staff_breakdown = self.get_staff_breakdown()
        platform_analytics = self.get_platform_analytics()
        recommendations = self.get_recommendations()

        # Generate charts
        charts = self.generate_charts(day_wise_stats, menu_performance, platform_analytics)

        # Get school name based on school type
        school_name = self.school.school_name if self.school_type == 'primary' else self.school.secondary_school_name

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>School Analytics Report - {school_name}</title>
            {self.get_styles()}
        </head>
        <body>
            {self.generate_cover_page()}
            {self.generate_executive_summary(charts)}
            {self.generate_revenue_analysis(charts) if self.school_type == 'secondary' else ''}
            {self.generate_order_analytics(charts)}
            {self.generate_user_engagement(charts)}
            {self.generate_menu_performance_section(menu_performance, charts)}
            {self.generate_day_wise_section(day_wise_stats, charts)}
            {self.generate_staff_breakdown_section(staff_breakdown)}
            {self.generate_platform_analytics_section(platform_analytics, charts) if platform_analytics else ''}
            {self.generate_inactive_users_section(inactive_users)}
            {self.generate_trend_analysis_section()}
            {self.generate_recommendations_section(recommendations)}
        </body>
        </html>
        """

        return html

    def get_styles(self):
        """Get CSS styles for the PDF"""
        return f"""
        <style>
            @page {{
                size: A4;
                margin: 0;
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                color: {self.COLORS['dark_gray']};
                line-height: 1.3;
                font-size: 8pt;
            }}

            /* Cover Page */
            .cover-page {{
                height: 297mm;
                background: {self.COLORS['white']};
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                page-break-after: always;
            }}

            .cover-logo {{
                margin-bottom: 30px;
            }}

            .cover-title {{
                font-size: 32pt;
                font-weight: bold;
                color: {self.COLORS['dark_forest']};
                margin-bottom: 10px;
                text-align: center;
            }}

            .cover-subtitle {{
                font-size: 18pt;
                color: {self.COLORS['sage_green']};
                margin-bottom: 30px;
                text-align: center;
            }}

            .cover-info {{
                font-size: 12pt;
                color: {self.COLORS['dark_gray']};
                text-align: center;
                line-height: 1.6;
            }}

            /* Page - Reduced padding */
            .page {{
                padding: 12mm 15mm;
                page-break-after: always;
            }}

            .page:last-child {{
                page-break-after: auto;
            }}

            /* Headers - Reduced margins */
            h1 {{
                font-size: 16pt;
                color: {self.COLORS['dark_forest']};
                margin-bottom: 10px;
                padding-bottom: 6px;
                border-bottom: 3px solid {self.COLORS['sage_green']};
            }}

            h2 {{
                font-size: 12pt;
                color: {self.COLORS['dark_forest']};
                margin-top: 10px;
                margin-bottom: 6px;
            }}

            h3 {{
                font-size: 10pt;
                color: {self.COLORS['sage_green']};
                margin-top: 8px;
                margin-bottom: 5px;
            }}

            /* KPI Cards - Compact */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin: 10px 0;
            }}

            .kpi-card {{
                background: {self.COLORS['light_gray']};
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid {self.COLORS['sage_green']};
            }}

            .kpi-card.revenue {{
                border-left-color: {self.COLORS['mustard_yellow']};
            }}

            .kpi-card.orders {{
                border-left-color: {self.COLORS['soft_aqua']};
            }}

            .kpi-card.engagement {{
                border-left-color: {self.COLORS['rose_pink']};
            }}

            .kpi-label {{
                font-size: 7pt;
                color: {self.COLORS['dark_gray']};
                margin-bottom: 3px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}

            .kpi-value {{
                font-size: 16pt;
                font-weight: bold;
                color: {self.COLORS['dark_forest']};
                margin-bottom: 3px;
            }}

            .kpi-change {{
                font-size: 7pt;
                font-weight: bold;
            }}

            .kpi-change.positive {{
                color: {self.COLORS['sage_green']};
            }}

            .kpi-change.negative {{
                color: {self.COLORS['rose_pink']};
            }}

            /* Tables - More compact */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 6px 0;
                font-size: 7pt;
            }}

            th {{
                background: {self.COLORS['dark_forest']};
                color: {self.COLORS['white']};
                padding: 4px 6px;
                text-align: left;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 6pt;
                letter-spacing: 0.3px;
            }}

            td {{
                padding: 3px 6px;
                border-bottom: 1px solid {self.COLORS['off_white']};
            }}

            tr:nth-child(even) {{
                background: {self.COLORS['light_gray']};
            }}

            /* Charts - Compact */
            .chart-container {{
                margin: 8px 0;
                text-align: center;
            }}

            .chart-container img {{
                max-width: 100%;
                height: auto;
            }}

            /* Two Column Layout */
            .two-column {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin: 10px 0;
            }}

            /* Badges - Compact */
            .badge {{
                display: inline-block;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 6pt;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}

            .badge.success {{
                background: {self.COLORS['pale_mint']};
                color: {self.COLORS['dark_forest']};
            }}

            .badge.warning {{
                background: {self.COLORS['mustard_yellow']};
                color: {self.COLORS['dark_forest']};
            }}

            .badge.danger {{
                background: {self.COLORS['rose_pink']};
                color: {self.COLORS['white']};
            }}

            /* Info Box - Compact */
            .info-box {{
                background: {self.COLORS['soft_aqua']};
                padding: 8px;
                border-radius: 4px;
                margin: 6px 0;
                border-left: 3px solid {self.COLORS['dark_forest']};
            }}

            .info-box p {{
                margin: 2px 0;
                font-size: 7pt;
                line-height: 1.4;
            }}
        </style>
        """

    def get_logo_base64(self):
        """Get Rafters logo as base64 from static files"""
        import os
        import base64
        from django.conf import settings

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'rafters-logo.svg')

        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                return f"data:image/svg+xml;base64,{base64.b64encode(logo_data).decode()}"
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            return None

    def generate_cover_page(self):
        """Generate clean cover page with logo only"""
        week_dates = self.format_week_dates()
        logo_base64 = self.get_logo_base64()
        school_name = self.school.school_name if self.school_type == 'primary' else self.school.secondary_school_name

        logo_html = ''
        if logo_base64:
            logo_html = f'<img src="{logo_base64}" alt="Rafters Logo" style="width: 200px; height: auto;" />'
        else:
            # Fallback if logo not found
            logo_html = f'''
                <div style="width: 150px; height: 150px; background: {self.COLORS['sage_green']};
                     border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 48pt; color: white; font-weight: bold;">R</span>
                </div>
            '''

        return f"""
        <div class="cover-page">
            <div class="cover-logo">
                {logo_html}
            </div>

            <h1 class="cover-title">School Analytics Report</h1>
            <p class="cover-subtitle">{school_name}</p>

            <div class="cover-info">
                <p><strong>Report Period:</strong> {week_dates}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%d %B %Y at %H:%M')}</p>
                <p><strong>School Type:</strong> {self.school_type.title()}</p>
            </div>
        </div>
        """

    def generate_executive_summary(self, charts):
        """Generate executive summary section with KPIs"""
        data = self.data

        # Use appropriate terminology based on school type
        student_label = "Child" if self.school_type == 'primary' else "Student"
        students_label = "Children" if self.school_type == 'primary' else "Students"

        order_change_class = 'positive' if data['order_change'] >= 0 else 'negative'
        order_arrow = '↑' if data['order_change'] >= 0 else '↓'

        # Show revenue only for secondary schools
        revenue_kpi = ""
        if self.school_type == 'secondary':
            revenue_change_class = 'positive' if data['revenue_change'] >= 0 else 'negative'
            revenue_arrow = '↑' if data['revenue_change'] >= 0 else '↓'
            revenue_kpi = f"""
                <div class="kpi-card revenue">
                    <div class="kpi-label">Total Revenue (Stripe)</div>
                    <div class="kpi-value">€{data['total_revenue']:,.2f}</div>
                    <div class="kpi-change {revenue_change_class}">
                        {revenue_arrow} {abs(data['revenue_change']):.1f}% vs last week
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-label">Avg Order Value</div>
                    <div class="kpi-value">€{data['avg_order_value']:,.2f}</div>
                </div>
            """

        # Parent engagement only for primary schools
        parent_kpi = ""
        if self.school_type == 'primary':
            parent_kpi = f"""
                <div class="kpi-card engagement">
                    <div class="kpi-label">Parent Engagement</div>
                    <div class="kpi-value">{data['parent_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_parents']} of {data['total_parents']} parents
                    </div>
                </div>
            """

        # Calculate grid columns based on number of cards
        num_cards = 3  # Base: orders, student engagement, staff engagement
        if self.school_type == 'secondary':
            num_cards += 2  # Add revenue cards
        elif self.school_type == 'primary':
            num_cards += 1  # Add parent engagement

        return f"""
        <div class="page">
            <h1>Executive Summary</h1>

            <div class="kpi-grid" style="grid-template-columns: repeat({min(num_cards, 4)}, 1fr);">
                {revenue_kpi}

                <div class="kpi-card orders">
                    <div class="kpi-label">Total Orders</div>
                    <div class="kpi-value">{data['total_orders']:,}</div>
                    <div class="kpi-change {order_change_class}">
                        {order_arrow} {abs(data['order_change']):.1f}% vs last week
                    </div>
                </div>

                <div class="kpi-card engagement">
                    <div class="kpi-label">{student_label} Engagement</div>
                    <div class="kpi-value">{data['student_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_students']} of {data['total_students']} {students_label.lower()}
                    </div>
                </div>

                {parent_kpi}

                <div class="kpi-card engagement">
                    <div class="kpi-label">Staff Engagement</div>
                    <div class="kpi-value">{data['staff_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_staff']} of {data['total_staff']} staff
                    </div>
                </div>
            </div>

            <h2>Key Highlights</h2>
            <div class="info-box">
                <p>• Week Period: {self.format_week_dates()}</p>
                <p>• Total Users: {data['total_students'] + data['total_parents'] + data['total_staff']:,}</p>
                <p>• Active Users: {data['active_students'] + data['active_parents'] + data['active_staff']:,}</p>
                <p>• Overall Engagement: {self.safe_round((data['active_students'] + data['active_parents'] + data['active_staff']) / (data['total_students'] + data['total_parents'] + data['total_staff']) * 100) if (data['total_students'] + data['total_parents'] + data['total_staff']) > 0 else 0}%</p>
            </div>
        </div>
        """

    def generate_revenue_analysis(self, charts):
        """Generate revenue analysis section"""
        html = f"""
        <div class="page">
            <h1>Revenue Analysis</h1>
            <p>Detailed breakdown of revenue metrics for this reporting period.</p>

            <h2>Revenue Breakdown</h2>
            <div class="info-box">
                <p><strong>Total Revenue:</strong> €{self.data['total_revenue']:,.2f}</p>
                <p><strong>Average Order Value:</strong> €{self.data['avg_order_value']:,.2f}</p>
                <p><strong>Total Orders:</strong> {self.data['total_orders']:,}</p>
            </div>
        """

        # Add user type chart if available
        if charts.get('user_type_orders'):
            html += f"""
            <div class="chart-container">
                <img src="{charts['user_type_orders']}" alt="Orders by User Type" style="max-width: 60%;" />
            </div>
            """

        html += f"""
            <h3>Revenue by User Type</h3>
            {self.generate_revenue_by_user_type_table()}
        </div>
        """

        return html

    def generate_revenue_by_user_type_table(self):
        """Generate revenue breakdown by user type table"""
        orders = self.data['orders']

        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"

        student_stats = orders.filter(user_type='student').aggregate(
            count=Count('id'),
            revenue=Sum('total_price')
        )
        parent_stats = orders.filter(user_type='parent').aggregate(
            count=Count('id'),
            revenue=Sum('total_price')
        )
        staff_stats = orders.filter(user_type='staff').aggregate(
            count=Count('id'),
            revenue=Sum('total_price')
        )

        student_revenue = self.safe_float(student_stats['revenue'])
        parent_revenue = self.safe_float(parent_stats['revenue'])
        staff_revenue = self.safe_float(staff_stats['revenue'])
        total = student_revenue + parent_revenue + staff_revenue

        return f"""
        <table>
            <thead>
                <tr>
                    <th>User Type</th>
                    <th>Orders</th>
                    <th>Revenue</th>
                    <th>% of Total</th>
                    <th>Avg Order</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{students_label}</td>
                    <td>{student_stats['count']}</td>
                    <td>€{student_revenue:,.2f}</td>
                    <td>{self.safe_round(student_revenue / total * 100) if total > 0 else 0}%</td>
                    <td>€{self.safe_round(student_revenue / student_stats['count']) if student_stats['count'] > 0 else 0}</td>
                </tr>
                <tr>
                    <td>Parents</td>
                    <td>{parent_stats['count']}</td>
                    <td>€{parent_revenue:,.2f}</td>
                    <td>{self.safe_round(parent_revenue / total * 100) if total > 0 else 0}%</td>
                    <td>€{self.safe_round(parent_revenue / parent_stats['count']) if parent_stats['count'] > 0 else 0}</td>
                </tr>
                <tr>
                    <td>Staff</td>
                    <td>{staff_stats['count']}</td>
                    <td>€{staff_revenue:,.2f}</td>
                    <td>{self.safe_round(staff_revenue / total * 100) if total > 0 else 0}%</td>
                    <td>€{self.safe_round(staff_revenue / staff_stats['count']) if staff_stats['count'] > 0 else 0}</td>
                </tr>
                <tr style="font-weight: bold; background: {self.COLORS['pale_mint']};">
                    <td>TOTAL</td>
                    <td>{self.data['total_orders']}</td>
                    <td>€{self.data['total_revenue']:,.2f}</td>
                    <td>100%</td>
                    <td>€{self.data['avg_order_value']:,.2f}</td>
                </tr>
            </tbody>
        </table>
        """

    def generate_order_analytics(self, charts):
        """Generate order analytics section - Full page with breakdown"""
        data = self.data
        orders = data['orders']

        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"

        # Get user type breakdown
        student_orders = orders.filter(user_type='student').count()
        parent_orders = orders.filter(user_type='parent').count()
        staff_orders = orders.filter(user_type='staff').count()

        return f"""
        <div class="page">
            <h1>Order Analytics</h1>
            <p>Comprehensive analysis of order patterns and trends.</p>

            <h2>Order Summary</h2>
            <div class="kpi-grid" style="grid-template-columns: repeat(2, 1fr);">
                <div class="kpi-card orders">
                    <div class="kpi-label">Total Orders</div>
                    <div class="kpi-value">{data['total_orders']:,}</div>
                    <div class="kpi-change {'positive' if data['order_change'] >= 0 else 'negative'}">
                        {'↑' if data['order_change'] >= 0 else '↓'} {abs(data['order_change']):.1f}% vs last week
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Week Period</div>
                    <div class="kpi-value" style="font-size: 14pt;">{self.format_week_dates()}</div>
                </div>
            </div>

            <h2>Orders by User Type</h2>
            <table>
                <thead>
                    <tr>
                        <th>User Type</th>
                        <th>Orders</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{students_label}</td>
                        <td>{student_orders:,}</td>
                        <td>{self.safe_round(student_orders / data['total_orders'] * 100) if data['total_orders'] > 0 else 0}%</td>
                    </tr>
                    <tr>
                        <td>Parents</td>
                        <td>{parent_orders:,}</td>
                        <td>{self.safe_round(parent_orders / data['total_orders'] * 100) if data['total_orders'] > 0 else 0}%</td>
                    </tr>
                    <tr>
                        <td>Staff</td>
                        <td>{staff_orders:,}</td>
                        <td>{self.safe_round(staff_orders / data['total_orders'] * 100) if data['total_orders'] > 0 else 0}%</td>
                    </tr>
                    <tr style="font-weight: bold; background: {self.COLORS['pale_mint']};">
                        <td>TOTAL</td>
                        <td>{data['total_orders']:,}</td>
                        <td>100%</td>
                    </tr>
                </tbody>
            </table>

            <div class="info-box">
                <p><strong>Key Insights:</strong></p>
                <p>• Most active user group: {students_label if student_orders >= max(parent_orders, staff_orders) else "Parents" if parent_orders >= staff_orders else "Staff"}</p>
                <p>• Total users who ordered: {data['active_students'] + data['active_parents'] + data['active_staff']:,}</p>
                <p>• Order trend: {"Increasing" if data['order_change'] > 5 else "Decreasing" if data['order_change'] < -5 else "Stable"}</p>
            </div>
        </div>
        """

    def generate_user_engagement(self, charts):
        """Generate user engagement section - Full page with detailed breakdown"""
        data = self.data

        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"
        total_users = data['total_students'] + data['total_parents'] + data['total_staff']
        active_users = data['active_students'] + data['active_parents'] + data['active_staff']
        overall_engagement = self.safe_round((active_users / total_users * 100) if total_users > 0 else 0)

        return f"""
        <div class="page">
            <h1>User Engagement</h1>
            <p>Analysis of user participation and engagement rates.</p>

            <h2>Engagement by User Type</h2>
            <div class="kpi-grid">
                <div class="kpi-card engagement">
                    <div class="kpi-label">{students_label}</div>
                    <div class="kpi-value">{data['student_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px; color: {self.COLORS['dark_gray']};">
                        {data['active_students']} / {data['total_students']} active
                    </div>
                </div>
                <div class="kpi-card engagement">
                    <div class="kpi-label">Parents</div>
                    <div class="kpi-value">{data['parent_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px; color: {self.COLORS['dark_gray']};">
                        {data['active_parents']} / {data['total_parents']} active
                    </div>
                </div>
                <div class="kpi-card engagement">
                    <div class="kpi-label">Staff</div>
                    <div class="kpi-value">{data['staff_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px; color: {self.COLORS['dark_gray']};">
                        {data['active_staff']} / {data['total_staff']} active
                    </div>
                </div>
            </div>

            <h2>Engagement Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>User Type</th>
                        <th>Total Users</th>
                        <th>Active Users</th>
                        <th>Inactive Users</th>
                        <th>Engagement Rate</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{students_label}</td>
                        <td>{data['total_students']:,}</td>
                        <td>{data['active_students']:,}</td>
                        <td>{data['total_students'] - data['active_students']:,}</td>
                        <td>{data['student_engagement']}%</td>
                        <td><span class="badge {'success' if data['student_engagement'] >= 70 else 'warning' if data['student_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['student_engagement'] >= 70 else 'GOOD' if data['student_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                    <tr>
                        <td>Parents</td>
                        <td>{data['total_parents']:,}</td>
                        <td>{data['active_parents']:,}</td>
                        <td>{data['total_parents'] - data['active_parents']:,}</td>
                        <td>{data['parent_engagement']}%</td>
                        <td><span class="badge {'success' if data['parent_engagement'] >= 70 else 'warning' if data['parent_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['parent_engagement'] >= 70 else 'GOOD' if data['parent_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                    <tr>
                        <td>Staff</td>
                        <td>{data['total_staff']:,}</td>
                        <td>{data['active_staff']:,}</td>
                        <td>{data['total_staff'] - data['active_staff']:,}</td>
                        <td>{data['staff_engagement']}%</td>
                        <td><span class="badge {'success' if data['staff_engagement'] >= 70 else 'warning' if data['staff_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['staff_engagement'] >= 70 else 'GOOD' if data['staff_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                    <tr style="font-weight: bold; background: {self.COLORS['pale_mint']};">
                        <td>TOTAL</td>
                        <td>{total_users:,}</td>
                        <td>{active_users:,}</td>
                        <td>{total_users - active_users:,}</td>
                        <td>{overall_engagement}%</td>
                        <td><span class="badge {'success' if overall_engagement >= 70 else 'warning' if overall_engagement >= 50 else 'danger'}">
                            {'EXCELLENT' if overall_engagement >= 70 else 'GOOD' if overall_engagement >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                </tbody>
            </table>

            <div class="info-box">
                <p><strong>Key Insights:</strong></p>
                <p>• Overall school engagement: {overall_engagement}%</p>
                <p>• Highest engagement: {students_label if data['student_engagement'] >= max(data['parent_engagement'], data['staff_engagement']) else "Parents" if data['parent_engagement'] >= data['staff_engagement'] else "Staff"}</p>
                <p>• Total inactive users: {total_users - active_users:,}</p>
            </div>
        </div>
        """

    def generate_menu_performance_section(self, menu_performance, charts):
        """Generate menu performance section with top and least ordered items"""
        # Hide revenue column for primary schools
        show_revenue = self.school_type == 'secondary'

        html = f"""
        <div class="page">
            <h1>Menu Performance</h1>
            <p>Menu item performance analysis during this period.</p>
        """

        # Add top menu items chart if available
        if charts.get('top_menu_items'):
            html += f"""
            <div class="chart-container">
                <img src="{charts['top_menu_items']}" alt="Top Menu Items" />
            </div>
            """

        # Top 10 items
        top_items = menu_performance.get('top', []) if isinstance(menu_performance, dict) else menu_performance
        if top_items:
            html += f"""
            <h3>Top 10 Menu Items - Most Ordered</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Menu Item</th>
                        <th>Quantity Sold</th>
                        {'<th>Revenue</th>' if show_revenue else ''}
                        <th>Orders</th>
                    </tr>
                </thead>
                <tbody>
            """

            for idx, item in enumerate(top_items, 1):
                html += f"""
                        <tr>
                            <td>{idx}</td>
                            <td>{item['name']}</td>
                            <td>{item['quantity']}</td>
                            {'<td>€' + f"{item['revenue']:,.2f}" + '</td>' if show_revenue else ''}
                            <td>{item['orders']}</td>
                        </tr>
                """

            html += """
                    </tbody>
                </table>
            """

        # Least ordered items
        bottom_items = menu_performance.get('bottom', []) if isinstance(menu_performance, dict) else []
        if bottom_items:
            html += f"""
            <h3>Least Ordered Menu Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Menu Item</th>
                        <th>Quantity Sold</th>
                        {'<th>Revenue</th>' if show_revenue else ''}
                        <th>Orders</th>
                    </tr>
                </thead>
                <tbody>
            """

            for idx, item in enumerate(bottom_items, 1):
                html += f"""
                        <tr>
                            <td>{idx}</td>
                            <td>{item['name']}</td>
                            <td>{item['quantity']}</td>
                            {'<td>€' + f"{item['revenue']:,.2f}" + '</td>' if show_revenue else ''}
                            <td>{item['orders']}</td>
                        </tr>
                """

            html += """
                    </tbody>
                </table>
            """

        html += """
        </div>
        """

        return html

    def generate_day_wise_section(self, day_wise_stats, charts):
        """Generate day-wise analysis section (excluding Sat/Sun)"""
        html = f"""
        <div class="page">
            <h1>Day-wise Analysis</h1>
            <p>Order and revenue breakdown by weekday (Monday - Friday).</p>

            <div class="two-column">
        """

        # Add charts if available
        if charts.get('day_wise_orders'):
            html += f"""
                <div class="chart-container">
                    <img src="{charts['day_wise_orders']}" alt="Orders by Day" />
                </div>
            """

        if charts.get('day_wise_revenue'):
            html += f"""
                <div class="chart-container">
                    <img src="{charts['day_wise_revenue']}" alt="Revenue by Day" />
                </div>
            """

        html += """
            </div>

            <h3>Detailed Breakdown</h3>
            <table>
                <thead>
                    <tr>
                        <th>Day</th>
                        <th>Orders</th>
                        <th>Revenue</th>
                        <th>Avg Order</th>
                    </tr>
                </thead>
                <tbody>
        """

        for day_stat in day_wise_stats:
            avg_order = self.safe_round(day_stat['revenue'] / day_stat['orders']) if day_stat['orders'] > 0 else 0
            html += f"""
                    <tr>
                        <td>{day_stat['day']}</td>
                        <td>{day_stat['orders']}</td>
                        <td>€{day_stat['revenue']:,.2f}</td>
                        <td>€{avg_order:,.2f}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

    def generate_staff_breakdown_section(self, staff_breakdown):
        """Generate staff/teacher breakdown section (no most popular meal)"""
        if not staff_breakdown:
            return """
            <div class="page">
                <h1>Staff/Teacher Breakdown</h1>
                <p>No staff orders were placed during this period.</p>
            </div>
            """

        html = f"""
        <div class="page">
            <h1>Staff/Teacher Breakdown</h1>
            <p>Individual staff member ordering statistics for this period.</p>

            <table>
                <thead>
                    <tr>
                        <th>Staff ID</th>
                        <th>Name</th>
                        <th>Total Orders</th>
                        <th>Total Spent</th>
                        <th>Avg per Order</th>
                    </tr>
                </thead>
                <tbody>
        """

        for staff in staff_breakdown:
            avg_per_order = self.safe_round(staff['spent'] / staff['orders']) if staff['orders'] > 0 else 0
            html += f"""
                    <tr>
                        <td>{staff['id']}</td>
                        <td>{staff['name']}</td>
                        <td>{staff['orders']}</td>
                        <td>€{staff['spent']:,.2f}</td>
                        <td>€{avg_per_order:,.2f}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

    def generate_platform_analytics_section(self, platform_analytics, charts):
        """Generate platform analytics section"""
        if not platform_analytics:
            return ""

        html = f"""
        <div class="page">
            <h1>Platform Analytics</h1>
            <p>Distribution of users across iOS, Android, and Web platforms.</p>

            <h2>Platform Distribution</h2>
            <div class="kpi-grid">
                <div class="kpi-card" style="border-left-color: {self.COLORS['soft_aqua']};">
                    <div class="kpi-label">iOS Users</div>
                    <div class="kpi-value">{platform_analytics['ios']:,}</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {platform_analytics['ios_percent']}% of total
                    </div>
                </div>
                <div class="kpi-card" style="border-left-color: {self.COLORS['sage_green']};">
                    <div class="kpi-label">Android Users</div>
                    <div class="kpi-value">{platform_analytics['android']:,}</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {platform_analytics['android_percent']}% of total
                    </div>
                </div>
                <div class="kpi-card" style="border-left-color: {self.COLORS['lavender']};">
                    <div class="kpi-label">Web Users</div>
                    <div class="kpi-value">{platform_analytics['web']:,}</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {platform_analytics['web_percent']}% of total
                    </div>
                </div>
            </div>
        """

        # Add chart if available
        if charts.get('platform_pie'):
            html += f"""
            <div class="chart-container">
                <img src="{charts['platform_pie']}" alt="Platform Distribution" />
            </div>
            """

        # Top iOS versions
        ios_versions = platform_analytics['versions']['ios']
        if ios_versions:
            # Sort by count
            top_ios = sorted(ios_versions.items(), key=lambda x: x[1], reverse=True)[:5]
            html += f"""
            <h3>Top iOS Versions</h3>
            <table>
                <thead>
                    <tr>
                        <th>Version</th>
                        <th>Users</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
            """
            for version, count in top_ios:
                percent = self.safe_round((count / platform_analytics['ios']) * 100, 1) if platform_analytics['ios'] > 0 else 0
                html += f"""
                    <tr>
                        <td>iOS {version}</td>
                        <td>{count}</td>
                        <td>{percent}%</td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """

        # Top Android versions
        android_versions = platform_analytics['versions']['android']
        if android_versions:
            # Sort by count
            top_android = sorted(android_versions.items(), key=lambda x: x[1], reverse=True)[:5]
            html += f"""
            <h3>Top Android Versions</h3>
            <table>
                <thead>
                    <tr>
                        <th>Version</th>
                        <th>Users</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
            """
            for version, count in top_android:
                percent = self.safe_round((count / platform_analytics['android']) * 100, 1) if platform_analytics['android'] > 0 else 0
                html += f"""
                    <tr>
                        <td>Android {version}</td>
                        <td>{count}</td>
                        <td>{percent}%</td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """

        html += """
        </div>
        """

        return html

    def generate_trend_analysis_section(self):
        """Generate trend analysis section with 4-week comparison"""
        data = self.data

        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"

        # Calculate trend indicators
        order_trend = 'increasing' if data['order_change'] > 5 else 'decreasing' if data['order_change'] < -5 else 'stable'
        order_badge_class = 'success' if data['order_change'] > 0 else 'danger' if data['order_change'] < 0 else 'warning'

        # Get Week N+1 (next week) - prediction or planned data
        week_n_plus_1_start, week_n_plus_1_end = self.get_week_dates(self.week_number + 1, self.year)
        week_n_plus_1_orders = Order.objects.filter(
            **{f'{self.school_type}_school': self.school},
            order_date__date__gte=week_n_plus_1_start,
            order_date__date__lte=week_n_plus_1_end
        )
        week_n_plus_1_count = week_n_plus_1_orders.count()
        week_n_plus_1_transactions = Transaction.objects.filter(
            order__in=week_n_plus_1_orders,
            payment_method='stripe',
            transaction_type='payment'
        )
        week_n_plus_1_revenue = self.safe_float(week_n_plus_1_transactions.aggregate(Sum('amount'))['amount__sum'])

        # Only show revenue for secondary schools
        revenue_section = ""
        if self.school_type == 'secondary':
            revenue_trend = 'increasing' if data['revenue_change'] > 5 else 'decreasing' if data['revenue_change'] < -5 else 'stable'
            revenue_badge_class = 'success' if data['revenue_change'] > 0 else 'danger' if data['revenue_change'] < 0 else 'warning'
            revenue_section = f"""
            <h2>Revenue Trend (4 Weeks)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>Orders</th>
                        <th>Revenue (Stripe)</th>
                        <th>Avg Order Value</th>
                        <th>Change</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Week N-2</td>
                        <td>{data['week_n2_orders']:,}</td>
                        <td>€{data['week_n2_revenue']:,.2f}</td>
                        <td>€{self.safe_round(data['week_n2_revenue'] / data['week_n2_orders']) if data['week_n2_orders'] > 0 else 0:,.2f}</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Week N-1</td>
                        <td>{data['week_n1_orders']:,}</td>
                        <td>€{data['week_n1_revenue']:,.2f}</td>
                        <td>€{self.safe_round(data['week_n1_revenue'] / data['week_n1_orders']) if data['week_n1_orders'] > 0 else 0:,.2f}</td>
                        <td><span class="badge {'success' if data['week_n1_revenue'] >= data['week_n2_revenue'] else 'danger'}">
                            {'+' if data['week_n1_revenue'] >= data['week_n2_revenue'] else ''}{self.safe_round(self.calculate_percentage_change(data['week_n2_revenue'], data['week_n1_revenue']))}%
                        </span></td>
                    </tr>
                    <tr style="font-weight: bold; background: {self.COLORS['pale_mint']};">
                        <td>Week N (Current)</td>
                        <td>{data['total_orders']:,}</td>
                        <td>€{data['total_revenue']:,.2f}</td>
                        <td>€{data['avg_order_value']:,.2f}</td>
                        <td><span class="badge {revenue_badge_class}">
                            {'+' if data['revenue_change'] >= 0 else ''}{self.safe_round(data['revenue_change'])}%
                        </span></td>
                    </tr>
                    <tr>
                        <td>Week N+1 (Next)</td>
                        <td>{week_n_plus_1_count:,}</td>
                        <td>€{week_n_plus_1_revenue:,.2f}</td>
                        <td>€{self.safe_round(week_n_plus_1_revenue / week_n_plus_1_count) if week_n_plus_1_count > 0 else 0:,.2f}</td>
                        <td><span class="badge {'success' if week_n_plus_1_revenue >= data['total_revenue'] else 'danger'}">
                            {'+' if week_n_plus_1_revenue >= data['total_revenue'] else ''}{self.safe_round(self.calculate_percentage_change(data['total_revenue'], week_n_plus_1_revenue))}%
                        </span></td>
                    </tr>
                </tbody>
            </table>
            """

        # Parent row only for primary schools
        parent_row = ""
        if self.school_type == 'primary':
            parent_row = f"""
                    <tr>
                        <td>Parents</td>
                        <td>{data['total_parents']}</td>
                        <td>{data['active_parents']}</td>
                        <td>{data['parent_engagement']}%</td>
                        <td><span class="badge {'success' if data['parent_engagement'] >= 70 else 'warning' if data['parent_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['parent_engagement'] >= 70 else 'GOOD' if data['parent_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
            """

        return f"""
        <div class="page">
            <h1>Trend Analysis</h1>
            <p>4-week comparison and trend indicators (Week N-2, N-1, N, N+1).</p>

            <h2>Orders Trend (4 Weeks)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>Orders</th>
                        <th>Change</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Week N-2</td>
                        <td>{data['week_n2_orders']:,}</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Week N-1</td>
                        <td>{data['week_n1_orders']:,}</td>
                        <td>{'+' if data['week_n1_orders'] >= data['week_n2_orders'] else ''}{self.safe_round(self.calculate_percentage_change(data['week_n2_orders'], data['week_n1_orders']))}%</td>
                        <td><span class="badge {'success' if data['week_n1_orders'] >= data['week_n2_orders'] else 'danger'}">
                            {'INCREASING' if data['week_n1_orders'] >= data['week_n2_orders'] else 'DECREASING'}
                        </span></td>
                    </tr>
                    <tr style="font-weight: bold; background: {self.COLORS['pale_mint']};">
                        <td>Week N (Current)</td>
                        <td>{data['total_orders']:,}</td>
                        <td>{'+' if data['order_change'] >= 0 else ''}{abs(data['order_change']):.1f}%</td>
                        <td><span class="badge {order_badge_class}">{order_trend.upper()}</span></td>
                    </tr>
                    <tr>
                        <td>Week N+1 (Next)</td>
                        <td>{week_n_plus_1_count:,}</td>
                        <td>{'+' if week_n_plus_1_count >= data['total_orders'] else ''}{self.safe_round(self.calculate_percentage_change(data['total_orders'], week_n_plus_1_count))}%</td>
                        <td><span class="badge {'success' if week_n_plus_1_count >= data['total_orders'] else 'danger'}">
                            {'INCREASING' if week_n_plus_1_count >= data['total_orders'] else 'DECREASING'}
                        </span></td>
                    </tr>
                </tbody>
            </table>

            {revenue_section}

            <h2>Engagement Trends</h2>
            <table>
                <thead>
                    <tr>
                        <th>User Type</th>
                        <th>Total Users</th>
                        <th>Active Users</th>
                        <th>Engagement Rate</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{students_label}</td>
                        <td>{data['total_students']}</td>
                        <td>{data['active_students']}</td>
                        <td>{data['student_engagement']}%</td>
                        <td><span class="badge {'success' if data['student_engagement'] >= 70 else 'warning' if data['student_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['student_engagement'] >= 70 else 'GOOD' if data['student_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                    {parent_row}
                    <tr>
                        <td>Staff</td>
                        <td>{data['total_staff']}</td>
                        <td>{data['active_staff']}</td>
                        <td>{data['staff_engagement']}%</td>
                        <td><span class="badge {'success' if data['staff_engagement'] >= 70 else 'warning' if data['staff_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['staff_engagement'] >= 70 else 'GOOD' if data['staff_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    def generate_recommendations_section(self, recommendations):
        """Generate recommendations section"""
        html = f"""
        <div class="page">
            <h1>Recommendations & Action Items</h1>
            <p>Data-driven insights and suggested actions based on this week's performance.</p>
        """

        # Group by priority
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        medium_priority = [r for r in recommendations if r['priority'] == 'medium']
        low_priority = [r for r in recommendations if r['priority'] == 'low']

        if high_priority:
            html += """
            <h2>High Priority</h2>
            <div style="margin-bottom: 15px;">
            """
            for rec in high_priority:
                html += f"""
                <div class="info-box" style="background: {self.COLORS['rose_pink']}20; border-left-color: {self.COLORS['rose_pink']};">
                    <p><strong>{rec['category']}:</strong> {rec['message']}</p>
                </div>
                """
            html += "</div>"

        if medium_priority:
            html += """
            <h2>Medium Priority</h2>
            <div style="margin-bottom: 15px;">
            """
            for rec in medium_priority:
                html += f"""
                <div class="info-box" style="background: {self.COLORS['mustard_yellow']}20; border-left-color: {self.COLORS['mustard_yellow']};">
                    <p><strong>{rec['category']}:</strong> {rec['message']}</p>
                </div>
                """
            html += "</div>"

        if low_priority:
            html += """
            <h2>Low Priority / General Notes</h2>
            <div style="margin-bottom: 15px;">
            """
            for rec in low_priority:
                html += f"""
                <div class="info-box" style="background: {self.COLORS['sage_green']}20; border-left-color: {self.COLORS['sage_green']};">
                    <p><strong>{rec['category']}:</strong> {rec['message']}</p>
                </div>
                """
            html += "</div>"

        html += """
        </div>
        """

        return html

    def generate_inactive_users_section(self, inactive_users):
        """Generate inactive users section with detailed information"""
        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"
        students_label_lower = students_label.lower()

        html = f"""
        <div class="page">
            <h1>Inactive Users</h1>
            <p>Users who did not receive/place orders during {self.format_week_dates()}.</p>
        """

        if self.school_type == 'primary':
            # Primary schools: Show inactive CHILDREN with parent info in ONE table
            if inactive_users.get('children'):
                html += f"""
                <h2>Inactive {students_label} ({len(inactive_users['children'])})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Child ID</th>
                            <th>Child Name</th>
                            <th>Parent/Staff Name</th>
                            <th>Parent/Staff Email</th>
                            <th>Last Order Date</th>
                            <th>Last Order ID</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                # Show all inactive children
                for child in inactive_users['children']:
                    html += f"""
                        <tr>
                            <td>{child['child_id']}</td>
                            <td>{child['child_name']}</td>
                            <td>{child['parent_name']}</td>
                            <td>{child['parent_email']}</td>
                            <td>{child['last_order_date']}</td>
                            <td>{child['last_order_id']}</td>
                        </tr>
                    """

                html += """
                    </tbody>
                </table>
                """
            else:
                html += f"<p>✓ All {students_label_lower} received orders this week!</p>"

        else:
            # Secondary schools: Show students only
            if inactive_users.get('students'):
                html += f"""
                <h2>Inactive {students_label} ({len(inactive_users['students'])})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Last Order Date</th>
                            <th>Last Order ID</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                # Show all inactive students
                for student in inactive_users['students']:
                    html += f"""
                        <tr>
                            <td>{student['id']}</td>
                            <td>{student['name']}</td>
                            <td>{student['email']}</td>
                            <td>{student['last_order_date']}</td>
                            <td>{student['last_order_id']}</td>
                        </tr>
                    """

                html += """
                    </tbody>
                </table>
                """
            else:
                html += f"<p>✓ All {students_label_lower} placed orders this week!</p>"

        # Inactive Staff (both primary and secondary)
        if inactive_users.get('staff'):
            html += f"""
            <h2>Inactive Staff ({len(inactive_users['staff'])})</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Last Order Date</th>
                        <th>Last Order ID</th>
                    </tr>
                </thead>
                <tbody>
            """

            for staff in inactive_users['staff']:
                html += f"""
                    <tr>
                        <td>{staff['id']}</td>
                        <td>{staff['name']}</td>
                        <td>{staff['email']}</td>
                        <td>{staff['last_order_date']}</td>
                        <td>{staff['last_order_id']}</td>
                    </tr>
                """

            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>✓ All staff placed orders this week!</p>"

        html += "</div>"

        return html

    def generate_compact_bar_chart(self, data, title, color=None):
        """Generate compact bar chart with data labels for professional PDF - Mint/Green theme"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        if not data:
            return None

        fig, ax = plt.subplots(figsize=(7, 3.5))  # Smaller, more compact

        # Set background to pale mint for modern look
        fig.patch.set_facecolor(self.COLORS['pale_mint'])
        ax.set_facecolor(self.COLORS['pale_mint'])

        labels = [item['label'] for item in data]
        values = [item['value'] for item in data]

        bar_color = color or self.COLORS['sage_green']
        bars = ax.bar(labels, values, color=bar_color, width=0.6, edgecolor=self.COLORS['dark_forest'], linewidth=0.5)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold',
                   color=self.COLORS['dark_forest'])

        ax.set_title(title, fontsize=10, fontweight='bold', pad=10,
                    color=self.COLORS['dark_forest'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(self.COLORS['sage_green'])
        ax.spines['left'].set_color(self.COLORS['sage_green'])
        ax.tick_params(labelsize=7, colors=self.COLORS['dark_forest'])
        plt.xticks(rotation=0)
        plt.tight_layout()

        # Convert to base64
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor=self.COLORS['pale_mint'], edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def generate_compact_pie_chart(self, data, title):
        """Generate compact pie chart for professional PDF - Mint/Green theme"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        if not data or sum(item['value'] for item in data) == 0:
            return None

        fig, ax = plt.subplots(figsize=(5, 3.5))  # Compact size

        # Set background to pale mint
        fig.patch.set_facecolor(self.COLORS['pale_mint'])
        ax.set_facecolor(self.COLORS['pale_mint'])

        labels = [item['label'] for item in data]
        values = [item['value'] for item in data]
        # Use green-mint gradient colors for pie chart
        colors = [self.COLORS['sage_green'], self.COLORS['pale_mint'],
                 self.COLORS['soft_aqua'], self.COLORS['lavender'],
                 self.COLORS['mustard_yellow'], self.COLORS['rose_pink']]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            colors=colors[:len(data)],
            autopct=lambda pct: f'{int(pct)}%' if pct > 5 else '',
            startangle=90,
            textprops={'fontsize': 7, 'fontweight': 'bold', 'color': self.COLORS['dark_forest']},
            wedgeprops={'edgecolor': self.COLORS['dark_forest'], 'linewidth': 0.5}
        )

        ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
                 fontsize=7, frameon=False, facecolor=self.COLORS['pale_mint'],
                 labelcolor=self.COLORS['dark_forest'])
        ax.set_title(title, fontsize=10, fontweight='bold', pad=10,
                    color=self.COLORS['dark_forest'])

        plt.tight_layout()

        # Convert to base64
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor=self.COLORS['pale_mint'], edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def generate_charts(self, day_wise_stats, menu_performance, platform_analytics=None):
        """Generate all charts for the report"""
        charts = {}

        # Day-wise chart (excluding weekends)
        if day_wise_stats:
            day_chart_data = [{'label': d['day'][:3], 'value': d['orders']}
                            for d in day_wise_stats]
            charts['day_wise_orders'] = self.generate_compact_bar_chart(
                day_chart_data,
                'Orders by Weekday',
                self.COLORS['soft_aqua']
            )

            day_revenue_data = [{'label': d['day'][:3], 'value': d['revenue']}
                               for d in day_wise_stats]
            charts['day_wise_revenue'] = self.generate_compact_bar_chart(
                day_revenue_data,
                'Revenue by Weekday (€)',
                self.COLORS['mustard_yellow']
            )

        # User type distribution
        orders = self.data['orders']
        user_type_data = []

        # Use appropriate terminology based on school type
        students_label = "Children" if self.school_type == 'primary' else "Students"

        student_count = orders.filter(user_type='student').count()
        parent_count = orders.filter(user_type='parent').count()
        staff_count = orders.filter(user_type='staff').count()

        if student_count > 0:
            user_type_data.append({'label': students_label, 'value': student_count})
        if parent_count > 0:
            user_type_data.append({'label': 'Parents', 'value': parent_count})
        if staff_count > 0:
            user_type_data.append({'label': 'Staff', 'value': staff_count})

        if user_type_data:
            charts['user_type_orders'] = self.generate_compact_pie_chart(
                user_type_data,
                'Orders by User Type'
            )

        # Top menu items chart
        if menu_performance:
            # Handle both dict and list formats
            top_items = menu_performance.get('top', []) if isinstance(menu_performance, dict) else menu_performance
            if top_items:
                top_5 = top_items[:5]
                menu_chart_data = [{'label': item['name'][:15], 'value': item['quantity']}
                                 for item in top_5]
                charts['top_menu_items'] = self.generate_compact_bar_chart(
                    menu_chart_data,
                    'Top 5 Menu Items by Quantity',
                    self.COLORS['sage_green']
                )

        # Platform analytics chart
        if platform_analytics and platform_analytics['total'] > 0:
            platform_chart_data = []
            if platform_analytics['ios'] > 0:
                platform_chart_data.append({'label': 'iOS', 'value': platform_analytics['ios']})
            if platform_analytics['android'] > 0:
                platform_chart_data.append({'label': 'Android', 'value': platform_analytics['android']})
            if platform_analytics['web'] > 0:
                platform_chart_data.append({'label': 'Web', 'value': platform_analytics['web']})

            if platform_chart_data:
                charts['platform_pie'] = self.generate_compact_pie_chart(
                    platform_chart_data,
                    'Platform Distribution'
                )

        return charts

    def generate(self):
        """Generate the PDF report"""
        try:
            html_content = self.generate_html()
            pdf_buffer = BytesIO()

            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)

            return pdf_buffer

        except Exception as e:
            import traceback
            error_msg = f"Error generating professional PDF: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)
