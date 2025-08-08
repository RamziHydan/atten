from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
import random

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed users: 1 Super Admin, 2 Company Owners, 8 HR Managers, 16 Employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing users...'))
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing users cleared.'))

        with transaction.atomic():
            # Create Super Admin
            super_admin = self.create_super_admin()
            
            # Create Company Owners (2)
            company_owners = self.create_company_owners()
            
            # Create HR Managers (8 total: 4 per company, 2 per branch, 1 per department)
            hr_managers = self.create_hr_managers()
            
            # Create Employees (16 total: 8 per company, 4 per branch, 2 per department)
            employees = self.create_employees()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'  - 1 Super Admin\n'
                f'  - {len(company_owners)} Company Owners\n'
                f'  - {len(hr_managers)} HR Managers\n'
                f'  - {len(employees)} Employees\n'
                f'  - Total: {1 + len(company_owners) + len(hr_managers) + len(employees)} users'
            )
        )

    def create_super_admin(self):
        """Create the Super Admin user"""
        super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@attendancehub.com',
            password='admin123',
            first_name='Super',
            last_name='Admin',
            role='SUPER_ADMIN',
            is_staff=True,
            is_superuser=True
        )
        self.stdout.write(f'Created Super Admin: {super_admin.username}')
        return super_admin

    def create_company_owners(self):
        """Create 2 Company Owners"""
        owners = []
        company_names = ['TechCorp Solutions', 'InnovateLab Inc']
        
        for i, company_name in enumerate(company_names, 1):
            owner = User.objects.create_user(
                username=f'owner{i}',
                email=f'owner{i}@{company_name.lower().replace(" ", "").replace("solutions", "").replace("inc", "")}.com',
                password='owner123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='COMPANY_MANAGER'
            )
            owners.append(owner)
            self.stdout.write(f'Created Company Owner {i}: {owner.username} ({owner.get_full_name()})')
        
        return owners

    def create_hr_managers(self):
        """Create 8 HR Managers (4 per company, 2 per branch, 1 per department)"""
        hr_managers = []
        
        # Company 1: 4 HR Managers
        for i in range(1, 5):
            hr_manager = User.objects.create_user(
                username=f'hr1_{i}',
                email=f'hr{i}@techcorp.com',
                password='hr123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='HR_EMPLOYEE'
            )
            hr_managers.append(hr_manager)
            self.stdout.write(f'Created HR Manager (Company 1): {hr_manager.username} ({hr_manager.get_full_name()})')
        
        # Company 2: 4 HR Managers
        for i in range(1, 5):
            hr_manager = User.objects.create_user(
                username=f'hr2_{i}',
                email=f'hr{i}@innovatelab.com',
                password='hr123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='HR_EMPLOYEE'
            )
            hr_managers.append(hr_manager)
            self.stdout.write(f'Created HR Manager (Company 2): {hr_manager.username} ({hr_manager.get_full_name()})')
        
        return hr_managers

    def create_employees(self):
        """Create 16 Employees (8 per company, 4 per branch, 2 per department)"""
        employees = []
        
        # Company 1: 8 Employees
        for i in range(1, 9):
            employee = User.objects.create_user(
                username=f'emp1_{i}',
                email=f'employee{i}@techcorp.com',
                password='emp123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='EMPLOYEE'
            )
            employees.append(employee)
            self.stdout.write(f'Created Employee (Company 1): {employee.username} ({employee.get_full_name()})')
        
        # Company 2: 8 Employees
        for i in range(1, 9):
            employee = User.objects.create_user(
                username=f'emp2_{i}',
                email=f'employee{i}@innovatelab.com',
                password='emp123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='EMPLOYEE'
            )
            employees.append(employee)
            self.stdout.write(f'Created Employee (Company 2): {employee.username} ({employee.get_full_name()})')
        
        return employees

    def get_user_summary(self):
        """Display summary of created users"""
        return {
            'super_admin': User.objects.filter(role='SUPER_ADMIN').count(),
            'company_managers': User.objects.filter(role='COMPANY_MANAGER').count(),
            'hr_employees': User.objects.filter(role='HR_EMPLOYEE').count(),
            'employees': User.objects.filter(role='EMPLOYEE').count(),
        }
