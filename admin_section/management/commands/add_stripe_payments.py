from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from admin_section.models import (
    Order, Transaction, PrimarySchool, SecondarySchool,
    SecondaryStudent, StaffRegisteration, ParentRegisteration
)
import random
from decimal import Decimal


class Command(BaseCommand):
    help = "Add dummy stripe payment transactions for orders in a school"

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            required=True,
            help='School ID',
        )
        parser.add_argument(
            '--school-type',
            type=str,
            choices=['primary', 'secondary'],
            required=True,
            help='School type (primary or secondary)',
        )
        parser.add_argument(
            '--week-number',
            type=int,
            help='Week number (optional, will process all orders if not specified)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2026,
            help='Year (default: 2026)',
        )
        parser.add_argument(
            '--stripe-percentage',
            type=int,
            default=70,
            help='Percentage of orders to pay with Stripe (rest will be credits). Default: 70%%',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        school_id = options['school_id']
        school_type = options['school_type']
        week_number = options.get('week_number')
        year = options['year']
        stripe_percentage = options['stripe_percentage']
        dry_run = options.get('dry_run', False)

        # Get the school
        try:
            if school_type == 'primary':
                school = PrimarySchool.objects.get(id=school_id)
                school_name = school.school_name
            else:
                school = SecondarySchool.objects.get(id=school_id)
                school_name = school.secondary_school_name
        except (PrimarySchool.DoesNotExist, SecondarySchool.DoesNotExist):
            self.stdout.write(self.style.ERROR(f"School with ID {school_id} not found!"))
            return

        self.stdout.write(f"\nProcessing: {school_name} ({school_type})")
        self.stdout.write(f"Year: {year}")
        if week_number:
            self.stdout.write(f"Week: {week_number}")
        else:
            self.stdout.write("Week: All weeks")
        self.stdout.write(f"Stripe percentage: {stripe_percentage}%")

        # Get orders for this school
        if school_type == 'primary':
            orders_query = Order.objects.filter(
                primary_school=school,
                year=year
            )
        else:
            orders_query = Order.objects.filter(
                secondary_school=school,
                year=year
            )

        if week_number:
            orders_query = orders_query.filter(week_number=week_number)

        orders = list(orders_query.exclude(status='cancelled'))

        if not orders:
            self.stdout.write(self.style.WARNING("No orders found for this school!"))
            return

        self.stdout.write(f"Found {len(orders)} orders")

        # Check for existing transactions
        orders_with_transactions = Order.objects.filter(
            id__in=[o.id for o in orders],
            transactions__isnull=False
        ).distinct().count()

        if orders_with_transactions > 0:
            self.stdout.write(self.style.WARNING(
                f"{orders_with_transactions} orders already have transactions. "
                f"These will be skipped."
            ))

        transactions_created = 0
        stripe_count = 0
        credits_count = 0

        utc = pytz.UTC

        for order in orders:
            # Skip if order already has a transaction
            if order.transactions.exists():
                continue

            # Determine payment method (stripe_percentage% stripe, rest credits)
            use_stripe = random.randint(1, 100) <= stripe_percentage
            payment_method = 'stripe' if use_stripe else 'credits'

            # Get user details
            user_id = order.user_id
            user_type = order.user_type
            user_reference = None

            if user_type == 'parent':
                try:
                    user_reference = ParentRegisteration.objects.get(id=user_id)
                except ParentRegisteration.DoesNotExist:
                    pass
            elif user_type == 'student':
                try:
                    user_reference = SecondaryStudent.objects.get(id=user_id)
                except SecondaryStudent.DoesNotExist:
                    pass
            elif user_type == 'staff':
                try:
                    user_reference = StaffRegisteration.objects.get(id=user_id)
                except StaffRegisteration.DoesNotExist:
                    pass

            # Create transaction timestamp (same as order date or slightly after)
            transaction_time = order.order_date + timedelta(minutes=random.randint(1, 30))
            if transaction_time.tzinfo is None:
                transaction_time = utc.localize(transaction_time)

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would create {payment_method} transaction for order {order.id}: "
                    f"€{order.total_price:.2f} ({user_type})"
                )
            else:
                # Create transaction
                transaction = Transaction.objects.create(
                    user_id=user_id,
                    user_type=user_type,
                    transaction_type='payment',
                    payment_method=payment_method,
                    amount=Decimal(str(order.total_price)),
                    order=order,
                    payment_intent_id=f"pi_dummy_{order.id}_{random.randint(100000, 999999)}" if use_stripe else None,
                    description=f"Payment for order {order.id} - {order.selected_day}",
                    created_at=transaction_time,
                    parent=user_reference if user_type == 'parent' else None,
                    staff=user_reference if user_type == 'staff' else None,
                    student=user_reference if user_type == 'student' else None,
                )

                transactions_created += 1
                if use_stripe:
                    stripe_count += 1
                else:
                    credits_count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would create approximately {len(orders)} transactions"
            ))
            self.stdout.write(f"  Expected Stripe: ~{int(len(orders) * stripe_percentage / 100)}")
            self.stdout.write(f"  Expected Credits: ~{int(len(orders) * (100 - stripe_percentage) / 100)}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully created {transactions_created} transactions!"
            ))
            self.stdout.write(f"  Stripe payments: {stripe_count}")
            self.stdout.write(f"  Credit payments: {credits_count}")
            self.stdout.write(f"  Total amount (Stripe): €{sum([t.amount for t in Transaction.objects.filter(order__in=orders, payment_method='stripe')]):,.2f}")
            self.stdout.write(f"  Total amount (Credits): €{sum([t.amount for t in Transaction.objects.filter(order__in=orders, payment_method='credits')]):,.2f}")
