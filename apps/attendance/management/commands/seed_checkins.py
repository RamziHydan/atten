from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, time
from decimal import Decimal
import random
from faker import Faker

from apps.attendance.models import CheckIn, AttendanceGroup, Period, AttendanceGroupMembership

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generate realistic check-in and check-out records for all employees over a month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing check-in records before seeding',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate attendance data for (default: 30)',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: 30 days ago)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing check-in records...')
            CheckIn.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing check-in records cleared.'))

        # Determine date range
        days = options['days']
        if options['start_date']:
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid start date format. Use YYYY-MM-DD'))
                return
        else:
            start_date = (timezone.now() - timedelta(days=days)).date()

        end_date = start_date + timedelta(days=days)

        self.stdout.write(f'Generating attendance data from {start_date} to {end_date}')

        # Get all active employee-group assignments
        assignments = AttendanceGroupMembership.objects.filter(is_active=True)
        
        if not assignments.exists():
            self.stdout.write(self.style.ERROR('No active employee-group assignments found. Run seed_assignments first.'))
            return

        total_checkins = 0
        companies_processed = set()

        # Process each assignment
        for assignment in assignments:
            employee = assignment.employee
            group = assignment.attendance_group
            company = group.company
            
            if company not in companies_processed:
                companies_processed.add(company)
                self.stdout.write(f'\nProcessing {company.name}:')

            # Get periods for this group
            periods = group.periods.filter(is_active=True)
            if not periods.exists():
                self.stdout.write(f'  Skipping {employee.get_full_name()} - no active periods in {group.name}')
                continue

            # Generate attendance for each day
            employee_checkins = 0
            current_date = start_date

            while current_date < end_date:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue

                # Determine if employee works today (90% attendance rate)
                if random.random() > 0.9:  # 10% chance of absence
                    current_date += timedelta(days=1)
                    continue

                # Select a random period for today
                period = random.choice(periods)
                
                # Check if this period is active on this weekday
                weekday_num = current_date.weekday() + 1  # Monday=1, Sunday=7
                if str(weekday_num) not in period.weekdays:
                    current_date += timedelta(days=1)
                    continue

                # Generate check-in and check-out for this day
                checkins_today = self.generate_daily_attendance(
                    employee, group, period, current_date
                )
                employee_checkins += checkins_today
                total_checkins += checkins_today

                current_date += timedelta(days=1)

            self.stdout.write(f'  Generated {employee_checkins} check-ins for {employee.get_full_name()}')

        # Display summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated {total_checkins} check-in records:\n'
                f'  - Date range: {start_date} to {end_date}\n'
                f'  - Companies processed: {len(companies_processed)}\n'
                f'  - Employee assignments: {assignments.count()}\n'
                f'  - Average check-ins per employee: {total_checkins / assignments.count():.1f}'
            )
        )

    def generate_daily_attendance(self, employee, group, period, date):
        """Generate check-in and check-out records for a single day"""
        checkins_created = 0
        
        # Generate realistic arrival time (with some variation)
        base_checkin_time = period.start_time
        
        # Add random variation: -15 to +30 minutes
        variation_minutes = random.randint(-15, 30)
        checkin_datetime = datetime.combine(date, base_checkin_time) + timedelta(minutes=variation_minutes)
        checkin_datetime = timezone.make_aware(checkin_datetime)

        # Determine check-in status
        if variation_minutes > period.late_checkin_grace_minutes:
            checkin_status = CheckIn.CheckInStatus.LATE
        elif variation_minutes < -5:  # Early by more than 5 minutes
            checkin_status = CheckIn.CheckInStatus.EARLY
        else:
            checkin_status = CheckIn.CheckInStatus.ON_TIME

        # Generate location near the group location (within radius)
        checkin_lat, checkin_lon = self.generate_location_near_group(group)

        # Create check-in record
        checkin = CheckIn.objects.create(
            employee=employee,
            attendance_group=group,
            period=period,
            timestamp=checkin_datetime,
            latitude=checkin_lat,
            longitude=checkin_lon,
            type=CheckIn.CheckInType.CHECK_IN,
            status=checkin_status,
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            notes=self.generate_checkin_notes(checkin_status)
        )
        checkins_created += 1

        # Generate check-out (80% of the time - sometimes people forget)
        if random.random() <= 0.8:
            # Generate realistic departure time
            base_checkout_time = period.end_time
            checkout_variation = random.randint(-30, 60)  # -30 to +60 minutes
            checkout_datetime = datetime.combine(date, base_checkout_time) + timedelta(minutes=checkout_variation)
            checkout_datetime = timezone.make_aware(checkout_datetime)

            # Determine checkout status
            if checkout_variation < -period.early_checkout_grace_minutes:
                checkout_status = CheckIn.CheckInStatus.EARLY
            elif checkout_variation > 60:  # Very late checkout
                checkout_status = CheckIn.CheckInStatus.LATE
            else:
                checkout_status = CheckIn.CheckInStatus.ON_TIME

            # Generate location (might be slightly different from check-in)
            checkout_lat, checkout_lon = self.generate_location_near_group(group)

            # Create check-out record
            checkout = CheckIn.objects.create(
                employee=employee,
                attendance_group=group,
                period=period,
                timestamp=checkout_datetime,
                latitude=checkout_lat,
                longitude=checkout_lon,
                type=CheckIn.CheckInType.CHECK_OUT,
                status=checkout_status,
                ip_address=fake.ipv4(),
                user_agent=fake.user_agent(),
                notes=self.generate_checkout_notes(checkout_status)
            )
            checkins_created += 1

        return checkins_created

    def generate_location_near_group(self, group):
        """Generate a random location within the group's radius"""
        # Get group location
        group_lat = float(group.latitude)
        group_lon = float(group.longitude)
        radius_meters = group.radius

        # Generate random offset within radius
        # Using simple approximation: 1 degree ≈ 111,000 meters
        max_lat_offset = (radius_meters * 0.8) / 111000  # Stay within 80% of radius
        max_lon_offset = (radius_meters * 0.8) / (111000 * abs(group_lat) / 90)

        lat_offset = random.uniform(-max_lat_offset, max_lat_offset)
        lon_offset = random.uniform(-max_lon_offset, max_lon_offset)

        new_lat = Decimal(str(group_lat + lat_offset)).quantize(Decimal('0.000001'))
        new_lon = Decimal(str(group_lon + lon_offset)).quantize(Decimal('0.000001'))

        return new_lat, new_lon

    def generate_checkin_notes(self, status):
        """Generate realistic notes for check-in based on status"""
        if status == CheckIn.CheckInStatus.LATE:
            return random.choice([
                'Traffic was heavy this morning',
                'Had to drop kids at school',
                'Public transport delay',
                'Car trouble',
                'Overslept - sorry!',
                ''  # Sometimes no excuse
            ])
        elif status == CheckIn.CheckInStatus.EARLY:
            return random.choice([
                'Arrived early to finish project',
                'Beat the traffic today',
                'Early meeting scheduled',
                'Couldn\'t sleep, might as well work',
                ''
            ])
        else:
            return random.choice([
                'Good morning!',
                'Ready for a productive day',
                'Looking forward to today\'s tasks',
                '',  # Most check-ins have no notes
                '',
                ''
            ])

    def generate_checkout_notes(self, status):
        """Generate realistic notes for check-out based on status"""
        if status == CheckIn.CheckInStatus.EARLY:
            return random.choice([
                'Finished all tasks for today',
                'Doctor appointment',
                'Family emergency',
                'Feeling unwell',
                'Flexible hours arrangement',
                ''
            ])
        elif status == CheckIn.CheckInStatus.LATE:
            return random.choice([
                'Working on urgent deadline',
                'Helping colleague with project',
                'System maintenance required',
                'Client call ran over',
                'Finishing important presentation',
                ''
            ])
        else:
            return random.choice([
                'Great day at work!',
                'All tasks completed',
                'See you tomorrow',
                'Have a good evening',
                '',
                '',
                ''
            ])
