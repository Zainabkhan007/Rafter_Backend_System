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
    ParentRegisteration, Menu
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

        # Get previous week for comparison
        prev_week_start, prev_week_end = self.get_week_dates(self.week_number - 1, self.year)
        prev_orders = Order.objects.filter(
            **{f'{self.school_type}_school': self.school},
            order_date__date__gte=prev_week_start,
            order_date__date__lte=prev_week_end
        )

        # Calculate metrics
        total_orders = orders.count()
        total_revenue = self.safe_float(orders.aggregate(Sum('total_price'))['total_price__sum'])
        avg_order_value = self.safe_float(orders.aggregate(Avg('total_price'))['total_price__avg'])

        prev_total_orders = prev_orders.count()
        prev_total_revenue = self.safe_float(prev_orders.aggregate(Sum('total_price'))['total_price__sum'])

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
        else:
            # Secondary school logic (if needed)
            total_students = 0
            total_parents = 0
            total_staff = 0

        # Active users (ordered this week)
        active_students = orders.filter(user_type='student').values('user_id').distinct().count()
        active_parents = orders.filter(user_type='parent').values('user_id').distinct().count()
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

        # Get all users who ordered this week
        ordered_student_ids = set(orders.filter(user_type='student').values_list('user_id', flat=True))
        ordered_parent_ids = set(orders.filter(user_type='parent').values_list('user_id', flat=True))
        ordered_staff_ids = set(orders.filter(user_type='staff').values_list('user_id', flat=True))

        # Get all users
        if self.school_type == 'primary':
            all_students = PrimaryStudentsRegister.objects.filter(school=self.school)
            all_parents = ParentRegisteration.objects.filter(
                id__in=all_students.values_list('parent_id', flat=True)
            )
            all_staff = StaffRegisteration.objects.filter(primary_school=self.school)
        else:
            all_students = []
            all_parents = []
            all_staff = []

        # Find inactive users
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
                    'email': student.email,
                    'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                    'last_order_id': last_order.id if last_order else 'N/A',
                })

        inactive_parents = []
        for parent in all_parents:
            if parent.id not in ordered_parent_ids:
                last_order = Order.objects.filter(
                    user_type='parent',
                    user_id=parent.id,
                    **{f'{self.school_type}_school': self.school}
                ).order_by('-order_date').first()

                inactive_parents.append({
                    'id': parent.id,
                    'name': f"{parent.first_name} {parent.last_name}",
                    'email': parent.email,
                    'last_order_date': last_order.order_date.strftime('%d %b %Y') if last_order else 'Never',
                    'last_order_id': last_order.id if last_order else 'N/A',
                })

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
            'parents': inactive_parents,
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
        """Get menu performance statistics"""
        menu_stats = self.data['order_items'].values('_menu_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('_menu_price')),
            order_count=Count('order', distinct=True)
        ).order_by('-total_quantity')[:10]

        result = []
        for stat in menu_stats:
            result.append({
                'name': stat['_menu_name'],
                'quantity': self.safe_int(stat['total_quantity']),
                'revenue': self.safe_float(stat['total_revenue']),
                'orders': self.safe_int(stat['order_count']),
            })

        return result

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
        """Get platform usage analytics (if available)"""
        # This would typically come from a platform field in the Order model
        # For now, return mock data or None if not available
        return None

    def get_recommendations(self):
        """Generate recommendations based on data analysis"""
        recommendations = []

        # Check engagement rates
        if self.data['student_engagement'] < 50:
            recommendations.append({
                'priority': 'high',
                'category': 'Engagement',
                'message': f"Student engagement is at {self.data['student_engagement']}%. Consider promotional campaigns or surveys to understand barriers."
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
        recommendations = self.get_recommendations()

        # Generate charts
        charts = self.generate_charts(day_wise_stats, menu_performance)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>School Analytics Report - {self.school.school_name}</title>
            {self.get_styles()}
        </head>
        <body>
            {self.generate_cover_page()}
            {self.generate_executive_summary(charts)}
            {self.generate_revenue_analysis(charts)}
            {self.generate_order_analytics(charts)}
            {self.generate_user_engagement(charts)}
            {self.generate_menu_performance_section(menu_performance, charts)}
            {self.generate_day_wise_section(day_wise_stats, charts)}
            {self.generate_staff_breakdown_section(staff_breakdown)}
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
                line-height: 1.4;
                font-size: 9pt;
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
                margin-bottom: 40px;
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
                margin-bottom: 40px;
                text-align: center;
            }}

            .cover-info {{
                font-size: 12pt;
                color: {self.COLORS['dark_gray']};
                text-align: center;
                line-height: 1.8;
            }}

            /* Page */
            .page {{
                padding: 15mm;
                page-break-after: always;
            }}

            .page:last-child {{
                page-break-after: auto;
            }}

            /* Headers */
            h1 {{
                font-size: 18pt;
                color: {self.COLORS['dark_forest']};
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 3px solid {self.COLORS['sage_green']};
            }}

            h2 {{
                font-size: 14pt;
                color: {self.COLORS['dark_forest']};
                margin-top: 15px;
                margin-bottom: 10px;
            }}

            h3 {{
                font-size: 11pt;
                color: {self.COLORS['sage_green']};
                margin-top: 12px;
                margin-bottom: 8px;
            }}

            /* KPI Cards */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 15px 0;
            }}

            .kpi-card {{
                background: {self.COLORS['light_gray']};
                padding: 12px;
                border-radius: 6px;
                border-left: 4px solid {self.COLORS['sage_green']};
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
                font-size: 8pt;
                color: {self.COLORS['dark_gray']};
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .kpi-value {{
                font-size: 20pt;
                font-weight: bold;
                color: {self.COLORS['dark_forest']};
                margin-bottom: 4px;
            }}

            .kpi-change {{
                font-size: 8pt;
                font-weight: bold;
            }}

            .kpi-change.positive {{
                color: {self.COLORS['sage_green']};
            }}

            .kpi-change.negative {{
                color: {self.COLORS['rose_pink']};
            }}

            /* Tables */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
                font-size: 8pt;
            }}

            th {{
                background: {self.COLORS['dark_forest']};
                color: {self.COLORS['white']};
                padding: 6px 8px;
                text-align: left;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 7pt;
                letter-spacing: 0.5px;
            }}

            td {{
                padding: 5px 8px;
                border-bottom: 1px solid {self.COLORS['off_white']};
            }}

            tr:nth-child(even) {{
                background: {self.COLORS['light_gray']};
            }}

            /* Charts */
            .chart-container {{
                margin: 15px 0;
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
                gap: 15px;
                margin: 15px 0;
            }}

            /* Badges */
            .badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 7pt;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 0.5px;
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

            /* Info Box */
            .info-box {{
                background: {self.COLORS['soft_aqua']};
                padding: 12px;
                border-radius: 6px;
                margin: 10px 0;
                border-left: 4px solid {self.COLORS['dark_forest']};
            }}

            .info-box p {{
                margin: 4px 0;
                font-size: 8pt;
            }}
        </style>
        """

    def generate_cover_page(self):
        """Generate clean cover page with logo only"""
        week_dates = self.format_week_dates()

        return f"""
        <div class="cover-page">
            <div class="cover-logo">
                <!-- Logo would go here if available -->
                <div style="width: 150px; height: 150px; background: {self.COLORS['sage_green']};
                     border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 48pt; color: white; font-weight: bold;">R</span>
                </div>
            </div>

            <h1 class="cover-title">School Analytics Report</h1>
            <p class="cover-subtitle">{self.school.school_name}</p>

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

        order_change_class = 'positive' if data['order_change'] >= 0 else 'negative'
        revenue_change_class = 'positive' if data['revenue_change'] >= 0 else 'negative'
        order_arrow = '↑' if data['order_change'] >= 0 else '↓'
        revenue_arrow = '↑' if data['revenue_change'] >= 0 else '↓'

        return f"""
        <div class="page">
            <h1>Executive Summary</h1>

            <div class="kpi-grid">
                <div class="kpi-card revenue">
                    <div class="kpi-label">Total Revenue</div>
                    <div class="kpi-value">€{data['total_revenue']:,.2f}</div>
                    <div class="kpi-change {revenue_change_class}">
                        {revenue_arrow} {abs(data['revenue_change']):.1f}% vs last week
                    </div>
                </div>

                <div class="kpi-card orders">
                    <div class="kpi-label">Total Orders</div>
                    <div class="kpi-value">{data['total_orders']:,}</div>
                    <div class="kpi-change {order_change_class}">
                        {order_arrow} {abs(data['order_change']):.1f}% vs last week
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-label">Avg Order Value</div>
                    <div class="kpi-value">€{data['avg_order_value']:,.2f}</div>
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card engagement">
                    <div class="kpi-label">Student Engagement</div>
                    <div class="kpi-value">{data['student_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_students']} of {data['total_students']} students
                    </div>
                </div>

                <div class="kpi-card engagement">
                    <div class="kpi-label">Parent Engagement</div>
                    <div class="kpi-value">{data['parent_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_parents']} of {data['total_parents']} parents
                    </div>
                </div>

                <div class="kpi-card engagement">
                    <div class="kpi-label">Staff Engagement</div>
                    <div class="kpi-value">{data['staff_engagement']}%</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 4px;">
                        {data['active_staff']} of {data['total_staff']} staff
                    </div>
                </div>
            </div>

            <div class="info-box">
                <p><strong>Key Highlights:</strong></p>
                <p>• Week Period: {self.format_week_dates()}</p>
                <p>• Total Users: {data['total_students'] + data['total_parents'] + data['total_staff']:,}</p>
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
                    <td>Students</td>
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
        """Generate order analytics section"""
        return f"""
        <div class="page">
            <h1>Order Analytics</h1>
            <p>Comprehensive analysis of order patterns and trends.</p>

            <div class="info-box">
                <p><strong>Total Orders:</strong> {self.data['total_orders']:,}</p>
                <p><strong>Change vs Last Week:</strong>
                    <span class="{'positive' if self.data['order_change'] >= 0 else 'negative'}">
                        {'↑' if self.data['order_change'] >= 0 else '↓'} {abs(self.data['order_change']):.1f}%
                    </span>
                </p>
            </div>
        </div>
        """

    def generate_user_engagement(self, charts):
        """Generate user engagement section"""
        return f"""
        <div class="page">
            <h1>User Engagement</h1>
            <p>Analysis of user participation and engagement rates.</p>

            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Students</div>
                    <div class="kpi-value">{self.data['student_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px;">
                        {self.data['active_students']} / {self.data['total_students']} active
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Parents</div>
                    <div class="kpi-value">{self.data['parent_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px;">
                        {self.data['active_parents']} / {self.data['total_parents']} active
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Staff</div>
                    <div class="kpi-value">{self.data['staff_engagement']}%</div>
                    <div style="font-size: 7pt; margin-top: 4px;">
                        {self.data['active_staff']} / {self.data['total_staff']} active
                    </div>
                </div>
            </div>
        </div>
        """

    def generate_menu_performance_section(self, menu_performance, charts):
        """Generate menu performance section"""
        html = f"""
        <div class="page">
            <h1>Menu Performance</h1>
            <p>Top performing menu items during this period.</p>
        """

        # Add top menu items chart if available
        if charts.get('top_menu_items'):
            html += f"""
            <div class="chart-container">
                <img src="{charts['top_menu_items']}" alt="Top Menu Items" />
            </div>
            """

        html += """
            <h3>Top 10 Menu Items - Detailed Stats</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Menu Item</th>
                        <th>Quantity Sold</th>
                        <th>Revenue</th>
                        <th>Orders</th>
                    </tr>
                </thead>
                <tbody>
        """

        for idx, item in enumerate(menu_performance, 1):
            html += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{item['name']}</td>
                        <td>{item['quantity']}</td>
                        <td>€{item['revenue']:,.2f}</td>
                        <td>{item['orders']}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
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

    def generate_trend_analysis_section(self):
        """Generate trend analysis section"""
        data = self.data

        # Calculate trend indicators
        order_trend = 'increasing' if data['order_change'] > 5 else 'decreasing' if data['order_change'] < -5 else 'stable'
        revenue_trend = 'increasing' if data['revenue_change'] > 5 else 'decreasing' if data['revenue_change'] < -5 else 'stable'

        # Trend indicators with colors
        order_badge_class = 'success' if data['order_change'] > 0 else 'danger' if data['order_change'] < 0 else 'warning'
        revenue_badge_class = 'success' if data['revenue_change'] > 0 else 'danger' if data['revenue_change'] < 0 else 'warning'

        return f"""
        <div class="page">
            <h1>Trend Analysis</h1>
            <p>Week-over-week comparison and trend indicators.</p>

            <h2>Key Metrics vs Last Week</h2>

            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Orders Trend</div>
                    <div class="kpi-value">{data['total_orders']:,}</div>
                    <div class="kpi-change {'positive' if data['order_change'] >= 0 else 'negative'}">
                        {'↑' if data['order_change'] >= 0 else '↓'} {abs(data['order_change']):.1f}%
                    </div>
                    <span class="badge {order_badge_class}">{order_trend.upper()}</span>
                </div>

                <div class="kpi-card">
                    <div class="kpi-label">Revenue Trend</div>
                    <div class="kpi-value">€{data['total_revenue']:,.2f}</div>
                    <div class="kpi-change {'positive' if data['revenue_change'] >= 0 else 'negative'}">
                        {'↑' if data['revenue_change'] >= 0 else '↓'} {abs(data['revenue_change']):.1f}%
                    </div>
                    <span class="badge {revenue_badge_class}">{revenue_trend.upper()}</span>
                </div>

                <div class="kpi-card">
                    <div class="kpi-label">Avg Order Value</div>
                    <div class="kpi-value">€{data['avg_order_value']:,.2f}</div>
                    <div style="font-size: 7pt; color: {self.COLORS['dark_gray']}; margin-top: 8px;">
                        Current week average
                    </div>
                </div>
            </div>

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
                        <td>Students</td>
                        <td>{data['total_students']}</td>
                        <td>{data['active_students']}</td>
                        <td>{data['student_engagement']}%</td>
                        <td><span class="badge {'success' if data['student_engagement'] >= 70 else 'warning' if data['student_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['student_engagement'] >= 70 else 'GOOD' if data['student_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
                    <tr>
                        <td>Parents</td>
                        <td>{data['total_parents']}</td>
                        <td>{data['active_parents']}</td>
                        <td>{data['parent_engagement']}%</td>
                        <td><span class="badge {'success' if data['parent_engagement'] >= 70 else 'warning' if data['parent_engagement'] >= 50 else 'danger'}">
                            {'EXCELLENT' if data['parent_engagement'] >= 70 else 'GOOD' if data['parent_engagement'] >= 50 else 'NEEDS ATTENTION'}
                        </span></td>
                    </tr>
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
        html = f"""
        <div class="page">
            <h1>Inactive Users</h1>
            <p>Users who did not place orders during {self.format_week_dates()}.</p>
        """

        # Inactive Students
        if inactive_users['students']:
            html += f"""
            <h2>Inactive Students ({len(inactive_users['students'])})</h2>
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

            for student in inactive_users['students'][:50]:  # Limit to 50 for space
                html += f"""
                    <tr>
                        <td>{student['id']}</td>
                        <td>{student['name']}</td>
                        <td>{student['email']}</td>
                        <td>{student['last_order_date']}</td>
                        <td>{student['last_order_id']}</td>
                    </tr>
                """

            if len(inactive_users['students']) > 50:
                html += f"""
                    <tr>
                        <td colspan="5" style="text-align: center; font-style: italic;">
                            ... and {len(inactive_users['students']) - 50} more
                        </td>
                    </tr>
                """

            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>✓ All students placed orders this week!</p>"

        html += "</div>"

        # Inactive Parents (new page)
        html += f"""
        <div class="page">
            <h1>Inactive Users (continued)</h1>
        """

        if inactive_users['parents']:
            html += f"""
            <h2>Inactive Parents ({len(inactive_users['parents'])})</h2>
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

            for parent in inactive_users['parents'][:50]:
                html += f"""
                    <tr>
                        <td>{parent['id']}</td>
                        <td>{parent['name']}</td>
                        <td>{parent['email']}</td>
                        <td>{parent['last_order_date']}</td>
                        <td>{parent['last_order_id']}</td>
                    </tr>
                """

            if len(inactive_users['parents']) > 50:
                html += f"""
                    <tr>
                        <td colspan="5" style="text-align: center; font-style: italic;">
                            ... and {len(inactive_users['parents']) - 50} more
                        </td>
                    </tr>
                """

            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>✓ All parents placed orders this week!</p>"

        # Inactive Staff
        if inactive_users['staff']:
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
        """Generate compact bar chart with data labels for professional PDF"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        if not data:
            return None

        fig, ax = plt.subplots(figsize=(7, 3.5))  # Smaller, more compact

        labels = [item['label'] for item in data]
        values = [item['value'] for item in data]

        bar_color = color or self.COLORS['sage_green']
        bars = ax.bar(labels, values, color=bar_color, width=0.6)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax.set_title(title, fontsize=10, fontweight='bold', pad=10,
                    color=self.COLORS['dark_forest'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=7)
        plt.xticks(rotation=0)
        plt.tight_layout()

        # Convert to base64
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def generate_compact_pie_chart(self, data, title):
        """Generate compact pie chart for professional PDF"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        if not data or sum(item['value'] for item in data) == 0:
            return None

        fig, ax = plt.subplots(figsize=(5, 3.5))  # Compact size

        labels = [item['label'] for item in data]
        values = [item['value'] for item in data]
        colors = [self.COLORS['sage_green'], self.COLORS['mustard_yellow'],
                 self.COLORS['soft_aqua'], self.COLORS['rose_pink'],
                 self.COLORS['pale_mint'], self.COLORS['lavender']]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            colors=colors[:len(data)],
            autopct=lambda pct: f'{int(pct)}%' if pct > 5 else '',
            startangle=90,
            textprops={'fontsize': 7, 'fontweight': 'bold', 'color': 'white'}
        )

        ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
                 fontsize=7, frameon=False)
        ax.set_title(title, fontsize=10, fontweight='bold', pad=10,
                    color=self.COLORS['dark_forest'])

        plt.tight_layout()

        # Convert to base64
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def generate_charts(self, day_wise_stats, menu_performance):
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

        student_count = orders.filter(user_type='student').count()
        parent_count = orders.filter(user_type='parent').count()
        staff_count = orders.filter(user_type='staff').count()

        if student_count > 0:
            user_type_data.append({'label': 'Students', 'value': student_count})
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
            top_5 = menu_performance[:5]
            menu_chart_data = [{'label': item['name'][:15], 'value': item['quantity']}
                             for item in top_5]
            charts['top_menu_items'] = self.generate_compact_bar_chart(
                menu_chart_data,
                'Top 5 Menu Items by Quantity',
                self.COLORS['sage_green']
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
