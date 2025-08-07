from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Company, Branch, Department, DepartmentMembership
from apps.users.models import UserRole
from apps.attendance.models import AttendanceGroup

User = get_user_model()

# Permission decorators
def company_manager_required(user):
    """Check if user is a company manager or super admin"""
    return user.is_authenticated and user.role in [UserRole.COMPANY_MANAGER, UserRole.SUPER_ADMIN]

def company_owner_required(user):
    """Check if user owns the company or is super admin"""
    return user.is_authenticated and (user.role == UserRole.SUPER_ADMIN or 
                                    (hasattr(user, 'owned_company') and user.owned_company))

@login_required
def company_detail(request, company_id):
    """View company details with branches and departments"""
    user = request.user
    
    # Get the company - ensure user has access
    if user.role == UserRole.SUPER_ADMIN:
        company = get_object_or_404(Company, id=company_id)
    else:
        # Ensure user can only access their own company
        if not user.company or user.company.id != company_id:
            raise Http404("Company not found")
        company = get_object_or_404(Company, id=company_id)
    
    # Get branches with department counts
    branches = Branch.objects.filter(
        company=company
    ).prefetch_related('departments').annotate(
        department_count=Count('departments'),
        employee_count=Count('departments__departmentmembership', distinct=True)
    ).order_by('name')
    
    # Get company statistics
    total_employees = User.objects.filter(company=company, is_active=True).count()
    total_departments = Department.objects.filter(branch__company=company).count()
    total_attendance_groups = AttendanceGroup.objects.filter(company=company).count()
    
    context = {
        'company': company,
        'branches': branches,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_branches': branches.count(),
        'total_attendance_groups': total_attendance_groups,
        'can_manage': user.role in [UserRole.COMPANY_MANAGER, UserRole.SUPER_ADMIN],
    }
    
    return render(request, 'companies/company_detail.html', context)

@login_required
@user_passes_test(company_manager_required)
def branch_list(request):
    """List all branches in the company with search and filter capabilities"""
    user = request.user
    company = user.company
    
    if not company:
        messages.error(request, 'You must be associated with a company to view branches.')
        return redirect('dashboard:dashboard')
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    
    # Base queryset - branches in the same company
    branches = Branch.objects.filter(
        company=company
    ).prefetch_related('departments').annotate(
        department_count=Count('departments'),
        total_employees=Count('departments__departmentmembership', distinct=True)
    )
    
    # Apply search filter
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Order by name
    branches = branches.order_by('name')
    
    # Calculate totals for statistics
    total_departments = sum(branch.department_count for branch in branches)
    total_employees = sum(branch.total_employees for branch in branches)
    
    # Pagination
    paginator = Paginator(branches, 12)  # 12 branches per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'branches': page_obj,
        'search_query': search_query,
        'total_branches': branches.count(),
        'total_departments': total_departments,
        'total_employees': total_employees,
        'company': company,
    }
    
    return render(request, 'companies/branch_list.html', context)

@login_required
@user_passes_test(company_manager_required)
def branch_detail(request, branch_id):
    """View detailed information about a branch"""
    user = request.user
    company = user.company
    
    branch = get_object_or_404(
        Branch.objects.prefetch_related(
            'departments__departmentmembership_set__employee'
        ),
        id=branch_id,
        company=company
    )
    
    # Get departments in this branch
    departments = branch.departments.all().annotate(
        employee_count=Count('departmentmembership', distinct=True)
    ).order_by('name')
    
    # Get branch statistics
    total_departments = departments.count()
    total_employees = sum(dept.employee_count for dept in departments)
    
    # Get recent activity (employees added to departments in this branch)
    recent_memberships = DepartmentMembership.objects.filter(
        department__branch=branch,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).select_related('employee', 'department').order_by('-created_at')[:10]
    
    context = {
        'branch': branch,
        'departments': departments,
        'total_departments': total_departments,
        'total_employees': total_employees,
        'recent_memberships': recent_memberships,
    }
    
    return render(request, 'companies/branch_detail.html', context)

