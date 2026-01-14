from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from admin_section.models import (
    Order, OrderItem, Menu, PrimarySchool,
    PrimaryStudentsRegister, StaffRegisteration, ParentRegisteration
)
import random


class Command(BaseCommand):
    help = "Create dummy order data for week 3 (Jan 13-17, 2026) for primary schools"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--orders-per-day',
            type=int,
            default=20,
            help='Number of orders to create per day per school (default: 20)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        orders_per_day = options.get('orders_per_day', 20)

        # Week 3 dates (Jan 13-17, 2026)
        week_number = 3
        year = 2026
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        # Calculate dates for week 3
        utc = pytz.UTC
        week_dates = {
            "Monday": datetime(2026, 1, 13, 0, 0, 0, tzinfo=utc),
            "Tuesday": datetime(2026, 1, 14, 0, 0, 0, tzinfo=utc),
            "Wednesday": datetime(2026, 1, 15, 0, 0, 0, tzinfo=utc),
            "Thursday": datetime(2026, 1, 16, 0, 0, 0, tzinfo=utc),
            "Friday": datetime(2026, 1, 17, 0, 0, 0, tzinfo=utc),
        }

        self.stdout.write(f"Creating dummy data for Week {week_number}, {year}")
        self.stdout.write(f"Date range: Jan 13-17, 2026")

        # Get all primary schools
        primary_schools = list(PrimarySchool.objects.all())
        if not primary_schools:
            self.stdout.write(self.style.ERROR("No primary schools found in database!"))
            return

        self.stdout.write(f"Found {len(primary_schools)} primary schools")

        # Get available menus for each day
        menus_by_day = {}
        for day in days:
            menus = list(Menu.objects.filter(
                menu_day__iexact=day,
                is_active=True,
                is_deleted=False,
                primary_schools__isnull=False
            ).distinct())
            menus_by_day[day] = menus
            self.stdout.write(f"{day}: {len(menus)} menus available")

        if not any(menus_by_day.values()):
            self.stdout.write(self.style.ERROR("No active menus found! Please create menus first."))
            return

        # Get users for creating orders
        primary_students = list(PrimaryStudentsRegister.objects.all())
        staff_users = list(StaffRegisteration.objects.filter(primary_school__isnull=False))
        parents = list(ParentRegisteration.objects.all())

        self.stdout.write(f"Available users: {len(primary_students)} students, {len(staff_users)} staff, {len(parents)} parents")

        if not primary_students and not staff_users:
            self.stdout.write(self.style.ERROR("No users found! Please create users first."))
            return

        total_orders_created = 0
        total_items_created = 0

        # Create orders for each school and each day
        for school in primary_schools:
            self.stdout.write(f"\nProcessing school: {school.school_name}")

            # Get students and staff for this school
            school_students = [s for s in primary_students if hasattr(s, 'school') and s.school == school]
            school_staff = [s for s in staff_users if s.primary_school == school]

            for day in days:
                menus = menus_by_day[day]
                if not menus:
                    continue

                order_date = week_dates[day]

                # Create student/parent orders
                student_orders_count = min(orders_per_day, len(school_students))
                for i in range(student_orders_count):
                    if school_students:
                        student = random.choice(school_students)
                        parent = random.choice(parents) if parents else None

                        # Randomly select 1-3 menu items
                        num_items = random.randint(1, min(3, len(menus)))
                        selected_menus = random.sample(menus, num_items)

                        total_price = sum([float(menu.price) * random.randint(1, 2) for menu in selected_menus])

                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Would create student order: {student.first_name} {student.last_name} "
                                f"on {day} ({order_date.date()}) - €{total_price:.2f}"
                            )
                        else:
                            # Create order
                            order = Order.objects.create(
                                user_id=parent.id if parent else student.id,
                                user_type='parent' if parent else 'student',
                                child_id=student.id if parent else None,
                                total_price=total_price,
                                week_number=week_number,
                                year=year,
                                order_date=order_date,
                                selected_day=day,
                                status='pending',
                                primary_student=student,
                                primary_school=school,
                                user_name=f"{student.first_name} {student.last_name}"
                            )

                            # Create order items
                            for menu in selected_menus:
                                quantity = random.randint(1, 2)
                                OrderItem.objects.create(
                                    order=order,
                                    menu=menu,
                                    quantity=quantity,
                                    _menu_name=menu.name,
                                    _menu_price=menu.price
                                )
                                total_items_created += 1

                            total_orders_created += 1

                # Create staff orders
                staff_orders_count = min(5, len(school_staff))  # 5 staff orders per day per school
                for i in range(staff_orders_count):
                    if school_staff:
                        staff = random.choice(school_staff)

                        # Randomly select 1-2 menu items
                        num_items = random.randint(1, min(2, len(menus)))
                        selected_menus = random.sample(menus, num_items)

                        total_price = sum([float(menu.price) * 1 for menu in selected_menus])

                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Would create staff order: {staff.first_name} {staff.last_name} "
                                f"on {day} ({order_date.date()}) - €{total_price:.2f}"
                            )
                        else:
                            # Create order
                            order = Order.objects.create(
                                user_id=staff.id,
                                user_type='staff',
                                child_id=None,
                                total_price=total_price,
                                week_number=week_number,
                                year=year,
                                order_date=order_date,
                                selected_day=day,
                                status='pending',
                                staff=staff,
                                primary_school=school,
                                user_name=f"{staff.first_name} {staff.last_name}"
                            )

                            # Create order items
                            for menu in selected_menus:
                                quantity = 1
                                OrderItem.objects.create(
                                    order=order,
                                    menu=menu,
                                    quantity=quantity,
                                    _menu_name=menu.name,
                                    _menu_price=menu.price
                                )
                                total_items_created += 1

                            total_orders_created += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would create approximately {orders_per_day * len(primary_schools) * 5} orders"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully created {total_orders_created} orders with {total_items_created} items for Week 3!"
            ))
            self.stdout.write(f"  Week: {week_number}")
            self.stdout.write(f"  Year: {year}")
            self.stdout.write(f"  Date range: Jan 13-17, 2026")
