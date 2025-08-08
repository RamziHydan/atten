from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.companies.models import Company, Branch, Department, DepartmentMembership
from apps.attendance.models import AttendanceGroup, AttendanceGroupMembership
from faker import Faker
import random

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed assignments: Link employees to attendance groups (2 employees per group)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing attendance group memberships before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing attendance group memberships...'))
            AttendanceGroupMembership.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing attendance group memberships cleared.'))

        # Check if we have the required data
        companies = Company.objects.all().order_by('id')
        groups = AttendanceGroup.objects.all().order_by('company_id', 'branch_id', 'id')
        employees = User.objects.filter(role='EMPLOYEE').order_by('company_id', 'id')
        hr_managers = User.objects.filter(role='HR_EMPLOYEE').order_by('company_id', 'id')

        if companies.count() < 2:
            self.stdout.write(self.style.ERROR('Not enough companies found. Please run all previous seeders first.'))
            return

        if groups.count() < 8:
            self.stdout.write(self.style.ERROR('Not enough attendance groups found. Please run seed_groups first.'))
            return

        if employees.count() < 16:
            self.stdout.write(self.style.ERROR('Not enough employees found. Please run seed_users first.'))
            return

        with transaction.atomic():
            assignments = self.create_assignments(companies, groups, employees, hr_managers)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(assignments)} attendance group assignments:\n' +
                '\n'.join([f'  - {assignment.employee.get_full_name()} -> {assignment.attendance_group.name}' 
                          for assignment in assignments[:10]]) +  # Show first 10
                (f'\n  ... and {len(assignments) - 10} more assignments' if len(assignments) > 10 else '')
            )
        )

    def create_assignments(self, companies, groups, employees, hr_managers):
        """Create attendance group assignments ensuring no cross-company mixing"""
        assignments = []
        
        # Group employees by company to ensure no cross-company assignments
        employees_by_company = {}
        hr_managers_by_company = {}
        
        for employee in employees:
            company_id = employee.company.id if employee.company else None
            if company_id:
                if company_id not in employees_by_company:
                    employees_by_company[company_id] = []
                employees_by_company[company_id].append(employee)
        
        for hr_manager in hr_managers:
            company_id = hr_manager.company.id if hr_manager.company else None
            if company_id:
                if company_id not in hr_managers_by_company:
                    hr_managers_by_company[company_id] = []
                hr_managers_by_company[company_id].append(hr_manager)
        
        # Process each company separately
        for company in companies:
            company_groups = groups.filter(company=company).order_by('branch_id', 'id')
            company_employees = employees_by_company.get(company.id, [])
            company_hr_managers = hr_managers_by_company.get(company.id, [])
            
            self.stdout.write(f'\nProcessing {company.name}:')
            self.stdout.write(f'  - Groups: {company_groups.count()}')
            self.stdout.write(f'  - Employees: {len(company_employees)}')
            self.stdout.write(f'  - HR Managers: {len(company_hr_managers)}')
            
            # Assign employees to groups within this company
            employee_idx = 0
            hr_manager_idx = 0
            
            for group in company_groups:
                # Assign 2 employees to each group
                group_assignments = []
                
                for i in range(2):
                    if employee_idx < len(company_employees):
                        employee = company_employees[employee_idx]
                        
                        # Create attendance group membership
                        assignment = AttendanceGroupMembership.objects.create(
                            employee=employee,
                            attendance_group=group,
                            is_active=True
                        )
                        
                        assignments.append(assignment)
                        group_assignments.append(assignment)
                        employee_idx += 1
                        
                        self.stdout.write(
                            f'    Assigned {employee.get_full_name()} to {group.name}'
                        )
                
                # Also assign the HR manager for this branch to the group
                if hr_manager_idx < len(company_hr_managers):
                    hr_manager = company_hr_managers[hr_manager_idx % len(company_hr_managers)]
                    
                    # Check if HR manager is already assigned to this group
                    existing_assignment = AttendanceGroupMembership.objects.filter(
                        employee=hr_manager,
                        attendance_group=group,
                        is_active=True
                    ).first()
                    
                    if not existing_assignment:
                        assignment = AttendanceGroupMembership.objects.create(
                            employee=hr_manager,
                            attendance_group=group,
                            is_active=True
                        )
                        
                        assignments.append(assignment)
                        self.stdout.write(
                            f'    Assigned HR Manager {hr_manager.get_full_name()} to {group.name}'
                        )
                
                # Rotate HR managers for variety
                if len(company_hr_managers) > 0:
                    hr_manager_idx += 1
        
        return assignments

    def get_assignment_summary(self):
        """Display summary of created assignments"""
        assignments = AttendanceGroupMembership.objects.filter(is_active=True)
        
        summary = {
            'total_assignments': assignments.count(),
            'assignments_by_company': {}
        }
        
        for company in Company.objects.all():
            company_assignments = assignments.filter(attendance_group__company=company)
            
            summary['assignments_by_company'][company.name] = {
                'total': company_assignments.count(),
                'by_group': {}
            }
            
            for group in company.attendance_groups.all():
                group_assignments = company_assignments.filter(attendance_group=group)
                summary['assignments_by_company'][company.name]['by_group'][group.name] = [
                    {
                        'employee': assignment.employee.get_full_name(),
                        'role': assignment.employee.get_role_display(),
                        'assigned_at': assignment.assigned_at.strftime('%Y-%m-%d %H:%M')
                    }
                    for assignment in group_assignments
                ]
        
        return summary

    def verify_no_cross_company_assignments(self):
        """Verify that no employee is assigned to groups outside their company"""
        violations = []
        
        for assignment in AttendanceGroupMembership.objects.filter(is_active=True):
            employee_company = assignment.employee.company
            group_company = assignment.attendance_group.company
            
            if employee_company != group_company:
                violations.append({
                    'employee': assignment.employee.get_full_name(),
                    'employee_company': employee_company.name if employee_company else 'None',
                    'group': assignment.attendance_group.name,
                    'group_company': group_company.name
                })
        
        if violations:
            self.stdout.write(
                self.style.ERROR(
                    f'Found {len(violations)} cross-company assignment violations!'
                )
            )
            for violation in violations:
                self.stdout.write(
                    self.style.ERROR(
                        f'  - {violation["employee"]} ({violation["employee_company"]}) '
                        f'assigned to {violation["group"]} ({violation["group_company"]})'
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ No cross-company assignment violations found!')
            )
        
        return len(violations) == 0
