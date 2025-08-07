from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CustomUser, UserRole, UserProfile, UserInvitation
from apps.companies.models import Company, Branch, Department, DepartmentMembership
from apps.attendance.models import AttendanceGroup, AttendanceGroupMembership

User = get_user_model()

# Permission decorators
def hr_required(user):
    """Check if user has HR permissions"""
    return user.is_authenticated and user.can_manage_hr

def company_manager_required(user):
    """Check if user is a company manager"""
    return user.is_authenticated and user.role in [UserRole.COMPANY_MANAGER, UserRole.SUPER_ADMIN]

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'users/profile.html', {
        'title': 'My Profile',
        'user': request.user
    })

@login_required
def settings(request):
    """User settings view"""
    return render(request, 'users/settings.html', {
        'title': 'Settings',
        'user': request.user
    })

@login_required
@user_passes_test(hr_required)
def employee_list(request):
    """List all employees in the company with search and filter capabilities"""
    user = request.user
    company = user.company
    
    if not company:
        messages.error(request, 'You must be associated with a company to view employees.')
        return redirect('dashboard:dashboard')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', 'active')
    
    # Base queryset - employees in the same company
    employees = User.objects.filter(
        company=company
    ).select_related('company', 'profile').prefetch_related(
        'departmentmembership_set__department__branch'
    )
    
    # Apply search filter
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Apply department filter
    if department_filter:
        employees = employees.filter(
            departmentmembership__department_id=department_filter
        )
    
    # Apply role filter
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    # Apply status filter
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    
    # Order by name
    employees = employees.order_by('first_name', 'last_name')
    
    # Pagination
    paginator = Paginator(employees, 20)  # 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = Department.objects.filter(
        branch__company=company
    ).select_related('branch')
    
    roles = UserRole.choices
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj,
        'departments': departments,
        'roles': roles,
        'search_query': search_query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_employees': employees.count(),
    }
    
    return render(request, 'users/employee_list.html', context)

@login_required
@user_passes_test(hr_required)
def employee_detail(request, employee_id):
    """View detailed information about an employee"""
    user = request.user
    company = user.company
    
    employee = get_object_or_404(
        User.objects.select_related('company', 'profile').prefetch_related(
            'departmentmembership_set__department__branch',
            'attendancegroupmembership_set__attendance_group'
        ),
        id=employee_id,
        company=company
    )
    
    # Get employee's department memberships
    department_memberships = employee.departmentmembership_set.filter(
        is_active=True
    ).select_related('department__branch')
    
    # Get employee's attendance groups
    attendance_memberships = employee.attendancegroupmembership_set.filter(
        is_active=True
    ).select_related('attendance_group')
    
    # Get recent attendance summary (last 30 days)
    from apps.attendance.models import AttendanceSummary
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_attendance = AttendanceSummary.objects.filter(
        employee=employee,
        date__gte=thirty_days_ago
    ).order_by('-date')[:10]
    
    context = {
        'employee': employee,
        'department_memberships': department_memberships,
        'attendance_memberships': attendance_memberships,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'users/employee_detail.html', context)

