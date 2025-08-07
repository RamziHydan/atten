#!/usr/bin/env python
"""
Simple script to create test data for the SaaS Attendance Platform
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import UserRole, UserProfile
from apps.companies.models import Company, Branch, Department
from apps.attendance.models import AttendanceGroup, Period
from datetime import time

User = get_user_model()

def create_test_data():
    print("Creating test data for SaaS Attendance Platform...")
    
    # Create a test company owner
    if not User.objects.filter(username='testowner').exists():
        owner = User.objects.create_user(
            username='testowner',
            email='owner@testcompany.com',
            password='test123',
            first_name='Test',
            last_name='Owner',
            role=UserRole.COMPANY_MANAGER
        )
        print(f"[+] Created company owner: {owner.username}")
    else:
        owner = User.objects.get(username='testowner')
        print(f"[+] Company owner already exists: {owner.username}")
    
    # Create a test company
    if not Company.objects.filter(name='Test Company Ltd').exists():
        company = Company.objects.create(
            name='Test Company Ltd',
            description='A test company for demonstration',
            website='https://testcompany.com',
            owner=owner
        )
        owner.company = company
        owner.save()
        print(f"[+] Created company: {company.name}")
    else:
        company = Company.objects.get(name='Test Company Ltd')
        print(f"[+] Company already exists: {company.name}")
    
    # Create owner profile
    if not hasattr(owner, 'profile'):
        UserProfile.objects.create(
            user=owner,
            bio='Company Owner and Manager',
            address='123 Business Street, Tech City'
        )
        print(f"[+] Created profile for: {owner.username}")
    
    # Create a test branch
    if not Branch.objects.filter(name='Main Office', company=company).exists():
        branch = Branch.objects.create(
            name='Main Office',
            company=company,
            address='123 Business Street, Tech City',
            latitude=40.7128,  # New York coordinates for demo
            longitude=-74.0060
        )
        print(f"[+] Created branch: {branch.name}")
    else:
        branch = Branch.objects.get(name='Main Office', company=company)
        print(f"[+] Branch already exists: {branch.name}")
    
    # Create a test department
    if not Department.objects.filter(name='Engineering', branch=branch).exists():
        department = Department.objects.create(
            name='Engineering',
            branch=branch,
            description='Software Engineering Department'
        )
        print(f"[+] Created department: {department.name}")
    else:
        department = Department.objects.get(name='Engineering', branch=branch)
        print(f"[+] Department already exists: {department.name}")
    
    # Create an attendance group
    if not AttendanceGroup.objects.filter(name='Engineering Team', company=company).exists():
        attendance_group = AttendanceGroup.objects.create(
            name='Engineering Team',
            company=company,
            branch=branch,
            latitude=40.7128,
            longitude=-74.0060,
            radius=100,
            description='Main engineering team attendance group'
        )
        print(f"[+] Created attendance group: {attendance_group.name}")
    else:
        attendance_group = AttendanceGroup.objects.get(name='Engineering Team', company=company)
        print(f"[+] Attendance group already exists: {attendance_group.name}")
    
    # Create a work period
    if not Period.objects.filter(name='Standard Hours', group=attendance_group).exists():
        period = Period.objects.create(
            name='Standard Hours',
            group=attendance_group,
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0),   # 5:00 PM
            weekdays='1,2,3,4,5',   # Monday to Friday
            late_checkin_grace_minutes=15,
            early_checkout_grace_minutes=15
        )
        print(f"[+] Created work period: {period.name}")
    else:
        period = Period.objects.get(name='Standard Hours', group=attendance_group)
        print(f"[+] Work period already exists: {period.name}")
    
    # Create a test employee
    if not User.objects.filter(username='testemployee').exists():
        employee = User.objects.create_user(
            username='testemployee',
            email='employee@testcompany.com',
            password='test123',
            first_name='Test',
            last_name='Employee',
            role=UserRole.EMPLOYEE,
            company=company
        )
        
        # Create employee profile
        UserProfile.objects.create(
            user=employee,
            bio='Software Engineer',
            address='456 Employee Street, Tech City'
        )
        
        # Add employee to attendance group
        from apps.attendance.models import AttendanceGroupMembership
        AttendanceGroupMembership.objects.create(
            employee=employee,
            attendance_group=attendance_group,
            is_active=True
        )
        
        print(f"[+] Created employee: {employee.username}")
    else:
        employee = User.objects.get(username='testemployee')
        print(f"[+] Employee already exists: {employee.username}")
    
    print("\n[SUCCESS] Test data creation completed!")
    print("\n=== TEST ACCOUNTS ===")
    print("Superuser: admin / [your password]")
    print("Company Owner: testowner / test123")
    print("Employee: testemployee / test123")
    print("\n=== NEXT STEPS ===")
    print("1. Visit http://127.0.0.1:8000/login/")
    print("2. Login with any of the test accounts above")
    print("3. Explore the beautiful dashboard and check-in functionality!")

if __name__ == '__main__':
    create_test_data()
