from django.core.management.base import BaseCommand
from django.db import transaction
from apps.attendance.models import AttendanceGroup, Period
from faker import Faker
from datetime import time

fake = Faker()

class Command(BaseCommand):
    help = 'Seed periods: 2 periods per attendance group (16 total periods)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing periods before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing periods...'))
            Period.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing periods cleared.'))

        # Check if we have the required attendance groups
        groups = AttendanceGroup.objects.all().order_by('company_id', 'branch_id', 'id')
        if groups.count() < 8:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough attendance groups found. Please run seed_groups first.'
                )
            )
            return

        with transaction.atomic():
            periods = self.create_periods(groups)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(periods)} periods:\n' +
                '\n'.join([f'  - {period.name} ({period.group.name} - {period.start_time} to {period.end_time})' 
                          for period in periods])
            )
        )

    def create_periods(self, groups):
        """Create 2 periods per attendance group (16 total periods)"""
        periods = []
        
        # Period templates - different shifts for different types of groups
        period_templates = [
            # Standard office periods
            {
                'morning': {
                    'name': 'Morning Shift',
                    'start_time': time(8, 0),
                    'end_time': time(17, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 15,
                    'early_checkout_grace_minutes': 15
                },
                'flexible': {
                    'name': 'Flexible Hours',
                    'start_time': time(9, 0),
                    'end_time': time(18, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 30,
                    'early_checkout_grace_minutes': 30
                }
            },
            # Executive/Management periods
            {
                'executive': {
                    'name': 'Executive Hours',
                    'start_time': time(9, 0),
                    'end_time': time(18, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 10,
                    'early_checkout_grace_minutes': 10
                },
                'meetings': {
                    'name': 'Meeting Schedule',
                    'start_time': time(10, 0),
                    'end_time': time(16, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 5,
                    'early_checkout_grace_minutes': 5
                }
            },
            # Lab/Research periods
            {
                'day_shift': {
                    'name': 'Day Shift',
                    'start_time': time(7, 0),
                    'end_time': time(15, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 10,
                    'early_checkout_grace_minutes': 10
                },
                'evening_shift': {
                    'name': 'Evening Shift',
                    'start_time': time(15, 0),
                    'end_time': time(23, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 15,
                    'early_checkout_grace_minutes': 15
                }
            },
            # Testing/QA periods
            {
                'testing_hours': {
                    'name': 'Testing Hours',
                    'start_time': time(8, 30),
                    'end_time': time(17, 30),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 20,
                    'early_checkout_grace_minutes': 20
                },
                'maintenance': {
                    'name': 'Maintenance Window',
                    'start_time': time(6, 0),
                    'end_time': time(8, 0),
                    'weekdays': '1,2,3,4,5',  # Monday to Friday
                    'late_checkin_grace_minutes': 5,
                    'early_checkout_grace_minutes': 5
                }
            }
        ]
        
        # Assign period templates to groups based on their characteristics
        group_period_mapping = {
            # Office-type groups get standard periods
            'Main Office Floor 1': 0,
            'Open Workspace': 0,
            'Conference Center': 1,
            'Executive Floor': 1,
            # Lab-type groups get lab periods
            'Development Lab A': 2,
            'Research Lab': 2,
            'Testing Facility': 3,
            'Clean Room': 3,
        }
        
        for group in groups:
            # Determine which period template to use
            template_idx = group_period_mapping.get(group.name, 0)
            period_template = period_templates[template_idx]
            
            # Create both periods for this group
            for period_key, period_data in period_template.items():
                period = Period.objects.create(
                    name=period_data['name'],
                    group=group,
                    start_time=period_data['start_time'],
                    end_time=period_data['end_time'],
                    weekdays=period_data['weekdays'],
                    late_checkin_grace_minutes=period_data['late_checkin_grace_minutes'],
                    early_checkout_grace_minutes=period_data['early_checkout_grace_minutes']
                )
                
                periods.append(period)
                self.stdout.write(
                    f'Created Period: {period.name} for {group.name} '
                    f'({period.start_time} - {period.end_time}, {self.get_weekday_names(period.weekdays)})'
                )
        
        return periods

    def get_weekday_names(self, weekdays_str):
        """Convert weekdays string to readable format"""
        weekday_map = {
            '1': 'Mon', '2': 'Tue', '3': 'Wed', 
            '4': 'Thu', '5': 'Fri', '6': 'Sat', '7': 'Sun'
        }
        days = [weekday_map.get(day, day) for day in weekdays_str.split(',')]
        return '-'.join(days)

    def get_period_summary(self):
        """Display summary of created periods"""
        periods = Period.objects.all()
        return {
            'total_periods': periods.count(),
            'periods_by_group': {
                group.name: [
                    {
                        'name': period.name,
                        'schedule': f"{period.start_time} - {period.end_time}",
                        'weekdays': self.get_weekday_names(period.weekdays),
                        'grace_minutes': f"Late: {period.late_checkin_grace_minutes}min, Early: {period.early_checkout_grace_minutes}min"
                    }
                    for period in group.periods.all()
                ]
                for group in AttendanceGroup.objects.all()
            }
        }