@login_required
@user_passes_test(company_manager_required)
def employee_create(request):
    """Create a new employee"""
    user = request.user
    company = user.company
    
    if not company:
        messages.error(request, 'You must be associated with a company to create employees.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role', UserRole.EMPLOYEE)
            department_id = request.POST.get('department')
            
            # Validate required fields
            if not all([username, email, first_name, last_name]):
                messages.error(request, 'All fields are required.')
                return render(request, 'users/employee_create.html', {
                    'departments': Department.objects.filter(branch__company=company),
                    'roles': UserRole.choices
                })
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'users/employee_create.html', {
                    'departments': Department.objects.filter(branch__company=company),
                    'roles': UserRole.choices
                })
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'users/employee_create.html', {
                    'departments': Department.objects.filter(branch__company=company),
                    'roles': UserRole.choices
                })
            
            # Create the user
            employee = User.objects.create_user(
                username=username,
                email=email,
                password='temp123',  # Temporary password
                first_name=first_name,
                last_name=last_name,
                role=role,
                company=company
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=employee,
                bio=f'{role.replace("_", " ").title()} at {company.name}',
                address=request.POST.get('address', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', '')
            )
            
            # Assign to department if specified
            if department_id:
                department = get_object_or_404(
                    Department,
                    id=department_id,
                    branch__company=company
                )
                DepartmentMembership.objects.create(
                    employee=employee,
                    department=department,
                    position='member'
                )
            
            messages.success(request, f'Employee {employee.get_full_name()} created successfully!')
            return redirect('users:employee_detail', employee_id=employee.id)
            
        except Exception as e:
            messages.error(request, f'Error creating employee: {str(e)}')
    
    # GET request - show form
    departments = Department.objects.filter(
        branch__company=company
    ).select_related('branch')
    
    context = {
        'departments': departments,
        'roles': UserRole.choices,
    }
    
    return render(request, 'users/employee_create.html', context)

@login_required
@user_passes_test(hr_required)
def employee_edit(request, employee_id):
    """Edit an existing employee"""
    user = request.user
    company = user.company
    
    employee = get_object_or_404(
        User.objects.select_related('profile'),
        id=employee_id,
        company=company
    )
    
    if request.method == 'POST':
        try:
            # Update basic information
            employee.first_name = request.POST.get('first_name', employee.first_name)
            employee.last_name = request.POST.get('last_name', employee.last_name)
            employee.email = request.POST.get('email', employee.email)
            
            # Only allow role changes for company managers
            if user.role == UserRole.COMPANY_MANAGER:
                employee.role = request.POST.get('role', employee.role)
            
            employee.is_active = request.POST.get('is_active') == 'on'
            employee.save()
            
            # Update profile if it exists
            if hasattr(employee, 'profile'):
                profile = employee.profile
                profile.bio = request.POST.get('bio', profile.bio)
                profile.address = request.POST.get('address', profile.address)
                profile.emergency_contact_name = request.POST.get('emergency_contact_name', profile.emergency_contact_name)
                profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', profile.emergency_contact_phone)
                profile.save()
            
            messages.success(request, f'Employee {employee.get_full_name()} updated successfully!')
            return redirect('users:employee_detail', employee_id=employee.id)
            
        except Exception as e:
            messages.error(request, f'Error updating employee: {str(e)}')
    
    # GET request - show form
    departments = Department.objects.filter(
        branch__company=company
    ).select_related('branch')
    
    current_department = None
    dept_membership = employee.departmentmembership_set.filter(is_active=True).first()
    if dept_membership:
        current_department = dept_membership.department
    
    context = {
        'employee': employee,
        'departments': departments,
        'current_department': current_department,
        'roles': UserRole.choices,
    }
    
    return render(request, 'users/employee_edit.html', context)

@login_required
@user_passes_test(company_manager_required)
@require_POST
def employee_delete(request, employee_id):
    """Deactivate an employee (soft delete)"""
    user = request.user
    company = user.company
    
    employee = get_object_or_404(
        User,
        id=employee_id,
        company=company
    )
    
    # Don't allow deleting yourself
    if employee == user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('users:employee_list')
    
    # Soft delete - deactivate the user
    employee.is_active = False
    employee.save()
    
    # Deactivate all memberships
    employee.departmentmembership_set.update(is_active=False)
    employee.attendancegroupmembership_set.update(is_active=False)
    
    messages.success(request, f'Employee {employee.get_full_name()} has been deactivated.')
    return redirect('users:employee_list')

@login_required
@user_passes_test(hr_required)
def department_management(request):
    """Manage department assignments for employees"""
    user = request.user
    company = user.company
    
    if not company:
        messages.error(request, 'You must be associated with a company.')
        return redirect('dashboard:dashboard')
    
    # Get all departments in the company
    departments = Department.objects.filter(
        branch__company=company
    ).select_related('branch').prefetch_related(
        'departmentmembership_set__employee'
    )
    
    # Get employees without department assignments
    unassigned_employees = User.objects.filter(
        company=company,
        is_active=True
    ).exclude(
        departmentmembership__is_active=True
    )
    
    context = {
        'departments': departments,
        'unassigned_employees': unassigned_employees,
    }
    
    return render(request, 'users/department_management.html', context)

@login_required
@user_passes_test(hr_required)
@require_POST
def assign_department(request):
    """Assign an employee to a department"""
    user = request.user
    company = user.company
    
    try:
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department_id')
        role = request.POST.get('role', 'member')
        
        employee = get_object_or_404(
            User,
            id=employee_id,
            company=company
        )
        
        department = get_object_or_404(
            Department,
            id=department_id,
            branch__company=company
        )
        
        # Check if already assigned
        existing = DepartmentMembership.objects.filter(
            employee=employee,
            department=department,
            is_active=True
        ).exists()
        
        if existing:
            messages.warning(request, f'{employee.get_full_name()} is already assigned to {department.name}.')
        else:
            # Create new assignment
            DepartmentMembership.objects.create(
                employee=employee,
                department=department,
                position=role
            )
            messages.success(request, f'{employee.get_full_name()} assigned to {department.name}.')
    
    except Exception as e:
        messages.error(request, f'Error assigning department: {str(e)}')
    
    return redirect('users:department_management')

@login_required
@user_passes_test(hr_required)
@require_POST
def remove_department(request):
    """Remove an employee from a department"""
    user = request.user
    company = user.company
    
    try:
        membership_id = request.POST.get('membership_id')
        
        membership = get_object_or_404(
            DepartmentMembership.objects.select_related('employee', 'department'),
            id=membership_id,
            department__branch__company=company
        )
        
        employee_name = membership.employee.get_full_name()
        department_name = membership.department.name
        
        # Deactivate membership
        membership.is_active = False
        membership.save()
        
        messages.success(request, f'{employee_name} removed from {department_name}.')
    
    except Exception as e:
        messages.error(request, f'Error removing department assignment: {str(e)}')
    
    return redirect('users:department_management')
