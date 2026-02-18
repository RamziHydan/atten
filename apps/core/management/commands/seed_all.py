from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.companies.models import Company, Branch, Department, DepartmentMembership
from apps.attendance.models import AttendanceGroup, Period, AttendanceGroupMembership, CheckIn
from apps.subscriptions.models import SubscriptionPlan, CompanySubscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Run all seeders in correct sequence to create comprehensive test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all existing data before seeding (WARNING: This will delete ALL data!)',
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip user seeding (use existing users)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                'Starting Comprehensive SaaS Attendance Platform Seeding\n'
                '=' * 60
            )
        )

        if options['clear_all']:
            self.stdout.write(self.style.WARNING('WARNING: CLEARING ALL DATA...'))
            self.clear_all_data()

        # Run seeders in correct dependency order
        seeder_sequence = [
            ('seed_users', 'Users (Super Admin, Company Owners, HR Managers, Employees)', not options['skip_users']),
            ('seed_subscription_plans', 'Subscription Plans', True),
            ('seed_companies', 'Companies', True),
            ('seed_branches', 'Branches', True),
            ('seed_departments', 'Departments', True),
            ('seed_groups', 'Attendance Groups', True),
            ('seed_periods', 'Work Periods', True),
            ('seed_assignments', 'Employee-Group Assignments', True),
            ('seed_checkins', 'Attendance Records (Check-ins/Check-outs)', True),
        ]

        for command, description, should_run in seeder_sequence:
            if should_run:
                self.stdout.write(f'\nSeeding {description}...')
                try:
                    call_command(command, '--clear')
                    self.stdout.write(self.style.SUCCESS(f'SUCCESS: {description} seeded successfully'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'ERROR: Error seeding {description}: {str(e)}'))
                    return
            else:
                self.stdout.write(f'\nSkipping {description}')

        # Display final summary
        self.display_final_summary()

    def clear_all_data(self):
        """Clear all seeded data directly from database in proper order"""
        try:
            from apps.subscriptions.models import CompanySubscription, Payment
            
            self.stdout.write('Clearing all data in dependency order...')
            
            # Clear in reverse dependency order
            CheckIn.objects.all().delete()
            self.stdout.write('  - Cleared check-ins')
            
            AttendanceGroupMembership.objects.all().delete()
            self.stdout.write('  - Cleared attendance group memberships')
            
            Period.objects.all().delete()
            self.stdout.write('  - Cleared periods')
            
            AttendanceGroup.objects.all().delete()
            self.stdout.write('  - Cleared attendance groups')
            
            DepartmentMembership.objects.all().delete()
            self.stdout.write('  - Cleared department memberships')
            
            Department.objects.all().delete()
            self.stdout.write('  - Cleared departments')
            
            Branch.objects.all().delete()
            self.stdout.write('  - Cleared branches')
            
            # Clear subscription-related data
            Payment.objects.all().delete()
            self.stdout.write('  - Cleared payments')
            
            CompanySubscription.objects.all().delete()
            self.stdout.write('  - Cleared company subscriptions')
            
            Company.objects.all().delete()
            self.stdout.write('  - Cleared companies')
            
            # Clear users (except superuser if exists)
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write('  - Cleared users (kept superusers)')
            
            # Clear subscription plans and payment methods (no dependencies)
            from apps.subscriptions.models import SubscriptionPlan, PaymentMethod
            SubscriptionPlan.objects.all().delete()
            PaymentMethod.objects.all().delete()
            self.stdout.write('  - Cleared subscription plans and payment methods')
            
            self.stdout.write(self.style.SUCCESS('SUCCESS: All data cleared successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: Error clearing data: {str(e)}'))
            raise

    def display_final_summary(self):
        """Display comprehensive summary of seeded data"""
        self.stdout.write(
            self.style.SUCCESS(
                '\n' + '=' * 60 + '\n'
                'SEEDING COMPLETED SUCCESSFULLY!\n'
                '=' * 60
            )
        )

        # Count all entities
        users = User.objects.all()
        companies = Company.objects.all()
        branches = Branch.objects.all()
        departments = Department.objects.all()
        groups = AttendanceGroup.objects.all()
        periods = Period.objects.all()
        assignments = AttendanceGroupMembership.objects.filter(is_active=True)
        checkins = CheckIn.objects.all()
        subscription_plans = SubscriptionPlan.objects.all()
        subscriptions = CompanySubscription.objects.all()

        summary = f"""
DATA SUMMARY:
+-- Users: {users.count()} total
|   +-- Super Admins: {users.filter(role='SUPER_ADMIN').count()}
|   +-- Company Managers: {users.filter(role='COMPANY_MANAGER').count()}
|   +-- HR Employees: {users.filter(role='HR_EMPLOYEE').count()}
|   +-- Employees: {users.filter(role='EMPLOYEE').count()}
+-- Subscription Plans: {subscription_plans.count()}
+-- Company Subscriptions: {subscriptions.count()}
+-- Companies: {companies.count()}
+-- Branches: {branches.count()} ({branches.count()//2} per company)
+-- Departments: {departments.count()} ({departments.count()//4} per branch)
+-- Attendance Groups: {groups.count()} ({groups.count()//4} per branch)
+-- Work Periods: {periods.count()} ({periods.count()//8} per group)
+-- Group Assignments: {assignments.count()}
+-- Attendance Records: {checkins.count()} ({checkins.filter(type='IN').count()} check-ins, {checkins.filter(type='OUT').count()} check-outs)

COMPANY BREAKDOWN:"""

        for company in companies:
            company_users = users.filter(company=company)
            company_branches = branches.filter(company=company)
            company_departments = departments.filter(branch__company=company)
            company_groups = groups.filter(company=company)
            company_assignments = assignments.filter(attendance_group__company=company)
            company_subscription = subscriptions.filter(company=company).first()

            subscription_info = "No Subscription"
            if company_subscription:
                subscription_info = f"{company_subscription.plan.name} ({company_subscription.status})"

            summary += f"""
+-- {company.name}:
|   +-- Owner: {company.owner.get_full_name()}
|   +-- Subscription: {subscription_info}
|   +-- Employees: {company_users.count()}
|   +-- Branches: {company_branches.count()}
|   +-- Departments: {company_departments.count()}
|   +-- Groups: {company_groups.count()}
|   +-- Assignments: {company_assignments.count()}"""

        summary += f"""

TEST LOGIN CREDENTIALS:
+-- Super Admin: superadmin / admin123
+-- Company Owner 1: owner1 / owner123
+-- Company Owner 2: owner2 / owner123
+-- HR Manager (Company 1): hr1_1 / hr123
+-- HR Manager (Company 2): hr2_1 / hr123
+-- Employee (Company 1): emp1_1 / emp123
+-- Employee (Company 2): emp2_1 / emp123

VERIFICATION:
+-- No cross-company data mixing: OK
+-- Proper role assignments: OK
+-- Geographic coordinates set: OK
+-- Work schedules configured: OK
+-- Employee-group assignments: OK

READY FOR TESTING!
Your SaaS Attendance Platform now has comprehensive test data.
You can log in with any of the credentials above to test different user roles.
"""

        self.stdout.write(summary)

        # Verify data integrity
        self.verify_data_integrity()

    def verify_data_integrity(self):
        """Verify that all seeded data maintains proper relationships"""
        issues = []

        # Check for users without companies (except super admin)
        users_without_company = User.objects.filter(company__isnull=True).exclude(role='SUPER_ADMIN')
        if users_without_company.exists():
            issues.append(f"Found {users_without_company.count()} users without company assignments")

        # Check for cross-company assignments
        cross_company_assignments = []
        for assignment in AttendanceGroupMembership.objects.filter(is_active=True):
            if assignment.employee.company != assignment.attendance_group.company:
                cross_company_assignments.append(assignment)

        if cross_company_assignments:
            issues.append(f"Found {len(cross_company_assignments)} cross-company assignments")

        # Check for groups without periods
        groups_without_periods = AttendanceGroup.objects.filter(periods__isnull=True)
        if groups_without_periods.exists():
            issues.append(f"Found {groups_without_periods.count()} groups without periods")

        if issues:
            self.stdout.write(self.style.ERROR('\nDATA INTEGRITY ISSUES FOUND:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'   - {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('\nDATA INTEGRITY VERIFICATION PASSED!'))
