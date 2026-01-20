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
    help = "Create dummy order data for primary schools with random orders per day"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--min-orders',
            type=int,
            default=10,
            help='Minimum orders per day per school (default: 10)',
        )
        parser.add_argument(
            '--max-orders',
            type=int,
            default=30,
            help='Maximum orders per day per school (default: 30)',
        )
        parser.add_argument(
            '--weeks',
            type=str,
            default='3,4,5',
            help='Comma-separated week numbers to generate (default: 3,4,5)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        min_orders = options.get('min_orders', 10)
        max_orders = options.get('max_orders', 30)
        weeks_str = options.get('weeks', '3,4,5')

        # Parse weeks
        try:
            weeks = [int(w.strip()) for w in weeks_str.split(',')]
        except ValueError:
            self.stdout.write(self.style.ERROR(f"Invalid week numbers: {weeks_str}"))
            return

        year = 2026
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        utc = pytz.UTC

        # Define week dates for weeks 3, 4, 5
        all_week_dates = {
            3: {
                "Monday": datetime(2026, 1, 13, 0, 0, 0, tzinfo=utc),
                "Tuesday": datetime(2026, 1, 14, 0, 0, 0, tzinfo=utc),
                "Wednesday": datetime(2026, 1, 15, 0, 0, 0, tzinfo=utc),
                "Thursday": datetime(2026, 1, 16, 0, 0, 0, tzinfo=utc),
                "Friday": datetime(2026, 1, 17, 0, 0, 0, tzinfo=utc),
            },
            4: {
                "Monday": datetime(2026, 1, 20, 0, 0, 0, tzinfo=utc),
                "Tuesday": datetime(2026, 1, 21, 0, 0, 0, tzinfo=utc),
                "Wednesday": datetime(2026, 1, 22, 0, 0, 0, tzinfo=utc),
                "Thursday": datetime(2026, 1, 23, 0, 0, 0, tzinfo=utc),
                "Friday": datetime(2026, 1, 24, 0, 0, 0, tzinfo=utc),
            },
            5: {
                "Monday": datetime(2026, 1, 27, 0, 0, 0, tzinfo=utc),
                "Tuesday": datetime(2026, 1, 28, 0, 0, 0, tzinfo=utc),
                "Wednesday": datetime(2026, 1, 29, 0, 0, 0, tzinfo=utc),
                "Thursday": datetime(2026, 1, 30, 0, 0, 0, tzinfo=utc),
                "Friday": datetime(2026, 1, 31, 0, 0, 0, tzinfo=utc),
            }
        }

        self.stdout.write(f"Creating dummy data for primary schools")
        self.stdout.write(f"Weeks: {', '.join([str(w) for w in weeks])}")
        self.stdout.write(f"Year: {year}")
        self.stdout.write(f"Orders per day: Random between {min_orders} and {max_orders}")

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
            self.stdout.write(f"{day}: {len(menus)} primary menus available")

        if not any(menus_by_day.values()):
            self.stdout.write(self.style.ERROR("No active primary school menus found! Please create menus first."))
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

        # Process each week
        for week_number in weeks:
            week_dates = all_week_dates.get(week_number)
            if not week_dates:
                self.stdout.write(self.style.WARNING(f"Week {week_number} not defined, skipping..."))
                continue

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing Week {week_number}")
            self.stdout.write(f"{'='*60}")

            # Create orders for each school and each day
            for school in primary_schools:
                self.stdout.write(f"\nSchool: {school.school_name}")

                # Get students and staff for this school
                school_students = [s for s in primary_students if hasattr(s, 'school') and s.school == school]
                school_staff = [s for s in staff_users if s.primary_school == school]
                # Get parents through their children (students) at this school
                school_parents = list(set([s.parent for s in school_students if s.parent is not None]))

                if not school_students:
                    self.stdout.write(f"  No students found for {school.school_name}, skipping...")
                    continue

                for day in days:
                    menus = menus_by_day[day]
                    if not menus:
                        continue

                    order_date = week_dates[day]

                    # Random number of orders for this day
                    orders_for_day = random.randint(min_orders, max_orders)
                    orders_for_day = min(orders_for_day, len(school_students))  # Can't exceed number of students

                    self.stdout.write(f"  {day}: Creating {orders_for_day} orders")

                    # Create parent orders for children (80% of orders)
                    parent_orders_count = int(orders_for_day * 0.8)
                    selected_students = random.sample(school_students, min(parent_orders_count, len(school_students)))

                    for student in selected_students:
                        # Try to find parent for this student's school
                        parent = random.choice(school_parents) if school_parents else None

                        # Randomly select 1-3 menu items
                        num_items = random.randint(1, min(3, len(menus)))
                        selected_menus = random.sample(menus, num_items)

                        total_price = sum([float(menu.price) * random.randint(1, 2) for menu in selected_menus])

                        if dry_run:
                            self.stdout.write(
                                f"    [DRY RUN] Would create order for {student.first_name} "
                                f"via {'parent' if parent else 'direct'} - €{total_price:.2f}"
                            )
                        else:
                            # Create order (parent orders for child)
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
                                user_name=f"{parent.first_name if parent else student.first_name} {parent.last_name if parent else student.last_name}"
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

                    # Create staff orders (remaining 20%)
                    staff_orders_count = orders_for_day - parent_orders_count
                    staff_orders_count = min(staff_orders_count, len(school_staff))

                    selected_staff = random.sample(school_staff, staff_orders_count) if school_staff and staff_orders_count > 0 else []

                    for staff in selected_staff:
                        # Randomly select 1-2 menu items
                        num_items = random.randint(1, min(2, len(menus)))
                        selected_menus = random.sample(menus, num_items)

                        total_price = sum([float(menu.price) * 1 for menu in selected_menus])

                        if dry_run:
                            self.stdout.write(
                                f"    [DRY RUN] Would create staff order for {staff.first_name} - €{total_price:.2f}"
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
                f"\n[DRY RUN] Would create approximately orders based on random ranges"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully created {total_orders_created} orders with {total_items_created} items!"
            ))
            self.stdout.write(f"  Weeks: {', '.join([str(w) for w in weeks])}")
            self.stdout.write(f"  Year: {year}")
            self.stdout.write(f"  Schools: {len(primary_schools)}")