@login_required
@user_passes_test(company_manager_required)
def branch_create(request):
    """Create a new branch"""
    user = request.user
    company = user.company
    
    if not company:
        messages.error(request, 'You must be associated with a company to create branches.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            code = request.POST.get('code')
            address = request.POST.get('address')
            phone_number = request.POST.get('phone')
            email = request.POST.get('email')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            radius = request.POST.get('radius')
            hr_manager_id = request.POST.get('hr_manager')
            
            # Validate required fields
            if not all([name, address]):
                messages.error(request, 'Name and address are required.')
                return render(request, 'companies/branch_create.html', {
                    'company': company
                })
            
            # Generate branch code if not provided
            if not code:
                # Generate a simple code from branch name
                code = ''.join(word[:3].upper() for word in name.split()[:2])
                # Ensure uniqueness within company
                base_code = code
                counter = 1
                while Branch.objects.filter(company=company, code=code).exists():
                    code = f"{base_code}{counter}"
                    counter += 1
            
            # Validate coordinates if provided
            lat_value = None
            lng_value = None
            if latitude and longitude:
                try:
                    lat_value = float(latitude)
                    lng_value = float(longitude)
                    # Basic coordinate validation
                    if not (-90 <= lat_value <= 90):
                        messages.error(request, 'Latitude must be between -90 and 90 degrees.')
                        return render(request, 'companies/branch_create.html', {
                            'company': company
                        })
                    if not (-180 <= lng_value <= 180):
                        messages.error(request, 'Longitude must be between -180 and 180 degrees.')
                        return render(request, 'companies/branch_create.html', {
                            'company': company
                        })
                except ValueError:
                    messages.error(request, 'Invalid latitude or longitude format. Please enter valid decimal numbers.')
                    return render(request, 'companies/branch_create.html', {
                        'company': company
                    })
            
            # Validate radius if provided
            radius_value = None
            if radius:
                try:
                    radius_value = int(radius)
                    if radius_value < 10 or radius_value > 10000:
                        messages.error(request, 'Radius must be between 10 and 10,000 meters.')
                        return render(request, 'companies/branch_create.html', {
                            'company': company
                        })
                except ValueError:
                    messages.error(request, 'Invalid radius format. Please enter a valid number.')
                    return render(request, 'companies/branch_create.html', {
                        'company': company
                    })
            
            # Check if branch name already exists in this company
            if Branch.objects.filter(company=company, name=name).exists():
                messages.error(request, f'A branch named "{name}" already exists in your company.')
                return render(request, 'companies/branch_create.html', {
                    'company': company
                })
            
            # Create the branch
            branch = Branch.objects.create(
                company=company,
                name=name,
                code=code,
                address=address,
                phone_number=phone_number,
                email=email,
                latitude=lat_value,
                longitude=lng_value,
                radius=radius_value
            )
            
            # Assign HR manager if selected
            if hr_manager_id:
                from apps.users.models import CustomUser
                try:
                    hr_manager = CustomUser.objects.get(
                        id=hr_manager_id,
                        company=company,
                        role='HR_EMPLOYEE'
                    )
                    # Clear any existing branch assignment for this HR manager
                    hr_manager.managed_branch = branch
                    hr_manager.save()
                    messages.success(request, f'Branch "{branch.name}" created successfully and assigned to {hr_manager.get_full_name()}!')
                except CustomUser.DoesNotExist:
                    messages.warning(request, f'Branch "{branch.name}" created successfully, but HR manager assignment failed.')
            else:
                messages.success(request, f'Branch "{branch.name}" created successfully!')
            
            return redirect('companies:branch_detail', branch_id=branch.id)
            
        except Exception as e:
            messages.error(request, f'Error creating branch: {str(e)}')
    
    # GET request - show form
    # Get available HR managers (those without branch assignments)
    from apps.users.models import CustomUser
    available_hr_managers = CustomUser.objects.filter(
        company=company,
        role='HR_EMPLOYEE',
        managed_branch__isnull=True,
        is_active=True
    )
    
    context = {
        'company': company,
        'hr_managers': available_hr_managers,
    }
    
    return render(request, 'companies/branch_create.html', context)

@login_required
@user_passes_test(company_manager_required)
def branch_edit(request, branch_id):
    """Edit an existing branch"""
    user = request.user
    company = user.company
    
    branch = get_object_or_404(
        Branch,
        id=branch_id,
        company=company
    )
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            code = request.POST.get('code')
            address = request.POST.get('address')
            phone_number = request.POST.get('phone')
            email = request.POST.get('email')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            radius = request.POST.get('radius')
            hr_manager_id = request.POST.get('hr_manager')
            
            # Validate required fields
            if not all([name, address]):
                messages.error(request, 'Name and address are required.')
                return render(request, 'companies/branch_edit.html', {
                    'branch': branch,
                    'company': company
                })
            
            # Generate branch code if not provided
            if not code:
                # Generate a simple code from branch name
                code = ''.join(word[:3].upper() for word in name.split()[:2])
                # Ensure uniqueness within company (excluding current branch)
                base_code = code
                counter = 1
                while Branch.objects.filter(company=company, code=code).exclude(id=branch.id).exists():
                    code = f"{base_code}{counter}"
                    counter += 1
            
            # Validate coordinates if provided
            lat_value = branch.latitude
            lng_value = branch.longitude
            if latitude and longitude:
                try:
                    lat_value = float(latitude)
                    lng_value = float(longitude)
                    # Basic coordinate validation
                    if not (-90 <= lat_value <= 90):
                        messages.error(request, 'Latitude must be between -90 and 90 degrees.')
                        return render(request, 'companies/branch_edit.html', {
                            'branch': branch,
                            'company': company
                        })
                    if not (-180 <= lng_value <= 180):
                        messages.error(request, 'Longitude must be between -180 and 180 degrees.')
                        return render(request, 'companies/branch_edit.html', {
                            'branch': branch,
                            'company': company
                        })
                except ValueError:
                    messages.error(request, 'Invalid latitude or longitude format. Please enter valid decimal numbers.')
                    return render(request, 'companies/branch_edit.html', {
                        'branch': branch,
                        'company': company
                    })
            elif latitude or longitude:
                # If only one coordinate is provided, clear both
                lat_value = None
                lng_value = None
            
            # Validate radius if provided
            radius_value = branch.radius
            if radius:
                try:
                    radius_value = int(radius)
                    if radius_value < 10 or radius_value > 10000:
                        messages.error(request, 'Radius must be between 10 and 10,000 meters.')
                        return render(request, 'companies/branch_edit.html', {
                            'branch': branch,
                            'company': company
                        })
                except ValueError:
                    messages.error(request, 'Invalid radius format. Please enter a valid number.')
                    return render(request, 'companies/branch_edit.html', {
                        'branch': branch,
                        'company': company
                    })
            
            # Check for duplicate names (excluding current branch)
            if Branch.objects.filter(
                company=company, 
                name=name
            ).exclude(id=branch.id).exists():
                messages.error(request, f'A branch named "{name}" already exists in your company.')
                return render(request, 'companies/branch_edit.html', {
                    'branch': branch,
                    'company': company
                })
            
            # Update branch fields
            branch.name = name
            branch.code = code
            branch.address = address
            branch.phone_number = phone_number or ''
            branch.email = email or ''
            branch.latitude = lat_value
            branch.longitude = lng_value
            branch.radius = radius_value
            branch.save()
            
            # Handle HR manager assignment
            from apps.users.models import CustomUser
            current_hr_manager = CustomUser.objects.filter(managed_branch=branch).first()
            
            if hr_manager_id:
                try:
                    new_hr_manager = CustomUser.objects.get(
                        id=hr_manager_id,
                        company=company,
                        role='HR_EMPLOYEE'
                    )
                    # Clear any existing assignment for this HR manager
                    if current_hr_manager and current_hr_manager != new_hr_manager:
                        current_hr_manager.managed_branch = None
                        current_hr_manager.save()
                    
                    # Assign new HR manager
                    new_hr_manager.managed_branch = branch
                    new_hr_manager.save()
                    
                    messages.success(request, f'Branch "{branch.name}" updated successfully and assigned to {new_hr_manager.get_full_name()}!')
                except CustomUser.DoesNotExist:
                    messages.warning(request, f'Branch "{branch.name}" updated successfully, but HR manager assignment failed.')
            else:
                # Remove HR manager assignment if none selected
                if current_hr_manager:
                    current_hr_manager.managed_branch = None
                    current_hr_manager.save()
                messages.success(request, f'Branch "{branch.name}" updated successfully!')
            
            return redirect('companies:branch_detail', branch_id=branch.id)
            
        except Exception as e:
            messages.error(request, f'Error updating branch: {str(e)}')
    
    # GET request - show form
    # Get current HR manager for this branch
    from apps.users.models import CustomUser
    from django.db import models
    current_hr_manager = CustomUser.objects.filter(managed_branch=branch).first()
    
    # Get available HR managers (those without branch assignments, plus current one)
    available_hr_managers = CustomUser.objects.filter(
        company=company,
        role='HR_EMPLOYEE',
        is_active=True
    ).filter(
        models.Q(managed_branch__isnull=True) | models.Q(managed_branch=branch)
    )
    
    context = {
        'branch': branch,
        'company': company,
        'hr_managers': available_hr_managers,
        'current_hr_manager': current_hr_manager,
    }
    
    return render(request, 'companies/branch_edit.html', context)

@login_required
@user_passes_test(company_manager_required)
@require_POST
def branch_delete(request, branch_id):
    """Delete a branch (soft delete by deactivating departments)"""
    user = request.user
    company = user.company
    
    branch = get_object_or_404(
        Branch,
        id=branch_id,
        company=company
    )
    
    # Check if branch has departments with active employees
    active_memberships = DepartmentMembership.objects.filter(
        department__branch=branch,
        is_active=True
    ).count()
    
    if active_memberships > 0:
        messages.error(request, 
            f'Cannot delete branch "{branch.name}" because it has {active_memberships} active employee assignments. '
            'Please reassign employees to other departments first.')
        return redirect('companies:branch_detail', branch_id=branch.id)
    
    try:
        branch_name = branch.name
        
        # Deactivate all department memberships in this branch
        DepartmentMembership.objects.filter(
            department__branch=branch
        ).update(is_active=False)
        
        # Delete the branch (this will cascade to departments)
        branch.delete()
        
        messages.success(request, f'Branch "{branch_name}" has been deleted successfully.')
        return redirect('companies:branch_list')
        
    except Exception as e:
        messages.error(request, f'Error deleting branch: {str(e)}')
        return redirect('companies:branch_detail', branch_id=branch.id)

@login_required
@user_passes_test(company_manager_required)
def department_create(request, branch_id):
    """Create a new department in a branch"""
    user = request.user
    company = user.company
    
    branch = get_object_or_404(
        Branch,
        id=branch_id,
        company=company
    )
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not name:
                messages.error(request, 'Department name is required.')
                return render(request, 'companies/department_create.html', {
                    'branch': branch,
                    'company': company
                })
            
            # Check if department name already exists in this branch
            if Department.objects.filter(branch=branch, name=name).exists():
                messages.error(request, f'A department named "{name}" already exists in this branch.')
                return render(request, 'companies/department_create.html', {
                    'branch': branch,
                    'company': company
                })
            
            # Create the department
            department = Department.objects.create(
                branch=branch,
                name=name,
                description=description
            )
            
            messages.success(request, f'Department "{department.name}" created successfully!')
            return redirect('companies:branch_detail', branch_id=branch.id)
            
        except Exception as e:
            messages.error(request, f'Error creating department: {str(e)}')
    
    # GET request - show form
    context = {
        'branch': branch,
        'company': company,
    }
    
    return render(request, 'companies/department_create.html', context)
