"""
Management command to show the status of all menu cycles
Useful for debugging and understanding what menus are active/inactive
"""
from django.core.management.base import BaseCommand
from admin_section.models import Menu


class Command(BaseCommand):
    help = "Show status of all menu cycles (active and inactive)"

    def handle(self, *args, **options):
        # Get all menus (active and inactive)
        all_menus = Menu.objects.filter(is_deleted=False)

        # Group by cycle and status
        cycles = {}
        for menu in all_menus:
            cycle_name = menu.cycle_name or "No Cycle Name"
            status = "ACTIVE" if menu.is_active else "INACTIVE"

            key = f"{cycle_name}|{status}"

            if key not in cycles:
                cycles[key] = {
                    'cycle_name': cycle_name,
                    'status': status,
                    'menus': [],
                    'primary_schools': set(),
                    'secondary_schools': set()
                }

            cycles[key]['menus'].append(menu)

            # Track schools
            for school in menu.primary_schools.all():
                cycles[key]['primary_schools'].add(school.school_name)
            for school in menu.secondary_schools.all():
                cycles[key]['secondary_schools'].add(school.secondary_school_name)

        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS(f"Menu Cycles Status Report"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))

        # Separate active and inactive
        active_cycles = {k: v for k, v in cycles.items() if v['status'] == 'ACTIVE'}
        inactive_cycles = {k: v for k, v in cycles.items() if v['status'] == 'INACTIVE'}

        # Show active cycles
        if active_cycles:
            self.stdout.write(self.style.SUCCESS("ACTIVE MENU CYCLES:"))
            self.stdout.write(self.style.SUCCESS("-" * 80))

            for key, data in active_cycles.items():
                self.stdout.write(self.style.WARNING(f"\n✓ {data['cycle_name']}"))
                self.stdout.write(f"  Status: {self.style.SUCCESS('ACTIVE')}")
                self.stdout.write(f"  Menu Items: {len(data['menus'])}")

                if data['primary_schools']:
                    self.stdout.write(f"  Primary Schools ({len(data['primary_schools'])}):")
                    for school in sorted(data['primary_schools']):
                        self.stdout.write(f"    - {school}")

                if data['secondary_schools']:
                    self.stdout.write(f"  Secondary Schools ({len(data['secondary_schools'])}):")
                    for school in sorted(data['secondary_schools']):
                        self.stdout.write(f"    - {school}")

                if not data['primary_schools'] and not data['secondary_schools']:
                    self.stdout.write(self.style.ERROR(f"  ⚠ No schools associated!"))
        else:
            self.stdout.write(self.style.WARNING("\nNo active menu cycles found."))

        # Show inactive cycles
        if inactive_cycles:
            self.stdout.write(self.style.WARNING(f"\n\nINACTIVE MENU CYCLES:"))
            self.stdout.write("-" * 80)

            for key, data in inactive_cycles.items():
                self.stdout.write(f"\n✗ {data['cycle_name']}")
                self.stdout.write(f"  Status: {self.style.ERROR('INACTIVE')}")
                self.stdout.write(f"  Menu Items: {len(data['menus'])}")

                if data['primary_schools']:
                    self.stdout.write(f"  Primary Schools ({len(data['primary_schools'])}):")
                    for school in sorted(data['primary_schools']):
                        self.stdout.write(f"    - {school}")

                if data['secondary_schools']:
                    self.stdout.write(f"  Secondary Schools ({len(data['secondary_schools'])}):")
                    for school in sorted(data['secondary_schools']):
                        self.stdout.write(f"    - {school}")

        # Summary
        total_active = sum(len(data['menus']) for data in active_cycles.values())
        total_inactive = sum(len(data['menus']) for data in inactive_cycles.values())

        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS("SUMMARY:"))
        self.stdout.write(f"  Active Cycles: {len(active_cycles)}")
        self.stdout.write(f"  Active Menu Items: {total_active}")
        self.stdout.write(f"  Inactive Cycles: {len(inactive_cycles)}")
        self.stdout.write(f"  Inactive Menu Items: {total_inactive}")
        self.stdout.write(f"  Total Menu Items: {total_active + total_inactive}")
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
