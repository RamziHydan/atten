from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

from apps.users.models import CustomUser, UserRole, UserProfile
from apps.companies.models import Company, Branch, Department, DepartmentMembership
from apps.attendance.models import AttendanceGroup, AttendanceGroupMembership, Period, CheckIn, AttendanceSummary

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the SaaS Attendance Platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating sample data',
        )

    def handle(self, *args, **options):
        # Skip clearing for now to avoid constraint issues
        # if options['clear']:
        #     self.stdout.write('Clearing existing data...')
        #     # Complex deletion logic would go here

        self.stdout.write('Creating sample data...')
        
        # Check if sample data already exists
        if Company.objects.filter(name='TechCorp Solutions').exists():
            self.stdout.write('Sample data already exists. Skipping creation.')
            return

        # Create companies
        companies_data = [
            {
                'name': 'TechCorp Solutions',
                'description': 'Leading technology solutions provider',
                'website': 'https://techcorp.com'
            },
            {
                'name': 'Digital Innovations Ltd',
                'description': 'Digital transformation specialists',
                'website': 'https://digitalinnovations.com'
            }
        ]

        companies = []
        for company_data in companies_data:
            # Create company owner
            owner_username = f"owner_{company_data['name'].lower().replace(' ', '_')}"
            owner = User.objects.create_user(
                username=owner_username,
                email=f"{owner_username}@{company_data['name'].lower().replace(' ', '')}.com",
                password='owner123',
                first_name='Company',
                last_name='Owner',
                role=UserRole.COMPANY_MANAGER
            )

            # Create company
            company = Company.objects.create(
                name=company_data['name'],
                description=company_data['description'],
                website=company_data['website'],
                owner=owner
            )
            owner.company = company
            owner.save()

            # Create user profile for owner
            UserProfile.objects.create(
                user=owner,
                bio=f'Company Manager at {company.name}',
                date_of_birth=datetime(1980, 1, 1).date(),
                address='123 Main St, City, State',
                emergency_contact_name='Emergency Contact',
                emergency_contact_phone='+1234567890'
            )

            companies.append(company)
            self.stdout.write(f'Created company: {company.name}')

        # Create branches for each company
        for company in companies:
            branches_data = [
                {
                    'name': 'Headquarters',
                    'address': '123 Business Ave, Downtown',
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                {
                    'name': 'Branch Office',
                    'address': '456 Corporate Blvd, Uptown',
                    'latitude': 40.7589,
                    'longitude': -73.9851
                }
            ]

            for branch_data in branches_data:
                branch = Branch.objects.create(
                    name=branch_data['name'],
                    company=company,
                    address=branch_data['address'],
                    latitude=branch_data['latitude'],
                    longitude=branch_data['longitude']
                )

                # Create departments for each branch
                departments_data = [
                    'Engineering',
                    'Human Resources',
                    'Sales',
                    'Marketing'
                ]

                for dept_name in departments_data:
                    department = Department.objects.create(
                        name=dept_name,
                        branch=branch
                    )

                    # Create attendance group for each department
                    attendance_group = AttendanceGroup.objects.create(
                        name=f'{dept_name} - {branch.name}',
                        company=company,
                        branch=branch,
                        latitude=branch.latitude,
                        longitude=branch.longitude,
                        radius=100,  # 100 meters
                        description=f'Attendance group for {dept_name} department'
                    )

                    # Create periods (shifts) for attendance group
                    periods_data = [
                        {
                            'name': 'Morning Shift',
                            'start_time': time(9, 0),
                            'end_time': time(17, 0),
                            'weekdays': '1,2,3,4,5'  # Monday to Friday
                        },
                        {
                            'name': 'Flexible Hours',
                            'start_time': time(8, 0),
                            'end_time': time(18, 0),
                            'weekdays': '1,2,3,4,5'  # Monday to Friday
                        }
                    ]

                    for period_data in periods_data:
                        Period.objects.create(
                            name=period_data['name'],
                            group=attendance_group,
                            start_time=period_data['start_time'],
                            end_time=period_data['end_time'],
                            weekdays=period_data['weekdays'],
                            grace_period_minutes=15,
                            late_threshold_minutes=30
                        )

                    # Create users for each department
                    roles = [UserRole.HR_EMPLOYEE, UserRole.EMPLOYEE, UserRole.EMPLOYEE]
                    for i, role in enumerate(roles):
                        username = f"{dept_name.lower()}_{branch.name.lower().replace(' ', '_')}_{i+1}_{company.name.lower().replace(' ', '_')}"
                        user = User.objects.create_user(
                            username=username,
                            email=f"{username}@{company.name.lower().replace(' ', '')}.com",
                            password='employee123',
                            first_name=f'{dept_name}',
                            last_name=f'Employee {i+1}',
                            role=role,
                            company=company
                        )

                        # Create user profile
                        UserProfile.objects.create(
                            user=user,
                            bio=f'{role.replace("_", " ").title()} in {dept_name} department',
                            date_of_birth=datetime(1985 + i, 1, 1).date(),
                            address=f'{100 + i} Employee St, City, State',
                            emergency_contact_name=f'Emergency Contact {i+1}',
                            emergency_contact_phone=f'+123456789{i}'
                        )

                        # Add user to department
                        DepartmentMembership.objects.create(
                            user=user,
                            department=department,
                            role='member'
                        )

                        # Add user to attendance group
                        AttendanceGroupMembership.objects.create(
                            user=user,
                            group=attendance_group,
                            is_active=True
                        )

                        self.stdout.write(f'Created user: {user.username} ({user.get_role_display()})')

        # Create sample attendance data for the last 30 days
        self.stdout.write('Creating sample attendance data...')
        
        users = User.objects.filter(role__in=[UserRole.HR_EMPLOYEE, UserRole.EMPLOYEE])
        today = timezone.now().date()
        
        for user in users:
            attendance_groups = AttendanceGroup.objects.filter(
                attendancegroupmembership__user=user,
                attendancegroupmembership__is_active=True
            )
            
            if not attendance_groups.exists():
                continue
                
            attendance_group = attendance_groups.first()
            periods = attendance_group.periods.filter(is_active=True)
            
            if not periods.exists():
                continue
                
            period = periods.first()
            
            # Create attendance for last 20 working days
            for days_ago in range(20):
                date = today - timedelta(days=days_ago)
                
                # Skip weekends
                if date.weekday() >= 5:
                    continue
                
                # 90% chance of attendance
                if random.random() < 0.9:
                    # Random check-in time (with some variation)
                    base_checkin = datetime.combine(date, period.start_time)
                    checkin_variation = random.randint(-30, 60)  # -30 to +60 minutes
                    checkin_time = base_checkin + timedelta(minutes=checkin_variation)
                    
                    # Create check-in
                    checkin = CheckIn.objects.create(
                        employee=user,
                        attendance_group=attendance_group,
                        period=period,
                        timestamp=timezone.make_aware(checkin_time),
                        latitude=attendance_group.latitude + random.uniform(-0.001, 0.001),
                        longitude=attendance_group.longitude + random.uniform(-0.001, 0.001),
                        type=CheckIn.CheckInType.CHECK_IN,
                        status=CheckIn.CheckInStatus.APPROVED,
                        notes=f'Check-in for {date}'
                    )
                    
                    # 95% chance of check-out
                    if random.random() < 0.95:
                        # Random check-out time
                        base_checkout = datetime.combine(date, period.end_time)
                        checkout_variation = random.randint(-60, 120)  # -60 to +120 minutes
                        checkout_time = base_checkout + timedelta(minutes=checkout_variation)
                        
                        # Create check-out
                        checkout = CheckIn.objects.create(
                            employee=user,
                            attendance_group=attendance_group,
                            period=period,
                            timestamp=timezone.make_aware(checkout_time),
                            latitude=attendance_group.latitude + random.uniform(-0.001, 0.001),
                            longitude=attendance_group.longitude + random.uniform(-0.001, 0.001),
                            type=CheckIn.CheckInType.CHECK_OUT,
                            status=CheckIn.CheckInStatus.APPROVED,
                            notes=f'Check-out for {date}'
                        )
                        
                        # Calculate hours worked
                        hours_worked = (checkout.timestamp - checkin.timestamp).total_seconds() / 3600
                        
                        # Create attendance summary
                        AttendanceSummary.objects.create(
                            employee=user,
                            attendance_group=attendance_group,
                            date=date,
                            first_checkin=checkin,
                            last_checkout=checkout,
                            total_hours=hours_worked,
                            is_present=True,
                            is_late=checkin_time.time() > period.start_time,
                            is_early_departure=checkout_time.time() < period.end_time
                        )
                    else:
                        # No check-out, create summary with just check-in
                        AttendanceSummary.objects.create(
                            employee=user,
                            attendance_group=attendance_group,
                            date=date,
                            first_checkin=checkin,
                            total_hours=0,
                            is_present=True,
                            is_late=checkin_time.time() > period.start_time,
                            is_early_departure=False
                        )
                else:
                    # Absent day
                    AttendanceSummary.objects.create(
                        employee=user,
                        attendance_group=attendance_group,
                        date=date,
                        total_hours=0,
                        is_present=False,
                        is_late=False,
                        is_early_departure=False
                    )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        
        # Print summary
        self.stdout.write('\n=== SAMPLE DATA SUMMARY ===')
        self.stdout.write(f'Companies: {Company.objects.count()}')
        self.stdout.write(f'Branches: {Branch.objects.count()}')
        self.stdout.write(f'Departments: {Department.objects.count()}')
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Attendance Groups: {AttendanceGroup.objects.count()}')
        self.stdout.write(f'Periods: {Period.objects.count()}')
        self.stdout.write(f'Check-ins: {CheckIn.objects.count()}')
        self.stdout.write(f'Attendance Summaries: {AttendanceSummary.objects.count()}')
        
        self.stdout.write('\n=== TEST ACCOUNTS ===')
        self.stdout.write('Superuser: admin / admin (password you set)')
        self.stdout.write('Company Owners: owner_techcorp_solutions / owner123')
        self.stdout.write('                owner_digital_innovations_ltd / owner123')
        self.stdout.write('Employees: engineering_headquarters_1_techcorp_solutions / employee123')
        self.stdout.write('           hr_headquarters_1_techcorp_solutions / employee123')
        self.stdout.write('           (and many more...)')
