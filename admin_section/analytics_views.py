"""
School Analytics Views
Comprehensive analytics endpoints for school dashboard and PDF reporting
"""

from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q, Avg, F, Prefetch
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import (
    PrimarySchool, SecondarySchool, Order, OrderItem,
    PrimaryStudentsRegister, SecondaryStudent, Teacher,
    StaffRegisteration, ParentRegisteration, Menu, Transaction
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_school_and_type(school_id):
    """Get school object and determine type"""
    try:
        school = PrimarySchool.objects.get(id=school_id)
        return school, 'primary'
    except PrimarySchool.DoesNotExist:
        try:
            school = SecondarySchool.objects.get(id=school_id)
            return school, 'secondary'
        except SecondarySchool.DoesNotExist:
            return None, None


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if not old_value or old_value == 0:
        return 100.0 if new_value and new_value > 0 else 0.0
    return round(((new_value - old_value) / old_value) * 100, 2)


def get_week_date_range(week_number, year):
    """Get start and end date for a given week number"""
    from datetime import datetime, timedelta
    jan_1 = datetime(year, 1, 1)
    week_start = jan_1 + timedelta(weeks=week_number - 1)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start.date(), week_end.date()


# ============================================================================
# API ENDPOINT: GET SCHOOL SUMMARY
# ============================================================================

@api_view(['GET'])
def get_school_summary(request, school_id):
    """
    Comprehensive school summary endpoint
    GET /admin_details/dashboard/school/<int:school_id>/

    Returns:
    - school_info
    - summary_stats (week-over-week comparison)
    - platform_overview (iOS/Android split)
    - quick_metrics
    - all_orders (NO pagination - returns all orders for scrolling)
    """
    try:
        # Get school and type
        school, school_type = get_school_and_type(school_id)
        if not school:
            return Response({'error': 'School not found'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate current week and last week
        now = datetime.now()
        current_week = now.isocalendar()[1]
        last_week = (now - timedelta(weeks=1)).isocalendar()[1]
        current_year = now.year
        last_week_year = (now - timedelta(weeks=1)).year

        # Week-over-week comparison
        current_week_stats = Order.objects.filter(
            **{f'{school_type}_school_id': school_id},
            week_number=current_week,
            year=current_year
        ).aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price')
        )

        last_week_stats = Order.objects.filter(
            **{f'{school_type}_school_id': school_id},
            week_number=last_week,
            year=last_week_year
        ).aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price')
        )

        # Calculate changes
        orders_change = calculate_percentage_change(
            last_week_stats['total_orders'],
            current_week_stats['total_orders']
        )

        # Get all-time stats (exclude negative prices - likely refunds or errors)
        all_time_stats = Order.objects.filter(
            **{f'{school_type}_school_id': school_id},
            total_price__gte=0  # Only count positive prices
        ).aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price')
        )

        # Get registered vs actively ordering
        if school_type == 'primary':
            total_registered = PrimaryStudentsRegister.objects.filter(school_id=school_id).count()
            children_count = PrimaryStudentsRegister.objects.filter(
                school_id=school_id,
                parent__isnull=False
            ).count()

            # Students who ordered in current week - check both primary_student FK and child_id
            orders_current_week = Order.objects.filter(
                primary_school_id=school_id,
                week_number=current_week,
                year=current_year
            )

            # Collect unique child IDs from both primary_student and child_id fields
            active_children_ids = set()

            # Get IDs from primary_student ForeignKey
            primary_student_ids = orders_current_week.exclude(
                primary_student_id__isnull=True
            ).values_list('primary_student_id', flat=True).distinct()
            active_children_ids.update(primary_student_ids)

            # Get IDs from child_id field (used by parent orders)
            child_ids = orders_current_week.exclude(
                child_id__isnull=True
            ).values_list('child_id', flat=True).distinct()
            active_children_ids.update(child_ids)

            actively_ordering = len(active_children_ids)

        else:
            total_registered = SecondaryStudent.objects.filter(school_id=school_id).count()
            children_count = total_registered

            # Students who ordered in current week - use user_id where user_type='student'
            actively_ordering = Order.objects.filter(
                secondary_school_id=school_id,
                week_number=current_week,
                year=current_year,
                user_type='student'
            ).values('user_id').distinct().count()

        active_percentage = round((actively_ordering / total_registered * 100) if total_registered > 0 else 0, 1)
        inactive_count = total_registered - actively_ordering

        # Busiest/Quietest days
        day_stats = Order.objects.filter(
            **{f'{school_type}_school_id': school_id}
        ).values('selected_day').annotate(
            count=Count('id')
        ).order_by('-count')

        busiest_day = day_stats.first() if day_stats.exists() else None
        quietest_day = day_stats.last() if day_stats.exists() else None

        # Most popular meal
        popular_meal = OrderItem.objects.filter(
            **{f'order__{school_type}_school_id': school_id}
        ).values('_menu_name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity').first()

        # Platform overview (iOS vs Android) - exclude NULL and empty strings
        if school_type == 'primary':
            ios_count = ParentRegisteration.objects.filter(
                student_parent__school_id=school_id,
                ios_version__isnull=False
            ).exclude(ios_version='').distinct().count()

            android_count = ParentRegisteration.objects.filter(
                student_parent__school_id=school_id,
                android_version__isnull=False
            ).exclude(android_version='').distinct().count()

            # Also count staff
            ios_staff = StaffRegisteration.objects.filter(
                primary_school_id=school_id,
                ios_version__isnull=False
            ).exclude(ios_version='').count()

            android_staff = StaffRegisteration.objects.filter(
                primary_school_id=school_id,
                android_version__isnull=False
            ).exclude(android_version='').count()

            ios_count += ios_staff
            android_count += android_staff

        else:
            ios_count = SecondaryStudent.objects.filter(
                school_id=school_id,
                ios_version__isnull=False
            ).exclude(ios_version='').count()

            android_count = SecondaryStudent.objects.filter(
                school_id=school_id,
                android_version__isnull=False
            ).exclude(android_version='').count()

            # Also count staff for secondary schools
            ios_staff = StaffRegisteration.objects.filter(
                secondary_school_id=school_id,
                ios_version__isnull=False
            ).exclude(ios_version='').count()

            android_staff = StaffRegisteration.objects.filter(
                secondary_school_id=school_id,
                android_version__isnull=False
            ).exclude(android_version='').count()

            ios_count += ios_staff
            android_count += android_staff

        total_app_users = ios_count + android_count
        ios_percentage = round((ios_count / total_app_users * 100) if total_app_users > 0 else 0, 1)
        android_percentage = round((android_count / total_app_users * 100) if total_app_users > 0 else 0, 1)

        # New signups this week vs last week
        if school_type == 'primary':
            # Count children added by parents this week
            this_week_signups = PrimaryStudentsRegister.objects.filter(
                school_id=school_id,
                parent__created_at__gte=now - timedelta(days=7)
            ).count()

            last_week_signups = PrimaryStudentsRegister.objects.filter(
                school_id=school_id,
                parent__created_at__gte=now - timedelta(days=14),
                parent__created_at__lt=now - timedelta(days=7)
            ).count()
        else:
            this_week_signups = SecondaryStudent.objects.filter(
                school_id=school_id,
                created_at__gte=now - timedelta(days=7)
            ).count()

            last_week_signups = SecondaryStudent.objects.filter(
                school_id=school_id,
                created_at__gte=now - timedelta(days=14),
                created_at__lt=now - timedelta(days=7)
            ).count()

        signup_change = calculate_percentage_change(last_week_signups, this_week_signups)

        # Get ALL orders (no pagination) - for scrolling in frontend
        all_orders = Order.objects.filter(
            **{f'{school_type}_school_id': school_id}
        ).select_related(
            'primary_student', 'student', 'staff', 'primary_student__parent'
        ).prefetch_related(
            'order_items'
        ).order_by('-created_at')

        orders_data = []
        for order in all_orders:
            # Get child name - handle all relationship types
            child_name = None
            parent_staff_name = None

            # Primary school logic
            if school_type == 'primary':
                # Check primary_student ForeignKey first
                if order.primary_student:
                    child_name = f"{order.primary_student.first_name} {order.primary_student.last_name}"
                    # Get parent name if exists
                    if order.primary_student.parent:
                        parent_staff_name = f"{order.primary_student.parent.first_name} {order.primary_student.parent.last_name}"
                # If no primary_student FK, check child_id (for parent orders)
                elif order.child_id:
                    try:
                        child = PrimaryStudentsRegister.objects.get(id=order.child_id)
                        child_name = f"{child.first_name} {child.last_name}"
                        # Get parent name from user_id if user_type is parent
                        if order.user_type == 'parent' and order.user_id:
                            try:
                                parent = ParentRegisteration.objects.get(id=order.user_id)
                                parent_staff_name = f"{parent.first_name} {parent.last_name}"
                            except ParentRegisteration.DoesNotExist:
                                pass
                    except PrimaryStudentsRegister.DoesNotExist:
                        pass
                # Check if it's a staff order
                elif order.staff:
                    child_name = f"{order.staff.first_name} {order.staff.last_name}"
                    parent_staff_name = "Staff Member"
                # Fallback: check user_type and user_id
                elif order.user_type == 'staff' and order.user_id:
                    try:
                        staff = StaffRegisteration.objects.get(id=order.user_id)
                        child_name = f"{staff.first_name} {staff.last_name}"
                        parent_staff_name = "Staff Member"
                    except StaffRegisteration.DoesNotExist:
                        pass
            # Secondary school logic
            else:
                if order.student:
                    child_name = f"{order.student.first_name} {order.student.last_name}"
                elif order.staff:
                    child_name = f"{order.staff.first_name} {order.staff.last_name}"
                    parent_staff_name = "Staff Member"
                # Fallback: check user_id
                elif order.user_type == 'student' and order.user_id:
                    try:
                        student = SecondaryStudent.objects.get(id=order.user_id)
                        child_name = f"{student.first_name} {student.last_name}"
                    except SecondaryStudent.DoesNotExist:
                        pass
                elif order.user_type == 'staff' and order.user_id:
                    try:
                        staff = StaffRegisteration.objects.get(id=order.user_id)
                        child_name = f"{staff.first_name} {staff.last_name}"
                        parent_staff_name = "Staff Member"
                    except StaffRegisteration.DoesNotExist:
                        pass

            # Build order data
            # Calculate day name from created_at
            created_at_day = order.created_at.strftime('%A') if order.created_at else None

            # Format order_date if available
            order_date_formatted = None
            if hasattr(order, 'order_date') and order.order_date:
                if hasattr(order.order_date, 'strftime'):
                    order_date_formatted = order.order_date.strftime('%d %b %Y')

            order_dict = {
                'order_id': order.id,
                'child_name': child_name or "N/A",
                'selected_day': order.selected_day,
                'order_date': order_date_formatted,
                'status': order.status,
                'total_amount': float(order.total_price),
                'created_at': order.created_at.isoformat(),
                'created_at_day': created_at_day
            }

            # Add parent/staff name only for primary schools
            if school_type == 'primary' and parent_staff_name:
                order_dict['parent_staff_name'] = parent_staff_name

            orders_data.append(order_dict)

        # Build response
        response_data = {
            'school_info': {
                'id': school.id,
                'name': school.school_name if school_type == 'primary' else school.secondary_school_name,
                'school_type': school_type,
                'address': school.school_eircode if school_type == 'primary' else school.secondary_school_eircode,
                'total_students': total_registered,
                'total_staff': StaffRegisteration.objects.filter(
                    **{f'{school_type}_school_id': school_id}
                ).count() if school_type == 'primary' else 0
            },

            'summary_stats': {
                'total_registered': total_registered,
                'actively_ordering': actively_ordering,
                'active_percentage': active_percentage,
                'inactive_count': inactive_count,
                'children_count': children_count,
                'this_week_orders': current_week_stats['total_orders'] or 0,
                'last_week_orders': last_week_stats['total_orders'] or 0,
                'week_trend': 'up' if orders_change > 0 else 'down' if orders_change < 0 else 'stable',
                'week_change_percent': abs(orders_change),
                'all_time_total_orders': all_time_stats['total_orders'] or 0,
                'all_time_total_revenue': round(float(all_time_stats['total_revenue'] or 0), 2)
            },

            'platform_overview': {
                'ios_count': ios_count,
                'ios_percentage': ios_percentage,
                'android_count': android_count,
                'android_percentage': android_percentage,
                'total_app_users': total_app_users
            },

            'quick_metrics': {
                'new_signups_this_week': this_week_signups,
                'signup_trend': 'up' if signup_change > 0 else 'down' if signup_change < 0 else 'stable',
                'signup_change_percent': abs(signup_change),
                'churned_parents_count': 0,  # TODO: Calculate churned count
                'busiest_day': busiest_day['selected_day'] if busiest_day else 'N/A',
                'busiest_day_orders': busiest_day['count'] if busiest_day else 0,
                'quietest_day': quietest_day['selected_day'] if quietest_day else 'N/A',
                'quietest_day_orders': quietest_day['count'] if quietest_day else 0,
                'most_popular_meal': popular_meal['_menu_name'] if popular_meal else 'N/A',
                'most_popular_meal_count': popular_meal['total_quantity'] if popular_meal else 0
            },

            'orders': orders_data  # All orders - no pagination
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API ENDPOINT: GET FILTER OPTIONS
# ============================================================================

@api_view(['GET'])
def get_filter_options(request, school_id):
    """
    GET /admin_details/dashboard/school/<int:school_id>/filter-options/

    Returns available filters for the school:
    - Classes/teachers (primary only)
    - Delivery days
    - Date range presets
    """
    try:
        # Get school and type
        school, school_type = get_school_and_type(school_id)
        if not school:
            return Response({'error': 'School not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get classes and teachers (primary only)
        classes_teachers = []
        if school_type == 'primary':
            teachers = Teacher.objects.filter(
                school_id=school_id
            ).values('id', 'teacher_name', 'class_year').order_by('class_year')

            classes_teachers = [
                {
                    'teacher_id': t['id'],
                    'teacher_name': t['teacher_name'],
                    'class_year': t['class_year'],
                    'label': f"{t['teacher_name']} - {t['class_year']}"
                }
                for t in teachers
            ]
        else:
            # For secondary schools, get unique class years
            class_years = SecondaryStudent.objects.filter(
                school_id=school_id
            ).values_list('class_year', flat=True).distinct().order_by('class_year')

            classes_teachers = [
                {
                    'class_year': cy,
                    'label': cy
                }
                for cy in class_years
            ]

        # Get available delivery days
        delivery_days = Order.objects.filter(
            **{f'{school_type}_school_id': school_id}
        ).values_list('selected_day', flat=True).distinct().order_by('selected_day')

        # Date range presets
        today = datetime.now().date()
        presets = {
            'this_week': {
                'label': 'This Week',
                'start_date': str(today - timedelta(days=today.weekday())),
                'end_date': str(today)
            },
            'last_week': {
                'label': 'Last Week',
                'start_date': str(today - timedelta(days=today.weekday() + 7)),
                'end_date': str(today - timedelta(days=today.weekday() + 1))
            },
            'last_4_weeks': {
                'label': 'Last 4 Weeks',
                'start_date': str(today - timedelta(weeks=4)),
                'end_date': str(today)
            },
            'this_month': {
                'label': 'This Month',
                'start_date': str(today.replace(day=1)),
                'end_date': str(today)
            },
            'last_month': {
                'label': 'Last Month',
                'start_date': str((today.replace(day=1) - timedelta(days=1)).replace(day=1)),
                'end_date': str(today.replace(day=1) - timedelta(days=1))
            },
            'last_3_months': {
                'label': 'Last 3 Months',
                'start_date': str(today - timedelta(days=90)),
                'end_date': str(today)
            }
        }

        return Response({
            'school_id': school_id,
            'school_type': school_type,
            'classes_teachers': classes_teachers,
            'delivery_days': list(delivery_days),
            'date_range_presets': presets
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API ENDPOINT: GENERATE PDF REPORT
# ============================================================================

@api_view(['POST'])
def generate_school_report(request, school_id):
    """
    POST /admin_details/dashboard/school/<int:school_id>/generate-report/

    Request body (Weekly Professional Report - NEW):
    {
        "week_number": 3,  # required for weekly report
        "year": 2026       # required for weekly report
    }

    OR (Flexible Date Range Report - OLD):
    {
        "start_date": "2024-01-01",  # optional if date_range preset provided
        "end_date": "2024-12-31",    # optional if date_range preset provided
        "date_range": "last_4_weeks",  # optional preset: this_week, last_week, last_4_weeks, this_month, last_month, last_3_months
        "class_year": "Junior Infants",  # optional
        "teacher_id": 123,  # optional
        "delivery_days": ["Monday", "Tuesday"],  # optional
        "include_detailed_lists": true  # optional - includes detailed user lists
    }

    Returns:
    {
        "status": "success",
        "download_url": "/media/reports/school_123_report_20240113.pdf",
        "filename": "St_Marys_Primary_School_Report_2024-01-13.pdf",
        "generated_at": "2024-01-13T10:30:00Z",
        "expires_at": "2024-01-14T10:30:00Z",
        "file_size_mb": 2.5,
        "total_pages": 28
    }
    """
    try:
        import os
        from django.conf import settings

        # Get school and type
        school, school_type = get_school_and_type(school_id)
        if not school:
            return Response({'error': 'School not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get date range preset if provided
        date_range_preset = request.data.get('date_range')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # If preset provided and no custom dates, calculate dates from preset
        if date_range_preset and (not start_date or not end_date):
            today = datetime.now().date()

            if date_range_preset == 'this_week':
                start_date = str(today - timedelta(days=today.weekday()))
                end_date = str(today)
            elif date_range_preset == 'last_week':
                start_date = str(today - timedelta(days=today.weekday() + 7))
                end_date = str(today - timedelta(days=today.weekday() + 1))
            elif date_range_preset == 'last_4_weeks':
                start_date = str(today - timedelta(weeks=4))
                end_date = str(today)
            elif date_range_preset == 'this_month':
                start_date = str(today.replace(day=1))
                end_date = str(today)
            elif date_range_preset == 'last_month':
                first_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
                last_of_last_month = today.replace(day=1) - timedelta(days=1)
                start_date = str(first_of_last_month)
                end_date = str(last_of_last_month)
            elif date_range_preset == 'last_3_months':
                start_date = str(today - timedelta(days=90))
                end_date = str(today)

        # Parse filters
        filters = {
            'start_date': start_date,
            'end_date': end_date,
            'date_range_preset': date_range_preset,
            'class_year': request.data.get('class_year'),
            'teacher_id': request.data.get('teacher_id'),
            'delivery_days': request.data.get('delivery_days', []),
            'include_detailed_lists': request.data.get('include_detailed_lists', True)
        }

        # Check if this is a weekly report (new professional PDF)
        week_number = request.data.get('week_number')
        year = request.data.get('year')

        # ALWAYS use ProfessionalPDFGenerator for consistent PDF format
        # Auto-detect week from date range preset or custom dates
        # Priority 1: Explicit week_number and year from request
        # Priority 2: Calculate week from date_range_preset
        # Priority 3: Custom date range - use end date's week
        # Priority 4: DEFAULT - use current week

        if not week_number:
            today = datetime.now()

            if date_range_preset == 'this_week':
                target_date = today
            elif date_range_preset == 'last_week':
                target_date = today - timedelta(weeks=1)
            elif date_range_preset == 'last_4_weeks':
                # Use most recent complete week (last week)
                target_date = today - timedelta(weeks=1)
            elif date_range_preset == 'this_month':
                target_date = today
            elif date_range_preset == 'last_month':
                # Use middle of last month to get a week from last month
                first_of_this_month = today.replace(day=1)
                target_date = first_of_this_month - timedelta(days=15)
            elif date_range_preset == 'last_3_months':
                # Use most recent complete week
                target_date = today - timedelta(weeks=1)
            elif start_date and end_date:
                # Custom date range - use end date's week
                try:
                    from datetime import datetime as dt
                    end_dt = dt.strptime(end_date, '%Y-%m-%d')
                    target_date = end_dt
                except (ValueError, TypeError):
                    target_date = today
            else:
                # DEFAULT: No parameters provided, use current week
                target_date = today

            year = target_date.year
            week_number = target_date.isocalendar()[1]

        # Always use ProfessionalPDFGenerator for consistent PDF format
        if week_number and year:
            # Use new professional PDF generator for weekly reports
            from .professional_pdf_generator import ProfessionalPDFGenerator
            generator = ProfessionalPDFGenerator(
                school=school,
                week_number=int(week_number),
                year=int(year),
                school_type=school_type,
                filters=filters  # Pass filters to the generator
            )
            pdf_buffer = generator.generate()

            # Save to file
            import os
            from django.conf import settings
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            school_name = school.school_name if school_type == 'primary' else school.secondary_school_name
            filename = f"{school_name.replace(' ', '_')}_Week{week_number}_{year}_Report.pdf"
            pdf_path = os.path.join(reports_dir, filename)

            with open(pdf_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
        else:
            # Fallback: This should never happen now since we always calculate week_number
            # But keep as safety net - use current week
            today = datetime.now()
            week_number = today.isocalendar()[1]
            year = today.year

            from .professional_pdf_generator import ProfessionalPDFGenerator
            generator = ProfessionalPDFGenerator(
                school=school,
                week_number=int(week_number),
                year=int(year),
                school_type=school_type
            )
            pdf_buffer = generator.generate()

            import os
            from django.conf import settings
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            school_name = school.school_name if school_type == 'primary' else school.secondary_school_name
            filename = f"{school_name.replace(' ', '_')}_Week{week_number}_{year}_Report.pdf"
            pdf_path = os.path.join(reports_dir, filename)

            with open(pdf_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())

        # Get file info
        file_size = os.path.getsize(pdf_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)

        # Calculate expiry (24 hours from now)
        generated_at = datetime.now()
        expires_at = generated_at + timedelta(hours=24)

        # Get relative path for download URL
        relative_path = pdf_path.replace(str(settings.MEDIA_ROOT), '').lstrip('/')
        download_url = f"{settings.MEDIA_URL}{relative_path}"

        school_name = school.school_name if school_type == 'primary' else school.secondary_school_name
        filename = f"{school_name.replace(' ', '_')}_Report_{generated_at.strftime('%Y-%m-%d')}.pdf"

        # Count pages in PDF (simple estimation based on sections)
        # Each section averages 2-3 pages, plus cover and TOC
        estimated_pages = 3 + (len([k for k, v in filters.items() if k.startswith('include_') and v]) * 2.5)

        return Response({
            'status': 'success',
            'download_url': download_url,
            'filename': filename,
            'generated_at': generated_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'file_size_mb': file_size_mb,
            'total_pages': int(estimated_pages)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# PDF PREVIEW - Web preview for CSS/Design iteration
# ============================================================================

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def preview_school_report(request):
    """
    Web preview for PDF report - renders HTML for easy CSS iteration

    GET Parameters:
    - school_id: ID of the school (required)
    - school_type: 'primary' or 'secondary' (optional, auto-detected if not provided)
    - week_number: Week number (optional, defaults to current week)
    - year: Year (optional, defaults to current year)

    Example: /admin_details/dashboard/preview-report/?school_id=1&week_number=3&year=2026
    """
    try:
        # Get parameters
        school_id = request.GET.get('school_id')
        school_type = request.GET.get('school_type')
        week_number = request.GET.get('week_number')
        year = request.GET.get('year')

        if not school_id:
            return HttpResponse("""
            <html>
            <head>
                <title>PDF Preview - Select Parameters</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #053F34; }
                    .form-group { margin-bottom: 20px; }
                    label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
                    input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
                    button { background: #009C5B; color: white; padding: 12px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                    button:hover { background: #053F34; }
                    .info { background: #f0f8ff; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
                    .info code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>PDF Report Preview</h1>
                    <div class="info">
                        <strong>How to use:</strong><br>
                        Select a school and week to preview the PDF report in your browser.
                        This allows you to iterate on CSS/design without generating actual PDFs.
                    </div>
                    <form method="GET">
                        <div class="form-group">
                            <label>School ID *</label>
                            <input type="number" name="school_id" required placeholder="Enter school ID">
                        </div>
                        <div class="form-group">
                            <label>School Type</label>
                            <select name="school_type">
                                <option value="">Auto-detect</option>
                                <option value="primary">Primary</option>
                                <option value="secondary">Secondary</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Week Number</label>
                            <input type="number" name="week_number" placeholder="Current week if empty" min="1" max="53">
                        </div>
                        <div class="form-group">
                            <label>Year</label>
                            <input type="number" name="year" placeholder="Current year if empty" min="2020" max="2030">
                        </div>
                        <button type="submit">Preview Report</button>
                    </form>
                </div>
            </body>
            </html>
            """, content_type='text/html')

        # Get school
        school = None
        if school_type == 'primary':
            try:
                school = PrimarySchool.objects.get(id=school_id)
            except PrimarySchool.DoesNotExist:
                return HttpResponse(f"<h1>Error</h1><p>Primary school with ID {school_id} not found</p>", status=404)
        elif school_type == 'secondary':
            try:
                school = SecondarySchool.objects.get(id=school_id)
            except SecondarySchool.DoesNotExist:
                return HttpResponse(f"<h1>Error</h1><p>Secondary school with ID {school_id} not found</p>", status=404)
        else:
            # Auto-detect
            school, school_type = get_school_and_type(int(school_id))
            if not school:
                return HttpResponse(f"<h1>Error</h1><p>School with ID {school_id} not found</p>", status=404)

        # Default to current week/year if not provided
        today = datetime.now()
        if not week_number:
            week_number = today.isocalendar()[1]
        if not year:
            year = today.year

        # Generate HTML preview
        from .professional_pdf_generator import ProfessionalPDFGenerator
        generator = ProfessionalPDFGenerator(
            school=school,
            week_number=int(week_number),
            year=int(year),
            school_type=school_type
        )

        html_content = generator.generate_html_preview()

        # Add navigation bar at top for easy parameter changes
        school_name = school.school_name if school_type == 'primary' else school.secondary_school_name
        nav_bar = f"""
        <div style="position: fixed; top: 0; left: 0; right: 0; background: #053F34; color: white; padding: 10px 20px; z-index: 9999; display: flex; align-items: center; justify-content: space-between; font-family: Arial, sans-serif;">
            <div>
                <strong>Preview:</strong> {school_name} | Week {week_number}, {year} | Type: {school_type.title()}
            </div>
            <div>
                <a href="?school_id={school_id}&school_type={school_type}&week_number={int(week_number)-1}&year={year}" style="color: #CAFEC7; margin-right: 15px;">← Prev Week</a>
                <a href="?school_id={school_id}&school_type={school_type}&week_number={int(week_number)+1}&year={year}" style="color: #CAFEC7; margin-right: 15px;">Next Week →</a>
                <a href="?" style="color: #FCCB5E;">Change School</a>
            </div>
        </div>
        <div style="height: 50px;"></div>
        """

        # Insert nav bar after body tag
        html_content = html_content.replace('<body>', '<body>' + nav_bar)

        return HttpResponse(html_content, content_type='text/html')

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; padding: 40px;">
            <h1 style="color: red;">Error Generating Preview</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <pre style="background: #f0f0f0; padding: 20px; overflow: auto;">{error_details}</pre>
            <a href="?">← Back to form</a>
        </body>
        </html>
        """, status=500)
