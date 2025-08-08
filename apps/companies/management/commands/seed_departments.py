from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.companies.models import Company, Branch, Department, DepartmentMembership
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed departments: 2 departments per branch (8 total departments) with HR managers and employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing departments before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing departments and memberships...'))
            DepartmentMembership.objects.all().delete()
            Department.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing departments and memberships cleared.'))

        # Check if we have the required branches
        branches = Branch.objects.all().order_by('company_id', 'id')
        if branches.count() < 4:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough branches found. Please run seed_branches first.'
                )
            )
            return

        # Check if we have the required HR managers and employees
        hr_managers = User.objects.filter(role='HR_EMPLOYEE').order_by('id')
        employees = User.objects.filter(role='EMPLOYEE').order_by('id')
        
        if hr_managers.count() < 8:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough HR managers found. Please run seed_users first.'
                )
            )
            return

        if employees.count() < 16:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough employees found. Please run seed_users first.'
                )
            )
            return

        with transaction.atomic():
            departments = self.create_departments(branches, hr_managers, employees)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(departments)} departments:\n' +
                '\n'.join([f'  - {dept.name} ({dept.branch.company.name} - {dept.branch.name})' 
                          for dept in departments])
            )
        )

    def create_departments(self, branches, hr_managers, employees):
        """Create 2 departments per branch (8 total departments)"""
        departments = []
        
        # Department templates for each branch
        department_templates = [
            # TechCorp Headquarters departments
            ['Engineering', 'Marketing'],
            # TechCorp R&D Center departments  
            ['Research', 'Quality Assurance'],
            # InnovateLab Main Office departments
            ['Operations', 'Sales'],
            # InnovateLab Lab Facility departments
            ['Laboratory', 'Product Development']
        ]
        
        hr_manager_idx = 0
        employee_idx = 0
        
        for branch_idx, branch in enumerate(branches):
            branch_departments = department_templates[branch_idx]
            
            for dept_name in branch_departments:
                # Create department
                department = Department.objects.create(
                    name=dept_name,
                    branch=branch,
                    code=f"{branch.code}-{dept_name[:3].upper()}",
                    description=f"{dept_name} department for {branch.name}"
                )
                
                # Assign HR manager to this department
                hr_manager = hr_managers[hr_manager_idx]
                hr_manager.managed_branch = branch  # Set the managed branch
                hr_manager.company = branch.company  # Set the company
                hr_manager.save()
                
                # Create HR manager membership
                DepartmentMembership.objects.create(
                    employee=hr_manager,
                    department=department,
                    position='HR Manager',
                    is_active=True
                )
                
                # Assign 2 employees to this department
                for i in range(2):
                    employee = employees[employee_idx]
                    employee.company = branch.company  # Set the company
                    employee.save()
                    
                    # Create employee membership
                    DepartmentMembership.objects.create(
                        employee=employee,
                        department=department,
                        position=f'{dept_name} Specialist',
                        is_active=True
                    )
                    
                    employee_idx += 1
                
                departments.append(department)
                self.stdout.write(
                    f'Created Department: {department.name} ({branch.company.name} - {branch.name}) '
                    f'with HR Manager: {hr_manager.get_full_name()} and 2 employees'
                )
                
                hr_manager_idx += 1
        
        return departments

    def get_department_summary(self):
        """Display summary of created departments"""
        departments = Department.objects.all()
        return {
            'total_departments': departments.count(),
            'departments_by_company': {
                company.name: {
                    branch.name: [
                        {
                            'name': dept.name,
                            'code': dept.code,
                            'hr_manager': dept.departmentmembership_set.filter(position='HR Manager').first().employee.get_full_name(),
                            'employee_count': dept.departmentmembership_set.filter(position__contains='Specialist').count()
                        }
                        for dept in branch.departments.all()
                    ]
                    for branch in company.branches.all()
                }
                for company in Company.objects.all()
            }
        }
