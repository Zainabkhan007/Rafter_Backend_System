"""
Management command to deactivate all active menu cycles
This is scheduled to run every Friday at 9 AM via cron job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from admin_section.models import Menu


class Command(BaseCommand):
    help = "Deactivate all active menu cycles for all schools (runs Friday 9 AM)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deactivated without actually deactivating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Get all active menus
        active_menus = Menu.objects.filter(is_active=True, is_deleted=False)

        count = active_menus.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No active menu cycles found."))
            return

        # Group by cycle for better logging
        cycles = {}
        for menu in active_menus:
            cycle_name = menu.cycle_name or "No Cycle Name"
            if cycle_name not in cycles:
                cycles[cycle_name] = {
                    'menus': [],
                    'primary_schools': set(),
                    'secondary_schools': set()
                }
            cycles[cycle_name]['menus'].append(menu)

            # Track schools
            for school in menu.primary_schools.all():
                cycles[cycle_name]['primary_schools'].add(school.school_name)
            for school in menu.secondary_schools.all():
                cycles[cycle_name]['secondary_schools'].add(school.secondary_school_name)

        # Count total affected schools
        total_primary_schools = sum(len(data['primary_schools']) for data in cycles.values())
        total_secondary_schools = sum(len(data['secondary_schools']) for data in cycles.values())
        total_schools = total_primary_schools + total_secondary_schools

        # Display what will be deactivated
        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        self.stdout.write(self.style.SUCCESS(f"Menu Cycle Deactivation - {timezone.now().strftime('%d %b %Y, %I:%M %p')}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}\n"))

        self.stdout.write(self.style.WARNING(f"📊 SUMMARY:"))
        self.stdout.write(f"  • Active Menu Cycles: {len(cycles)}")
        self.stdout.write(f"  • Total Menu Items: {count}")
        self.stdout.write(f"  • Affected Primary Schools: {total_primary_schools}")
        self.stdout.write(f"  • Affected Secondary Schools: {total_secondary_schools}")
        self.stdout.write(f"  • Total Affected Schools: {total_schools}")
        self.stdout.write("")

        for cycle_name, data in cycles.items():
            self.stdout.write(self.style.WARNING(f"📋 Cycle: {cycle_name}"))
            self.stdout.write(f"  - Menu items: {len(data['menus'])}")

            if data['primary_schools']:
                self.stdout.write(f"  - Primary Schools ({len(data['primary_schools'])}): {', '.join(sorted(data['primary_schools']))}")

            if data['secondary_schools']:
                self.stdout.write(f"  - Secondary Schools ({len(data['secondary_schools'])}): {', '.join(sorted(data['secondary_schools']))}")

            self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would deactivate {count} menu items across {len(cycles)} cycle(s)"
            ))
            self.stdout.write("Run without --dry-run to actually deactivate.")
        else:
            # Deactivate all active menus
            active_menus.update(is_active=False)

            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully deactivated {count} menu items across {len(cycles)} cycle(s)!"
            ))
            self.stdout.write(self.style.SUCCESS(
                "All schools now have inactive menus. Admins need to activate new cycles."
            ))

        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}\n"))
