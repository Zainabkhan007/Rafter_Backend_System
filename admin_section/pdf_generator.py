"""
School Report PDF Generator
Generates comprehensive PDF reports with 11 detailed sections
"""

import os
import base64
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Sum, Avg, F, Q
from django.template.loader import render_to_string
from .models import (
    Order, OrderItem, PrimaryStudentsRegister, SecondaryStudent,
    ParentRegisteration, StaffRegisteration, Teacher, Menu, Transaction
)
from .utils.chart_generators import ChartGenerator
from .utils.analytics_helpers import (
    calculate_percentage_change, aggregate_by_week,
    aggregate_by_day_of_week, calculate_completion_rate,
    calculate_repeat_customers, format_currency, format_percentage
)


class SchoolReportGenerator:
    """
    Generates comprehensive PDF reports for schools
    Uses WeasyPrint for HTML-to-PDF conversion
    """

    def __init__(self, school, school_type, filters):
        self.school = school
        self.school_type = school_type
        self.filters = filters
        self.chart_generator = ChartGenerator()
        self.data = {}
        self.charts = {}

        # Parse date filters
        self.start_date = None
        self.end_date = None
        if filters.get('start_date'):
            self.start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        if filters.get('end_date'):
            self.end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()

        # Set default date range if not provided (last 30 days)
        if not self.start_date or not self.end_date:
            self.end_date = datetime.now().date()
            self.start_date = self.end_date - timedelta(days=30)

    @staticmethod
    def safe_float(value, default=0.0):
        """Safely convert value to float, handling None and NaN"""
        if value is None:
            return default

        # Check for string 'nan'
        if isinstance(value, str) and value.lower() in ('nan', 'inf', '-inf'):
            return default

        try:
            result = float(value)
            # Check if result is NaN or Inf
            import math
            if math.isnan(result) or math.isinf(result):
                return default
            return result
        except (ValueError, TypeError, OverflowError):
            return default

    @staticmethod
    def safe_int(value, default=0):
        """Safely convert value to int, handling None and NaN"""
        if value is None:
            return default

        # Check for string 'nan'
        if isinstance(value, str) and value.lower() in ('nan', 'inf', '-inf'):
            return default

        try:
            # First convert to float to handle NaN
            import math
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return default
            return int(float_val)
        except (ValueError, TypeError, OverflowError):
            return default

    @staticmethod
    def safe_round(value, decimals=2, default=0.0):
        """Safely round a value, handling None and NaN"""
        if value is None:
            return default

        # Check for string 'nan'
        if isinstance(value, str) and value.lower() in ('nan', 'inf', '-inf'):
            return default

        try:
            import math
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return default
            return round(float_val, decimals)
        except (ValueError, TypeError, OverflowError):
            return default

    def generate(self):
        """Main generation method"""
        try:
            # 1. Collect all data
            self.collect_data()

            # 2. Generate charts
            self.generate_charts()

            # 3. Render HTML template
            html_content = self.render_html()

            # 4. Convert to PDF
            pdf_path = self.create_pdf(html_content)

            return pdf_path
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in generate(): {str(e)}")
            print(f"Traceback: {error_trace}")
            raise Exception(f"PDF generation failed: {str(e)}\n\nTraceback:\n{error_trace}")

    # ========================================================================
    # DATA COLLECTION METHODS
    # ========================================================================

    def get_filtered_orders(self):
        """Get orders filtered by date range and other criteria"""
        filters = {f'{self.school_type}_school_id': self.school.id}

        if self.start_date and self.end_date:
            filters['order_date__date__gte'] = self.start_date
            filters['order_date__date__lte'] = self.end_date

        orders = Order.objects.filter(**filters)

        # Apply additional filters
        if self.filters.get('class_year'):
            if self.school_type == 'primary':
                orders = orders.filter(primary_student__class_year=self.filters['class_year'])
            else:
                orders = orders.filter(student__class_year=self.filters['class_year'])

        if self.filters.get('teacher_id'):
            orders = orders.filter(primary_student__teacher_id=self.filters['teacher_id'])

        if self.filters.get('delivery_days'):
            orders = orders.filter(selected_day__in=self.filters['delivery_days'])

        return orders

    def collect_data(self):
        """Collect data for all report sections"""
        self.data = {
            'school_info': self.get_school_info(),
            'executive_summary': self.get_executive_summary(),
            'weekly_order_numbers': self.get_weekly_order_numbers(),
            'registered_vs_ordering': self.get_registered_vs_ordering(),
            'weekly_non_orderers': self.get_weekly_non_orderers(),
            'class_teacher_breakdown': self.get_class_teacher_breakdown(),
            'week_comparisons': self.get_week_comparisons(),
            'active_inactive_users': self.get_active_inactive_users(),
            'new_signups': self.get_new_signups(),
            'churned_parents': self.get_churned_parents(),
            'busiest_quietest_days': self.get_busiest_quietest_days(),
            'meal_popularity': self.get_meal_popularity(),
            'platform_usage': self.get_platform_usage()
        }

    def get_school_info(self):
        """Section 1: School Information"""
        school_name = self.school.school_name if self.school_type == 'primary' else self.school.secondary_school_name
        eircode = self.school.school_eircode if self.school_type == 'primary' else self.school.secondary_school_eircode

        return {
            'name': school_name,
            'eircode': eircode,
            'type': self.school_type.title(),
            'report_period': f"{self.start_date.strftime('%B %d, %Y')} to {self.end_date.strftime('%B %d, %Y')}",
            'generated_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'logo_base64': self.get_logo_base64()
        }

    def get_executive_summary(self):
        """Executive Summary with key metrics"""
        orders = self.get_filtered_orders()

        stats = orders.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price'),
            avg_order_value=Avg('total_price')
        )

        # Get unique users count
        if self.school_type == 'primary':
            unique_users = orders.values('user_id').distinct().count()
        else:
            unique_users = orders.values('student_id').distinct().count()

        # Most popular day
        popular_day = orders.values('selected_day').annotate(
            count=Count('id')
        ).order_by('-count').first()

        # Top menu item
        top_item = OrderItem.objects.filter(
            order__in=orders
        ).values('_menu_name').annotate(
            total=Sum('quantity')
        ).order_by('-total').first()

        return {
            'total_orders': self.safe_int(stats['total_orders']),
            'total_revenue': self.safe_float(stats['total_revenue']),
            'avg_order_value': self.safe_float(stats['avg_order_value']),
            'total_users': unique_users,
            'most_popular_day': popular_day['selected_day'] if popular_day else 'N/A',
            'most_popular_day_count': popular_day['count'] if popular_day else 0,
            'top_menu_item': top_item['_menu_name'] if top_item else 'N/A',
            'top_menu_item_count': self.safe_int(top_item['total']) if top_item else 0
        }

    def get_weekly_order_numbers(self):
        """Section 2: Weekly Order Numbers Detailed"""
        orders = self.get_filtered_orders()

        weekly_data = aggregate_by_week(orders, self.start_date, self.end_date)

        # Calculate week-over-week changes
        for i in range(1, len(weekly_data)):
            prev_count = weekly_data[i-1]['count']
            current_count = weekly_data[i]['count']
            change_percent = calculate_percentage_change(prev_count, current_count)

            weekly_data[i]['change_percent'] = self.safe_float(change_percent)
            weekly_data[i]['change_direction'] = 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable'
            weekly_data[i]['avg_per_order'] = self.safe_round(weekly_data[i]['revenue'] / weekly_data[i]['count'], 2) if weekly_data[i]['count'] > 0 else 0

        if weekly_data:
            weekly_data[0]['change_percent'] = 0
            weekly_data[0]['change_direction'] = 'stable'
            weekly_data[0]['avg_per_order'] = self.safe_round(weekly_data[0]['revenue'] / weekly_data[0]['count'], 2) if weekly_data[0]['count'] > 0 else 0

        # Calculate summary stats
        total_orders = sum(w['count'] for w in weekly_data)
        avg_orders_per_week = total_orders / len(weekly_data) if weekly_data else 0
        peak_week = max(weekly_data, key=lambda x: x['count']) if weekly_data else None
        lowest_week = min(weekly_data, key=lambda x: x['count']) if weekly_data else None

        return {
            'weekly_data': weekly_data,
            'total_orders': total_orders,
            'avg_orders_per_week': self.safe_round(avg_orders_per_week, 1),
            'peak_week': peak_week,
            'lowest_week': lowest_week
        }

    def get_registered_vs_ordering(self):
        """Section 3: Registered vs Ordering Analysis"""
        if self.school_type == 'primary':
            total_registered = PrimaryStudentsRegister.objects.filter(
                school_id=self.school.id
            ).count()

            ordering_users = self.get_filtered_orders().values(
                'primary_student_id'
            ).distinct().count()

        else:
            total_registered = SecondaryStudent.objects.filter(
                school_id=self.school.id
            ).count()

            ordering_users = self.get_filtered_orders().values(
                'student_id'
            ).distinct().count()

        non_ordering = total_registered - ordering_users
        ordering_percentage = self.safe_round((ordering_users / total_registered * 100) if total_registered > 0 else 0, 1)

        # Get list of non-ordering users (if detailed lists enabled)
        non_ordering_list = []
        if self.filters.get('include_detailed_lists'):
            if self.school_type == 'primary':
                ordering_ids = set(self.get_filtered_orders().values_list('primary_student_id', flat=True).distinct())
                all_students = PrimaryStudentsRegister.objects.filter(school_id=self.school.id)

                for student in all_students:
                    if student.id not in ordering_ids:
                        # Get last order date
                        last_order = Order.objects.filter(
                            primary_student_id=student.id
                        ).order_by('-created_at').first()

                        non_ordering_list.append({
                            'child_name': f"{student.first_name} {student.last_name}",
                            'parent_id': student.parent_id if student.parent else 'N/A',
                            'class_teacher': f"{student.teacher.teacher_name} - {student.teacher.class_year}" if student.teacher else 'N/A',
                            'last_order': last_order.created_at.date() if last_order else 'Never',
                            'days_inactive': (datetime.now().date() - last_order.created_at.date()).days if last_order else 'N/A'
                        })

        return {
            'total_registered': total_registered,
            'ordering_users': ordering_users,
            'ordering_percentage': ordering_percentage,
            'non_ordering': non_ordering,
            'non_ordering_percentage': self.safe_round(100 - ordering_percentage, 1),
            'non_ordering_list': non_ordering_list[:100]  # Limit to 100 for PDF size
        }

    def get_weekly_non_orderers(self):
        """Section 4: Weekly Non-Orderers Report"""
        # Get week-by-week non-ordering students
        weekly_non_orderers = []

        current = self.start_date
        week_num = 1

        while current <= self.end_date:
            week_end = min(current + timedelta(days=6), self.end_date)

            week_orders = Order.objects.filter(
                **{f'{self.school_type}_school_id': self.school.id},
                order_date__date__gte=current,
                order_date__date__lte=week_end
            )

            if self.school_type == 'primary':
                total_students = PrimaryStudentsRegister.objects.filter(school_id=self.school.id).count()
                ordering_count = week_orders.values('primary_student_id').distinct().count()
            else:
                total_students = SecondaryStudent.objects.filter(school_id=self.school.id).count()
                ordering_count = week_orders.values('student_id').distinct().count()

            non_ordering_count = total_students - ordering_count

            weekly_non_orderers.append({
                'week_number': week_num,
                'start_date': current,
                'end_date': week_end,
                'total_students': total_students,
                'ordering': ordering_count,
                'non_ordering': non_ordering_count,
                'non_ordering_percent': self.safe_round((non_ordering_count / total_students * 100) if total_students > 0 else 0, 1)
            })

            current = week_end + timedelta(days=1)
            week_num += 1

        return {
            'weekly_data': weekly_non_orderers
        }

    def get_class_teacher_breakdown(self):
        """Section 5: Class/Teacher Breakdown"""
        if self.school_type != 'primary':
            # For secondary schools, group by class_year
            orders = self.get_filtered_orders()

            class_stats = orders.filter(
                student__isnull=False
            ).values(
                'student__class_year'
            ).annotate(
                order_count=Count('id'),
                total_revenue=Sum('total_price'),
                student_count=Count('student_id', distinct=True)
            ).order_by('student__class_year')

            breakdown = []
            for stat in class_stats:
                total_in_class = SecondaryStudent.objects.filter(
                    school_id=self.school.id,
                    class_year=stat['student__class_year']
                ).count()

                participation = self.safe_round((stat['student_count'] / total_in_class * 100) if total_in_class > 0 else 0, 1)

                breakdown.append({
                    'class_name': stat['student__class_year'],
                    'teacher_name': 'N/A',
                    'total_students': total_in_class,
                    'ordering_students': stat['student_count'],
                    'order_count': stat['order_count'],
                    'revenue': float(stat['total_revenue'] or 0),
                    'avg_per_student': self.safe_round(stat['order_count'] / stat['student_count'], 2) if stat['student_count'] > 0 else 0,
                    'participation_rate': participation
                })

            return {'breakdown': breakdown}

        # For primary schools, group by teacher
        orders = self.get_filtered_orders()

        teacher_stats = orders.filter(
            primary_student__isnull=False,
            primary_student__teacher__isnull=False
        ).values(
            'primary_student__teacher__teacher_name',
            'primary_student__teacher__class_year'
        ).annotate(
            order_count=Count('id'),
            total_revenue=Sum('total_price'),
            student_count=Count('primary_student_id', distinct=True)
        ).order_by('primary_student__teacher__class_year')

        breakdown = []
        for stat in teacher_stats:
            teacher = Teacher.objects.filter(
                teacher_name=stat['primary_student__teacher__teacher_name'],
                class_year=stat['primary_student__teacher__class_year'],
                school_id=self.school.id
            ).first()

            if teacher:
                total_in_class = PrimaryStudentsRegister.objects.filter(
                    teacher=teacher
                ).count()

                participation = self.safe_round((stat['student_count'] / total_in_class * 100) if total_in_class > 0 else 0, 1)

                # Get most popular meal in this class
                popular_meal = OrderItem.objects.filter(
                    order__in=orders.filter(primary_student__teacher=teacher)
                ).values('_menu_name').annotate(
                    total=Sum('quantity')
                ).order_by('-total').first()

                breakdown.append({
                    'teacher_name': stat['primary_student__teacher__teacher_name'],
                    'class_year': stat['primary_student__teacher__class_year'],
                    'total_students': total_in_class,
                    'ordering_students': stat['student_count'],
                    'order_count': stat['order_count'],
                    'revenue': float(stat['total_revenue'] or 0),
                    'avg_per_student': self.safe_round(stat['order_count'] / stat['student_count'], 2) if stat['student_count'] > 0 else 0,
                    'participation_rate': participation,
                    'most_popular_meal': popular_meal['_menu_name'] if popular_meal else 'N/A'
                })

        return {'breakdown': breakdown}

    def get_week_comparisons(self):
        """Section 6: Week-to-Week Comparisons"""
        weekly_data = self.data.get('weekly_order_numbers', {}).get('weekly_data', [])

        # Already calculated in weekly_order_numbers
        return {
            'weekly_data': weekly_data
        }

    def get_active_inactive_users(self):
        """Section 7: Active vs Inactive Users"""
        # Define inactive as no orders in last 7 days from end_date
        inactive_threshold = self.end_date - timedelta(days=7)

        if self.school_type == 'primary':
            total_users = PrimaryStudentsRegister.objects.filter(school_id=self.school.id).count()

            # Active: ordered in last 7 days
            active_ids = Order.objects.filter(
                primary_school_id=self.school.id,
                order_date__date__gte=inactive_threshold,
                order_date__date__lte=self.end_date
            ).values_list('primary_student_id', flat=True).distinct()

            active_count = len(set(active_ids))

            # Get inactive users list
            inactive_list = []
            if self.filters.get('include_detailed_lists'):
                all_students = PrimaryStudentsRegister.objects.filter(school_id=self.school.id)

                for student in all_students:
                    if student.id not in active_ids:
                        last_order = Order.objects.filter(
                            primary_student_id=student.id
                        ).order_by('-created_at').first()

                        # Calculate total historical orders
                        total_orders = Order.objects.filter(primary_student_id=student.id).count()
                        total_revenue = Order.objects.filter(primary_student_id=student.id).aggregate(
                            Sum('total_price')
                        )['total_price__sum'] or 0

                        inactive_list.append({
                            'child_name': f"{student.first_name} {student.last_name}",
                            'parent_id': f"PS-{student.parent_id}" if student.parent_id else 'N/A',
                            'last_order': last_order.created_at.date() if last_order else 'Never',
                            'days_inactive': (self.end_date - last_order.created_at.date()).days if last_order else 'N/A',
                            'historic_orders': total_orders,
                            'historic_revenue': float(total_revenue),
                            'category': self._categorize_inactive_user(last_order.created_at.date() if last_order else None)
                        })

        else:
            total_users = SecondaryStudent.objects.filter(school_id=self.school.id).count()

            active_ids = Order.objects.filter(
                secondary_school_id=self.school.id,
                order_date__date__gte=inactive_threshold,
                order_date__date__lte=self.end_date
            ).values_list('student_id', flat=True).distinct()

            active_count = len(set(active_ids))
            inactive_list = []  # Implement similar logic for secondary

        inactive_count = total_users - active_count

        # Sort by days inactive (most concerning first)
        if inactive_list:
            inactive_list.sort(key=lambda x: x['days_inactive'] if isinstance(x['days_inactive'], int) else 9999, reverse=True)

        return {
            'total_users': total_users,
            'active_count': active_count,
            'active_percent': self.safe_round((active_count / total_users * 100) if total_users > 0 else 0, 1),
            'inactive_count': inactive_count,
            'inactive_percent': self.safe_round((inactive_count / total_users * 100) if total_users > 0 else 0, 1),
            'inactive_list': inactive_list[:50]  # Limit to 50 for PDF size
        }

    def get_new_signups(self):
        """Section 8: New Sign-ups Per Week"""
        weekly_signups = []

        current = self.start_date
        week_num = 1

        while current <= self.end_date:
            week_end = min(current + timedelta(days=6), self.end_date)

            if self.school_type == 'primary':
                # Count children added via parent signup
                signups = PrimaryStudentsRegister.objects.filter(
                    school_id=self.school.id,
                    parent__created_at__gte=current,
                    parent__created_at__lte=week_end
                ).count()

                # Count how many placed orders
                signup_ids = PrimaryStudentsRegister.objects.filter(
                    school_id=self.school.id,
                    parent__created_at__gte=current,
                    parent__created_at__lte=week_end
                ).values_list('id', flat=True)

                ordered_count = Order.objects.filter(
                    primary_student_id__in=signup_ids
                ).values('primary_student_id').distinct().count()

            else:
                signups = SecondaryStudent.objects.filter(
                    school_id=self.school.id,
                    created_at__gte=current,
                    created_at__lte=week_end
                ).count()

                signup_ids = SecondaryStudent.objects.filter(
                    school_id=self.school.id,
                    created_at__gte=current,
                    created_at__lte=week_end
                ).values_list('id', flat=True)

                ordered_count = Order.objects.filter(
                    student_id__in=signup_ids
                ).values('student_id').distinct().count()

            conversion_rate = self.safe_round((ordered_count / signups * 100) if signups > 0 else 0, 1)

            weekly_signups.append({
                'week_number': week_num,
                'start_date': current,
                'end_date': week_end,
                'signups': signups,
                'ordered': ordered_count,
                'conversion_rate': conversion_rate
            })

            current = week_end + timedelta(days=1)
            week_num += 1

        # Calculate week-over-week change
        for i in range(1, len(weekly_signups)):
            change = calculate_percentage_change(
                weekly_signups[i-1]['signups'],
                weekly_signups[i]['signups']
            )
            weekly_signups[i]['change_percent'] = change

        if weekly_signups:
            weekly_signups[0]['change_percent'] = 0

        total_signups = sum(w['signups'] for w in weekly_signups)
        total_converted = sum(w['ordered'] for w in weekly_signups)
        overall_conversion = self.safe_round((total_converted / total_signups * 100) if total_signups > 0 else 0, 1)

        return {
            'weekly_data': weekly_signups,
            'total_signups': total_signups,
            'total_converted': total_converted,
            'overall_conversion_rate': overall_conversion
        }

    def get_churned_parents(self):
        """Section 9: Churned Parents (stopped ordering)"""
        # Define churned as: ordered before but no orders in last 30 days
        churn_threshold = self.end_date - timedelta(days=30)

        churned_list = []

        if self.school_type == 'primary':
            # Get all parents who have ordered before
            all_ordering_parents = Order.objects.filter(
                primary_school_id=self.school.id,
                user_type='parent'
            ).values_list('user_id', flat=True).distinct()

            # Get parents who ordered recently
            recent_parents = Order.objects.filter(
                primary_school_id=self.school.id,
                user_type='parent',
                order_date__date__gte=churn_threshold
            ).values_list('user_id', flat=True).distinct()

            churned_parent_ids = set(all_ordering_parents) - set(recent_parents)

            if self.filters.get('include_detailed_lists'):
                for parent_id in churned_parent_ids:
                    parent = ParentRegisteration.objects.filter(id=parent_id).first()
                    if not parent:
                        continue

                    last_order = Order.objects.filter(
                        user_id=parent_id,
                        user_type='parent'
                    ).order_by('-created_at').first()

                    total_orders = Order.objects.filter(user_id=parent_id, user_type='parent').count()
                    total_revenue = Order.objects.filter(user_id=parent_id, user_type='parent').aggregate(
                        Sum('total_price')
                    )['total_price__sum'] or 0

                    # Get children
                    children = PrimaryStudentsRegister.objects.filter(parent_id=parent_id)
                    children_names = ", ".join([f"{c.first_name} {c.last_name}" for c in children])

                    days_inactive = (self.end_date - last_order.created_at.date()).days if last_order else 999

                    churned_list.append({
                        'parent_name': f"{parent.first_name} {parent.last_name}",
                        'parent_id': f"P-{parent.id}",
                        'children': children_names,
                        'last_order': last_order.created_at.date() if last_order else 'Unknown',
                        'days_inactive': days_inactive,
                        'total_orders': total_orders,
                        'total_revenue': float(total_revenue),
                        'category': 'High' if total_revenue > 200 else 'Medium' if total_revenue > 50 else 'Low'
                    })

        # Sort by revenue impact
        churned_list.sort(key=lambda x: x['total_revenue'], reverse=True)

        high_value = [c for c in churned_list if c['category'] == 'High']
        medium_value = [c for c in churned_list if c['category'] == 'Medium']
        low_value = [c for c in churned_list if c['category'] == 'Low']

        return {
            'total_churned': len(churned_list),
            'high_value_count': len(high_value),
            'medium_value_count': len(medium_value),
            'low_value_count': len(low_value),
            'total_lost_revenue': sum(c['total_revenue'] for c in churned_list),
            'churned_list': churned_list[:30]  # Limit to 30 for PDF size
        }

    def get_busiest_quietest_days(self):
        """Section 10: Busiest and Quietest Days"""
        orders = self.get_filtered_orders()

        day_stats = aggregate_by_day_of_week(orders)

        # Convert to list and sort
        days_list = []
        for day, stats in day_stats.items():
            days_list.append({
                'day': day,
                'count': stats['count'],
                'revenue': stats['revenue'],
                'avg_order_value': self.safe_round(stats['revenue'] / stats['count'], 2) if stats['count'] > 0 else 0
            })

        days_list.sort(key=lambda x: x['count'], reverse=True)

        busiest = days_list[0] if days_list else None
        quietest = days_list[-1] if days_list and days_list[-1]['count'] > 0 else None

        # Calculate total weekly volume
        total_weekly = sum(d['count'] for d in days_list)
        for day in days_list:
            day['percent_of_week'] = self.safe_round((day['count'] / total_weekly * 100) if total_weekly > 0 else 0, 1)

        return {
            'days_data': days_list,
            'busiest_day': busiest,
            'quietest_day': quietest,
            'total_weekly_orders': total_weekly
        }

    def get_meal_popularity(self):
        """Section 11: Meal Popularity"""
        orders = self.get_filtered_orders()
        order_items = OrderItem.objects.filter(order__in=orders)

        # Top 10 meals
        top_meals = order_items.values('_menu_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('_menu_price')),
            order_count=Count('order_id', distinct=True)
        ).order_by('-total_quantity')[:10]

        # Bottom 10 meals
        bottom_meals = order_items.values('_menu_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('_menu_price'))
        ).order_by('total_quantity')[:10]

        # Calculate percentages
        total_orders = order_items.aggregate(Sum('quantity'))['quantity__sum'] or 1

        top_list = []
        for i, meal in enumerate(top_meals, 1):
            percent = self.safe_round((meal['total_quantity'] / total_orders * 100), 1)
            top_list.append({
                'rank': i,
                'meal_name': meal['_menu_name'],
                'orders': meal['total_quantity'],
                'percent': percent,
                'revenue': float(meal['total_revenue']),
                'trend': 'stable'  # TODO: Calculate trend
            })

        bottom_list = []
        for i, meal in enumerate(bottom_meals, 1):
            percent = self.safe_round((meal['total_quantity'] / total_orders * 100), 1)
            bottom_list.append({
                'rank': i,
                'meal_name': meal['_menu_name'],
                'orders': meal['total_quantity'],
                'percent': percent,
                'revenue': float(meal['total_revenue'])
            })

        return {
            'top_meals': top_list,
            'bottom_meals': bottom_list
        }

    def get_platform_usage(self):
        """Section 12: Platform Usage (iOS vs Android)"""
        if self.school_type == 'primary':
            # Parents
            ios_parents = ParentRegisteration.objects.filter(
                student_parent__school_id=self.school.id,
                ios_version__isnull=False
            ).distinct()

            android_parents = ParentRegisteration.objects.filter(
                student_parent__school_id=self.school.id,
                android_version__isnull=False
            ).distinct()

            # Staff
            ios_staff = StaffRegisteration.objects.filter(
                primary_school_id=self.school.id,
                ios_version__isnull=False
            )

            android_staff = StaffRegisteration.objects.filter(
                primary_school_id=self.school.id,
                android_version__isnull=False
            )

            # iOS versions
            ios_versions = {}
            for parent in ios_parents:
                version = parent.ios_version or 'Unknown'
                ios_versions[version] = ios_versions.get(version, 0) + 1
            for staff in ios_staff:
                version = staff.ios_version or 'Unknown'
                ios_versions[version] = ios_versions.get(version, 0) + 1

            # Android versions
            android_versions = {}
            for parent in android_parents:
                version = parent.android_version or 'Unknown'
                android_versions[version] = android_versions.get(version, 0) + 1
            for staff in android_staff:
                version = staff.android_version or 'Unknown'
                android_versions[version] = android_versions.get(version, 0) + 1

            total_ios = ios_parents.count() + ios_staff.count()
            total_android = android_parents.count() + android_staff.count()

        else:
            # Secondary students
            ios_students = SecondaryStudent.objects.filter(
                school_id=self.school.id,
                ios_version__isnull=False
            )

            android_students = SecondaryStudent.objects.filter(
                school_id=self.school.id,
                android_version__isnull=False
            )

            ios_versions = {}
            for student in ios_students:
                version = student.ios_version or 'Unknown'
                ios_versions[version] = ios_versions.get(version, 0) + 1

            android_versions = {}
            for student in android_students:
                version = student.android_version or 'Unknown'
                android_versions[version] = android_versions.get(version, 0) + 1

            total_ios = ios_students.count()
            total_android = android_students.count()

        total_users = total_ios + total_android

        # Convert to sorted lists
        ios_version_list = sorted([{'version': k, 'count': v, 'percent': round(v/total_ios*100, 1) if total_ios > 0 else 0} for k, v in ios_versions.items()], key=lambda x: x['count'], reverse=True)
        android_version_list = sorted([{'version': k, 'count': v, 'percent': round(v/total_android*100, 1) if total_android > 0 else 0} for k, v in android_versions.items()], key=lambda x: x['count'], reverse=True)

        return {
            'total_users': total_users,
            'total_ios': total_ios,
            'total_android': total_android,
            'ios_percent': round((total_ios / total_users * 100) if total_users > 0 else 0, 1),
            'android_percent': round((total_android / total_users * 100) if total_users > 0 else 0, 1),
            'ios_versions': ios_version_list,
            'android_versions': android_version_list
        }

    # ========================================================================
    # CHART GENERATION
    # ========================================================================

    def generate_charts(self):
        """Generate all charts for the report"""

        # Chart 1: Weekly orders trend
        weekly_data = self.data.get('weekly_order_numbers', {}).get('weekly_data', [])
        if weekly_data:
            chart_data = [{'x': f"Week {w['week_number']}", 'y': w['count']} for w in weekly_data]
            self.charts['weekly_orders_line'] = self.chart_generator.generate_line_chart(
                chart_data,
                'Weekly Order Trend',
                'Week',
                'Orders'
            )

        # Chart 2: Registered vs Ordering pie chart
        reg_vs_ord = self.data.get('registered_vs_ordering', {})
        if reg_vs_ord:
            pie_data = [
                {'label': 'Ordering', 'value': reg_vs_ord.get('ordering_users', 0)},
                {'label': 'Not Ordering', 'value': reg_vs_ord.get('non_ordering', 0)}
            ]
            self.charts['registered_vs_ordering_pie'] = self.chart_generator.generate_pie_chart(
                pie_data,
                'Registered vs Ordering Users'
            )

        # Chart 3: Class breakdown bar chart
        class_breakdown = self.data.get('class_teacher_breakdown', {}).get('breakdown', [])
        if class_breakdown and len(class_breakdown) > 0:
            bar_data = [
                {
                    'label': f"{c.get('teacher_name', c.get('class_name', 'N/A'))}",
                    'value': c['order_count']
                }
                for c in class_breakdown[:10]  # Top 10
            ]
            self.charts['class_orders_bar'] = self.chart_generator.generate_bar_chart(
                bar_data,
                'Orders by Class/Teacher',
                'Class',
                'Orders',
                horizontal=True
            )

        # Chart 4: Day of week breakdown
        days_data = self.data.get('busiest_quietest_days', {}).get('days_data', [])
        if days_data:
            bar_data = [{'label': d['day'], 'value': d['count']} for d in days_data]
            self.charts['day_of_week_bar'] = self.chart_generator.generate_bar_chart(
                bar_data,
                'Orders by Day of Week',
                'Day',
                'Orders'
            )

        # Chart 5: Platform usage pie chart
        platform = self.data.get('platform_usage', {})
        if platform:
            pie_data = [
                {'label': f"iOS ({platform.get('ios_percent', 0)}%)", 'value': platform.get('total_ios', 0)},
                {'label': f"Android ({platform.get('android_percent', 0)}%)", 'value': platform.get('total_android', 0)}
            ]
            self.charts['platform_pie'] = self.chart_generator.generate_pie_chart(
                pie_data,
                'Platform Usage (iOS vs Android)'
            )

        # Chart 6: Top meals horizontal bar
        top_meals = self.data.get('meal_popularity', {}).get('top_meals', [])
        if top_meals:
            bar_data = [{'label': m['meal_name'][:30], 'value': m['orders']} for m in top_meals]
            self.charts['top_meals_bar'] = self.chart_generator.generate_bar_chart(
                bar_data,
                'Top 10 Most Popular Meals',
                'Meal',
                'Orders',
                horizontal=True
            )

    # ========================================================================
    # HTML AND PDF GENERATION
    # ========================================================================

    def render_html(self):
        """Render HTML template with data and charts"""
        context = {
            'school_info': self.data['school_info'],
            'executive_summary': self.data['executive_summary'],
            'weekly_order_numbers': self.data['weekly_order_numbers'],
            'registered_vs_ordering': self.data['registered_vs_ordering'],
            'weekly_non_orderers': self.data['weekly_non_orderers'],
            'class_teacher_breakdown': self.data['class_teacher_breakdown'],
            'week_comparisons': self.data['week_comparisons'],
            'active_inactive_users': self.data['active_inactive_users'],
            'new_signups': self.data['new_signups'],
            'churned_parents': self.data['churned_parents'],
            'busiest_quietest_days': self.data['busiest_quietest_days'],
            'meal_popularity': self.data['meal_popularity'],
            'platform_usage': self.data['platform_usage'],
            'charts': self.charts,
            'format_currency': format_currency,
            'format_percentage': format_percentage
        }

        # For now, create HTML directly (template rendering would require template file)
        html = self._create_html_directly(context)
        return html

    def _create_html_directly(self, context):
        """Create HTML directly without template file - Professional version with improved UI/UX"""
        school_info = context['school_info']
        exec_summary = context['executive_summary']
        logo_data = school_info.get('logo_base64', '')

        # Get filter information
        filters_applied = []
        if self.filters.get('date_range_preset'):
            filters_applied.append(f"Date Range: {self.filters['date_range_preset'].replace('_', ' ').title()}")
        elif self.filters.get('start_date') and self.filters.get('end_date'):
            filters_applied.append(f"Date Range: {self.filters['start_date']} to {self.filters['end_date']}")
        if self.filters.get('class_year'):
            filters_applied.append(f"Class: {self.filters['class_year']}")
        if self.filters.get('teacher_id'):
            filters_applied.append(f"Teacher ID: {self.filters['teacher_id']}")
        if self.filters.get('delivery_days'):
            filters_applied.append(f"Delivery Days: {', '.join(self.filters['delivery_days'])}")

        filters_html = ""
        if filters_applied:
            filters_html = '<div class="filters-applied"><h3>Filters Applied:</h3><ul>'
            for filter_item in filters_applied:
                filters_html += f'<li>{filter_item}</li>'
            filters_html += '</ul></div>'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{school_info['name']} - Analytics Report</title>
            <style>
                /* Global Styles */
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.5;
                    color: #2c3e50;
                    background: white;
                    font-size: 11pt;
                }}

                /* Cover Page */
                .cover-page {{
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    background: linear-gradient(135deg, #009c5b 0%, #7cb342 100%);
                    color: white;
                    page-break-after: always;
                    padding: 40px;
                }}

                .cover-logo {{
                    width: 200px;
                    height: auto;
                    margin-bottom: 40px;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                }}

                .cover-title {{
                    font-size: 48px;
                    font-weight: 700;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                }}

                .cover-subtitle {{
                    font-size: 24px;
                    font-weight: 300;
                    margin-bottom: 40px;
                    opacity: 0.9;
                }}

                .cover-info {{
                    font-size: 18px;
                    margin-top: 60px;
                    opacity: 0.8;
                }}

                .filters-applied {{
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-top: 30px;
                    text-align: left;
                    max-width: 600px;
                }}

                .filters-applied h3 {{
                    font-size: 20px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}

                .filters-applied ul {{
                    list-style: none;
                    padding: 0;
                }}

                .filters-applied li {{
                    padding: 8px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                    font-size: 16px;
                }}

                .filters-applied li:last-child {{
                    border-bottom: none;
                }}


                /* Page Header & Footer */
                @page {{
                    size: A4;
                    margin: 20mm 15mm;
                    @top-right {{
                        content: "Page " counter(page);
                        font-size: 10px;
                        color: #999;
                    }}
                }}

                .page-header {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 60px;
                    background: white;
                    border-bottom: 2px solid #9ad983;
                    padding: 15px 30px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}

                .page-header-logo {{
                    width: 80px;
                    height: auto;
                }}

                .page-header-title {{
                    font-size: 12px;
                    color: #666;
                }}

                /* Main Content */
                .content {{
                    padding: 20px 30px;
                }}

                /* Headings */
                h1 {{
                    color: #009c5b;
                    font-size: 36px;
                    margin: 30px 0 20px 0;
                    font-weight: 700;
                }}

                h2 {{
                    color: #009c5b;
                    font-size: 28px;
                    margin: 25px 0 15px 0;
                    border-bottom: 3px solid #9ad983;
                    padding-bottom: 8px;
                    page-break-after: avoid;
                    font-weight: 600;
                }}

                h3 {{
                    color: #7cb342;
                    font-size: 20px;
                    margin: 25px 0 15px 0;
                    font-weight: 600;
                }}

                /* Metric Cards */
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}

                .metric-card {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-left: 5px solid #009c5b;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }}

                .metric-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}

                .metric-value {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #009c5b;
                    margin-bottom: 8px;
                }}

                .metric-label {{
                    font-size: 14px;
                    color: #666;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}

                /* Summary Boxes */
                .summary-box {{
                    background: #e8f5e9;
                    border-left: 5px solid #7cb342;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}

                .summary-box p {{
                    margin: 8px 0;
                    font-size: 15px;
                }}

                .summary-box strong {{
                    color: #009c5b;
                }}

                /* Tables */
                table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    margin: 25px 0;
                    page-break-inside: avoid;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }}

                thead {{
                    background: linear-gradient(135deg, #009c5b 0%, #7cb342 100%);
                }}

                th {{
                    color: white;
                    padding: 15px 12px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}

                td {{
                    padding: 12px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 12px;
                }}

                tbody tr {{
                    background: white;
                    transition: background 0.2s;
                }}

                tbody tr:nth-child(even) {{
                    background: #f8f9fa;
                }}

                tbody tr:hover {{
                    background: #e8f5e9;
                }}

                /* Charts */
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                    page-break-inside: avoid;
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}

                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 5px;
                }}

                .chart-title {{
                    font-size: 18px;
                    color: #009c5b;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}

                /* Section */
                .section {{
                    page-break-inside: avoid;
                    margin-bottom: 40px;
                    padding: 20px;
                    background: white;
                }}

                .section-header {{
                    background: linear-gradient(135deg, #009c5b 0%, #7cb342 100%);
                    color: white;
                    padding: 15px 20px;
                    margin: -20px -20px 20px -20px;
                    border-radius: 8px 8px 0 0;
                }}

                /* Footer */
                .footer {{
                    text-align: center;
                    margin-top: 60px;
                    padding: 30px 40px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e8f5e9 100%);
                    border-top: 3px solid #9ad983;
                    border-radius: 8px;
                }}

                .footer p {{
                    margin: 8px 0;
                    font-size: 13px;
                    color: #666;
                }}

                .footer-logo {{
                    width: 100px;
                    height: auto;
                    margin-bottom: 15px;
                }}

                /* Highlights */
                .highlight {{
                    background: #fff9e6;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }}

                /* Status Badges */
                .badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}

                .badge-success {{
                    background: #d4edda;
                    color: #155724;
                }}

                .badge-warning {{
                    background: #fff3cd;
                    color: #856404;
                }}

                .badge-info {{
                    background: #d1ecf1;
                    color: #0c5460;
                }}
            </style>
        </head>
        <body>
            <!-- Cover Page -->
            <div class="cover-page">
                {f'<img src="{logo_data}" alt="Rafters Logo" class="cover-logo" />' if logo_data else ''}
                <div class="cover-title">School Analytics Report</div>
                <div class="cover-subtitle">{school_info['name']}</div>
                <div class="cover-subtitle" style="font-size: 18px; margin-bottom: 10px;">{school_info.get('school_type', 'Primary School')}</div>
                <div class="cover-info">
                    <p>{school_info['report_period']}</p>
                    <p style="margin-top: 20px;">Generated on {school_info['generated_date']}</p>
                </div>
                {filters_html}
            </div>

            <!-- Main Content -->
            <div class="content">
                <div class="section">
                    <h2>Executive Summary</h2>
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-value">{exec_summary['total_orders']}</div>
                            <div class="metric-label">Total Orders</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{exec_summary['total_users']}</div>
                            <div class="metric-label">Total Users</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{exec_summary.get('ordering_users', 0)}</div>
                            <div class="metric-label">Ordering Users</div>
                        </div>
                    </div>
                    <div class="summary-box">
                        <p><strong>Most Popular Day:</strong> {exec_summary['most_popular_day']} ({exec_summary['most_popular_day_count']} orders)</p>
                        <p><strong>Top Menu Item:</strong> {exec_summary['top_menu_item']} ({exec_summary['top_menu_item_count']} orders)</p>
                        <p><strong>Non-Ordering Users:</strong> {exec_summary.get('non_ordering_users', 0)}</p>
                    </div>
                </div>

                {self._render_charts_section(context)}

                {self._render_tables_section(context)}
            </div>

            <div class="footer">
                {f'<img src="{logo_data}" alt="Rafters Logo" class="footer-logo" />' if logo_data else ''}
                <p><strong>Generated by Rafters Food Service Platform</strong></p>
                <p>&copy; {datetime.now().year} Rafters. All rights reserved.</p>
                <p style="margin-top: 10px; font-size: 11px;">This report is confidential and intended solely for the use of {school_info['name']}</p>
            </div>
        </body>
        </html>
        """
        return html

    def _render_charts_section(self, context):
        """Render charts section with improved titles"""
        html = ""
        charts = context.get('charts', {})

        # Section 1: Weekly Order Numbers
        if charts.get('weekly_orders_line'):
            html += f'''
            <div class="section">
                <h2>1. Weekly Order Numbers</h2>
                <div class="chart-container">
                    <img src="{charts['weekly_orders_line']}" alt="Weekly Orders">
                </div>
            </div>
            '''

        # Section 2: Registered vs Ordering Analysis
        if charts.get('registered_vs_ordering_pie'):
            html += f'''
            <div class="section">
                <h2>2. Registered vs Ordering Analysis</h2>
                <div class="chart-container">
                    <img src="{charts['registered_vs_ordering_pie']}" alt="Registered vs Ordering">
                </div>
            </div>
            '''

        # Section 9: Busiest & Quietest Days
        if charts.get('day_of_week_bar'):
            html += f'''
            <div class="section">
                <h2>9. Busiest & Quietest Days</h2>
                <div class="chart-container">
                    <img src="{charts['day_of_week_bar']}" alt="Day of Week Analysis">
                </div>
            </div>
            '''

        # Section 10: Meal Popularity
        if charts.get('top_meals_bar'):
            html += f'''
            <div class="section">
                <h2>10. Meal Popularity</h2>
                <div class="chart-container">
                    <img src="{charts['top_meals_bar']}" alt="Top Meals">
                </div>
            </div>
            '''

        # Bottom 10 Meals
        if charts.get('bottom_meals_bar'):
            html += f'''
            <div class="section">
                <h3>Least Popular Meals</h3>
                <div class="chart-container">
                    <img src="{charts['bottom_meals_bar']}" alt="Bottom Meals">
                </div>
            </div>
            '''

        # Section 11: Platform Usage (iOS vs Android)
        if charts.get('platform_pie'):
            html += f'''
            <div class="section">
                <h2>11. Platform Usage (iOS vs Android)</h2>
                <div class="chart-container">
                    <img src="{charts['platform_pie']}" alt="Platform Usage">
                </div>
            </div>
            '''

        # New Signups per Week
        if charts.get('signups_trend'):
            html += f'''
            <div class="section">
                <h2>7. New Sign-ups Per Week</h2>
                <div class="chart-container">
                    <img src="{charts['signups_trend']}" alt="Weekly Signups">
                </div>
            </div>
            '''

        # Week-to-Week Comparisons
        if charts.get('week_comparison'):
            html += f'''
            <div class="section">
                <h2>5. Week-to-Week Comparisons</h2>
                <div class="chart-container">
                    <img src="{charts['week_comparison']}" alt="Week Comparison">
                </div>
            </div>
            '''

        return html

    def _render_tables_section(self, context):
        """Render data tables with order IDs and NO revenue data"""
        html = ""

        # Weekly data table
        weekly_data = context.get('weekly_order_numbers', {}).get('weekly_data', [])
        if weekly_data:
            html += '''
            <div class="section">
                <h3>Weekly Performance Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Week</th>
                            <th>Period</th>
                            <th>Orders</th>
                            <th>Change</th>
                            <th>New Users</th>
                            <th>Returning</th>
                        </tr>
                    </thead>
                    <tbody>
            '''
            for week in weekly_data:
                change_arrow = '↑' if week.get('change_direction') == 'up' else '↓' if week.get('change_direction') == 'down' else '→'
                html += f'''
                        <tr>
                            <td>Week {week['week_number']}</td>
                            <td>{week['start_date']} to {week['end_date']}</td>
                            <td>{week['count']}</td>
                            <td>{change_arrow} {week.get('change_percent', 0):.1f}%</td>
                            <td>{week.get('new_users', 0)}</td>
                            <td>{week.get('returning_users', 0)}</td>
                        </tr>
                '''
            html += '''
                    </tbody>
                </table>
            </div>
            '''

        # Class breakdown table
        class_breakdown = context.get('class_teacher_breakdown', {}).get('breakdown', [])
        if class_breakdown:
            html += '''
            <div class="section">
                <h2>4. Class/Teacher Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Teacher/Class</th>
                            <th>Total Students</th>
                            <th>Ordering</th>
                            <th>Non-Ordering</th>
                            <th>Orders</th>
                            <th>Participation %</th>
                            <th>Most Popular Meal</th>
                        </tr>
                    </thead>
                    <tbody>
            '''
            for c in class_breakdown:
                teacher_name = c.get('teacher_name', c.get('class_name', 'N/A'))
                class_year = c.get('class_year', '')
                top_meal = c.get('top_meal', 'N/A')
                html += f'''
                        <tr>
                            <td>{teacher_name} - {class_year}</td>
                            <td>{c['total_students']}</td>
                            <td>{c['ordering_students']}</td>
                            <td>{c['total_students'] - c['ordering_students']}</td>
                            <td>{c['order_count']}</td>
                            <td>{c['participation_rate']}%</td>
                            <td>{top_meal}</td>
                        </tr>
                '''
            html += '''
                    </tbody>
                </table>
            </div>
            '''

        # Registered vs Ordering Analysis with detailed lists
        registered_vs_ordering = context.get('registered_vs_ordering', {})
        if registered_vs_ordering:
            non_orderers = registered_vs_ordering.get('non_orderers', [])
            if non_orderers:
                html += '''
                <div class="section">
                    <h3>Registered Non-Orderers (Detailed List)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>User ID</th>
                                <th>Child Name</th>
                                <th>Parent/Student ID</th>
                                <th>Class/Year</th>
                                <th>Registration Date</th>
                                <th>Last Login</th>
                            </tr>
                        </thead>
                        <tbody>
                '''
                for user in non_orderers[:50]:  # Limit to 50 for space
                    html += f'''
                            <tr>
                                <td>{user.get('user_id', 'N/A')}</td>
                                <td>{user.get('child_name', 'N/A')}</td>
                                <td>{user.get('parent_student_id', 'N/A')}</td>
                                <td>{user.get('class_year', 'N/A')}</td>
                                <td>{user.get('registration_date', 'N/A')}</td>
                                <td>{user.get('last_login', 'Never')}</td>
                            </tr>
                    '''
                html += '''
                        </tbody>
                    </table>
                </div>
                '''

        # Weekly Non-Orderers Report
        weekly_non_orderers = context.get('weekly_non_orderers', {})
        if weekly_non_orderers:
            consistent_non_orderers = weekly_non_orderers.get('consistent_non_orderers', [])
            if consistent_non_orderers:
                html += '''
                <div class="section">
                    <h2>3. Weekly Non-Orderers Report</h2>
                    <h3>Consistent Non-Orderers (3+ Weeks Missed)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>User ID</th>
                                <th>Name</th>
                                <th>Weeks Missed</th>
                                <th>Last Order</th>
                                <th>Order ID</th>
                                <th>Weeks Since Last Order</th>
                            </tr>
                        </thead>
                        <tbody>
                '''
                for user in consistent_non_orderers[:30]:  # Limit to 30
                    html += f'''
                            <tr>
                                <td>{user.get('user_id', 'N/A')}</td>
                                <td>{user.get('name', 'N/A')}</td>
                                <td>{user.get('weeks_missed', 0)}</td>
                                <td>{user.get('last_order_date', 'Never')}</td>
                                <td>{user.get('last_order_id', 'N/A')}</td>
                                <td>{user.get('weeks_since_last_order', 'N/A')}</td>
                            </tr>
                    '''
                html += '''
                        </tbody>
                    </table>
                </div>
                '''

        # Active vs Inactive Users
        active_inactive = context.get('active_inactive_users', {})
        if active_inactive:
            html += '''
            <div class="section">
                <h2>6. Active vs Inactive Users</h2>
                <div class="metric-grid">
            '''
            for category in ['Recently Inactive', 'Moderately Inactive', 'Highly Inactive']:
                count = active_inactive.get(category, {}).get('count', 0)
                html += f'''
                    <div class="metric-card">
                        <div class="metric-value">{count}</div>
                        <div class="metric-label">{category}</div>
                    </div>
                '''
            html += '''
                </div>
            </div>
            '''

        # Churned Parents
        churned = context.get('churned_parents', {})
        if churned:
            high_value = churned.get('high_value', [])
            if high_value:
                html += '''
                <div class="section">
                    <h2>8. Churned Parents</h2>
                    <h3>High-Value Churned Parents (10+ Historic Orders)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Parent ID</th>
                                <th>Name</th>
                                <th>Last Order</th>
                                <th>Order ID</th>
                                <th>Total Orders</th>
                                <th>Days Inactive</th>
                            </tr>
                        </thead>
                        <tbody>
                '''
                for parent in high_value[:20]:  # Limit to 20
                    html += f'''
                            <tr>
                                <td>{parent.get('parent_id', 'N/A')}</td>
                                <td>{parent.get('name', 'N/A')}</td>
                                <td>{parent.get('last_order_date', 'N/A')}</td>
                                <td>{parent.get('last_order_id', 'N/A')}</td>
                                <td>{parent.get('total_orders', 0)}</td>
                                <td>{parent.get('days_inactive', 0)}</td>
                            </tr>
                    '''
                html += '''
                        </tbody>
                    </table>
                </div>
                '''

        return html

    def create_pdf(self, html_content):
        """Convert HTML to PDF using WeasyPrint"""
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            # Fallback: save as HTML if WeasyPrint not installed
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"school_{self.school.id}_report_{timestamp}.html"
            html_path = os.path.join(reports_dir, filename)

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return html_path

        # Create reports directory
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"school_{self.school.id}_report_{timestamp}.pdf"
        pdf_path = os.path.join(reports_dir, filename)

        # Generate PDF
        HTML(string=html_content).write_pdf(pdf_path)

        return pdf_path

    def get_logo_base64(self):
        """Get Rafters logo as base64"""
        # Use the logo from backend static directory
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'rafters-logo.svg')

        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                return f"data:image/svg+xml;base64,{base64.b64encode(logo_data).decode()}"
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            return None

    def _categorize_inactive_user(self, last_order_date):
        """Categorize inactive user based on last order date"""
        if not last_order_date:
            return 'Never Ordered'

        days_inactive = (self.end_date - last_order_date).days

        if days_inactive <= 14:
            return 'Recently Inactive'
        elif days_inactive <= 30:
            return 'Moderately Inactive'
        else:
            return 'Highly Inactive'
