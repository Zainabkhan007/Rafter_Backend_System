from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from admin_section.models import (
    Transaction, PrimarySchool, SecondarySchool,
    SecondaryStudent, StaffRegisteration, ParentRegisteration
)
import random
from decimal import Decimal


class Command(BaseCommand):
    help = "Add dummy credit top-up transactions for users in a school"

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
            '--num-topups',
            type=int,
            default=20,
            help='Number of top-up transactions to create (default: 20)',
        )
        parser.add_argument(
            '--date-start',
            type=str,
            help='Start date for top-ups (YYYY-MM-DD), default: 30 days ago',
        )
        parser.add_argument(
            '--date-end',
            type=str,
            help='End date for top-ups (YYYY-MM-DD), default: today',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        school_id = options['school_id']
        school_type = options['school_type']
        num_topups = options['num_topups']
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

        # Parse dates
        utc = pytz.UTC
        if options.get('date_end'):
            end_date = datetime.strptime(options['date_end'], '%Y-%m-%d')
        else:
            end_date = datetime.now()

        if options.get('date_start'):
            start_date = datetime.strptime(options['date_start'], '%Y-%m-%d')
        else:
            start_date = end_date - timedelta(days=30)

        # Ensure timezone aware
        if start_date.tzinfo is None:
            start_date = utc.localize(start_date)
        if end_date.tzinfo is None:
            end_date = utc.localize(end_date)

        self.stdout.write(f"\nProcessing: {school_name} ({school_type})")
        self.stdout.write(f"Date range: {start_date.date()} to {end_date.date()}")
        self.stdout.write(f"Number of top-ups: {num_topups}")

        # Get users for this school
        if school_type == 'primary':
            parents = list(ParentRegisteration.objects.filter(primary_school=school))
            staff = list(StaffRegisteration.objects.filter(primary_school=school))
            all_users = [{'obj': p, 'type': 'parent'} for p in parents] + \
                       [{'obj': s, 'type': 'staff'} for s in staff]
        else:
            students = list(SecondaryStudent.objects.filter(school=school))
            staff = list(StaffRegisteration.objects.filter(secondary_school=school))
            all_users = [{'obj': s, 'type': 'student'} for s in students] + \
                       [{'obj': s, 'type': 'staff'} for s in staff]

        if not all_users:
            self.stdout.write(self.style.WARNING("No users found for this school!"))
            return

        self.stdout.write(f"Found {len(all_users)} users")

        # Top-up amounts (common amounts people add)
        topup_amounts = [10, 20, 25, 30, 40, 50, 75, 100, 150, 200]

        transactions_created = 0
        total_amount = Decimal('0.00')

        for i in range(num_topups):
            # Select random user
            user_data = random.choice(all_users)
            user = user_data['obj']
            user_type = user_data['type']

            # Random top-up amount
            amount = Decimal(str(random.choice(topup_amounts)))

            # Random date within range
            time_diff = (end_date - start_date).total_seconds()
            random_seconds = random.randint(0, int(time_diff))
            transaction_time = start_date + timedelta(seconds=random_seconds)

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would create credit top-up: €{amount} for "
                    f"{user.first_name} {user.last_name} ({user_type}) on {transaction_time.date()}"
                )
            else:
                # Create credit top-up transaction
                transaction = Transaction.objects.create(
                    user_id=user.id,
                    user_type=user_type,
                    transaction_type='credit',
                    payment_method='stripe',  # Credits are topped up via Stripe
                    amount=amount,
                    order=None,  # No order for credit top-ups
                    payment_intent_id=f"pi_topup_{random.randint(100000, 999999)}",
                    description=f"Credit top-up - €{amount}",
                    created_at=transaction_time,
                    parent=user if user_type == 'parent' else None,
                    staff=user if user_type == 'staff' else None,
                    student=user if user_type == 'student' else None,
                )

                transactions_created += 1
                total_amount += amount

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would create {num_topups} credit top-up transactions"
            ))
            avg_amount = sum(topup_amounts) / len(topup_amounts)
            self.stdout.write(f"  Expected total: ~€{avg_amount * num_topups:,.2f}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully created {transactions_created} credit top-up transactions!"
            ))
            self.stdout.write(f"  Total amount: €{total_amount:,.2f}")
            self.stdout.write(f"  Average top-up: €{total_amount / transactions_created:,.2f}")
