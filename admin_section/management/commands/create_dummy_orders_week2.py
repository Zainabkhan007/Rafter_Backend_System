from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from admin_section.models import (
    Order, OrderItem, PrimarySchool, PrimaryStudentsRegister,
    Menu, ParentRegisteration
)


class Command(BaseCommand):
    help = "Create dummy orders for week 2 for all primary schools"

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help='Year for the orders (default: current year)'
        )
        parser.add_argument(
            '--week',
            type=int,
            default=2,
            help='Week number (default: 2)'
        )
        parser.add_argument(
            '--orders-per-student',
            type=int,
            default=3,
            help='Average number of orders per student (default: 3)'
        )

    def handle(self, *args, **options):
        year = options['year']
        week_number = options['week']
        orders_per_student = options['orders_per_student']

        self.stdout.write(self.style.WARNING(
            f"Creating dummy orders for Week {week_number}, Year {year}"
        ))

        # Get all primary schools
        primary_schools = PrimarySchool.objects.all()

        if not primary_schools.exists():
            self.stdout.write(self.style.ERROR("No primary schools found!"))
            return

        self.stdout.write(f"Found {primary_schools.count()} primary schools")

        # Calculate dates for week 2
        # Week 2 typically spans from day 8 to day 14 of January (or the year)
        start_of_year = datetime(year, 1, 1)
        # Find the Monday of week 2
        days_to_monday = (7 - start_of_year.weekday()) % 7
        week_2_start = start_of_year + timedelta(days=days_to_monday + 7)  # Second Monday

        # Days of the week for ordering (Monday to Friday)
        order_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        total_orders_created = 0
        total_order_items_created = 0

        for school in primary_schools:
            self.stdout.write(f"\nProcessing school: {school.school_name}")

            # Get students from this school
            students = PrimaryStudentsRegister.objects.filter(school=school)

            if not students.exists():
                self.stdout.write(self.style.WARNING(
                    f"  No students found for {school.school_name}, skipping..."
                ))
                continue

            # Get active menus for this primary school
            menus = Menu.objects.filter(
                primary_schools=school,
                is_active=True,
                is_deleted=False
            )

            if not menus.exists():
                self.stdout.write(self.style.WARNING(
                    f"  No active menus found for {school.school_name}, skipping..."
                ))
                continue

            self.stdout.write(f"  Students: {students.count()}, Available menus: {menus.count()}")

            school_orders = 0
            school_items = 0

            # Create orders for each student
            for student in students:
                # Randomly determine how many orders this student will have (0 to orders_per_student)
                num_orders = random.randint(0, orders_per_student)

                for order_num in range(num_orders):
                    # Pick a random day of the week
                    day_index = random.randint(0, len(order_days) - 1)
                    selected_day = order_days[day_index]
                    order_date = week_2_start + timedelta(days=day_index)

                    # Determine user type and user_id
                    if student.parent:
                        user_type = 'parent'
                        user_id = student.parent.id
                        user_name = student.parent.username
                    else:
                        # If no parent, create order as student (though primary students typically need parents)
                        user_type = 'primary_student'
                        user_id = student.id
                        user_name = student.username or f"{student.first_name} {student.last_name}"

                    # Randomly select 1-3 menu items
                    num_items = random.randint(1, min(3, menus.count()))
                    selected_menus = random.sample(list(menus), num_items)

                    # Calculate total price
                    total_price = sum(float(menu.price) * random.randint(1, 2) for menu in selected_menus)

                    # Create the order
                    order = Order.objects.create(
                        user_id=user_id,
                        user_type=user_type,
                        user_name=user_name,
                        child_id=student.id,
                        total_price=total_price,
                        week_number=week_number,
                        year=year,
                        order_date=order_date,
                        created_at=timezone.now(),
                        selected_day=selected_day,
                        is_delivered=False,
                        status='pending',
                        primary_student=student,
                        primary_school=school,
                        payment_id=f"DUMMY_PAY_{random.randint(100000, 999999)}"
                    )

                    school_orders += 1
                    total_orders_created += 1

                    # Create order items for each selected menu
                    for menu in selected_menus:
                        quantity = random.randint(1, 2)
                        OrderItem.objects.create(
                            order=order,
                            menu=menu,
                            quantity=quantity,
                            _menu_name=menu.name,
                            _menu_price=menu.price
                        )
                        school_items += 1
                        total_order_items_created += 1

            self.stdout.write(self.style.SUCCESS(
                f"  Created {school_orders} orders with {school_items} order items for {school.school_name}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Total: {total_orders_created} orders with {total_order_items_created} order items created!"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✓ Orders created for Week {week_number}, {year}"
        ))
