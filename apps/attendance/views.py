from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Q, Count
from django.db import models
from datetime import datetime, timedelta
import json

from .models import AttendanceGroup, CheckIn, AttendanceSummary, Period, AttendanceGroupMembership
from apps.users.models import CustomUser
from apps.companies.models import Branch


def get_accessible_employees(user):
    """
    Get employees that the user has permission to manage based on their role.
    """
    if user.role == 'SUPER_ADMIN':
        # Super admin can access all employees
        return CustomUser.objects.filter(is_active=True)
    elif user.role == 'COMPANY_MANAGER':
        # Company manager can access all employees in their company
        return CustomUser.objects.filter(
            company=user.company,
            is_active=True
        )
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        # HR employee can only access employees in their managed branch
        from apps.companies.models import DepartmentMembership
        # Get employees in departments within the HR manager's branch
        return CustomUser.objects.filter(
            departmentmembership__department__branch=user.managed_branch,
            departmentmembership__is_active=True,
            is_active=True
        ).distinct()
    else:
        # Regular employees or users without proper permissions
        return CustomUser.objects.none()


@login_required
def check_in(request):
    """
    Check-in view with location validation.
    """
    user = request.user
    
    # Get user's attendance groups
    attendance_groups = AttendanceGroup.objects.filter(
        employees=user,
        is_active=True
    ).select_related('company', 'branch')
    
    if request.method == 'POST':
        try:
            attendance_group_id = request.POST.get('attendance_group')
            latitude = float(request.POST.get('latitude', 0))
            longitude = float(request.POST.get('longitude', 0))
            notes = request.POST.get('notes', '')
            
            # Get the attendance group
            attendance_group = get_object_or_404(
                AttendanceGroup, 
                id=attendance_group_id, 
                employees=user,
                is_active=True
            )
            
            # Check if user is within radius
            if not attendance_group.is_within_radius(latitude, longitude):
                return JsonResponse({
                    'success': False,
                    'error': 'You are not within the valid check-in area.'
                })
            
            # Check if user already checked in today
            today = timezone.now().date()
            existing_checkin = CheckIn.objects.filter(
                employee=user,
                attendance_group=attendance_group,
                timestamp__date=today,
                type=CheckIn.CheckInType.CHECK_IN
            ).first()
            
            if existing_checkin:
                return JsonResponse({
                    'success': False,
                    'error': 'You have already checked in today.'
                })
            
            # Find applicable period
            current_time = timezone.now().time()
            applicable_period = None
            
            for period in attendance_group.periods.filter(is_active=True):
                if period.is_applicable_today() and period.is_within_checkin_time():
                    applicable_period = period
                    break
            
            # Create check-in record
            checkin = CheckIn.objects.create(
                employee=user,
                attendance_group=attendance_group,
                period=applicable_period,
                latitude=latitude,
                longitude=longitude,
                type=CheckIn.CheckInType.CHECK_IN,
                notes=notes,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Successfully checked in at {checkin.timestamp.strftime("%H:%M")}')
            
            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Check-in failed: {str(e)}'
            })
    
    context = {
        'attendance_groups': attendance_groups,
    }
    
    return render(request, 'attendance/check_in.html', context)


@login_required
def check_out(request):
    """
    Check-out view.
    """
    user = request.user
    today = timezone.now().date()
    
    # Find today's check-in without check-out
    open_checkins = CheckIn.objects.filter(
        employee=user,
        timestamp__date=today,
        type=CheckIn.CheckInType.CHECK_IN
    ).select_related('attendance_group')
    
    # Filter out those that already have check-out
    available_checkins = []
    for checkin in open_checkins:
        checkout_exists = CheckIn.objects.filter(
            employee=user,
            attendance_group=checkin.attendance_group,
            timestamp__date=today,
            type=CheckIn.CheckInType.CHECK_OUT,
            timestamp__gt=checkin.timestamp
        ).exists()
        
        if not checkout_exists:
            available_checkins.append(checkin)
    
    if request.method == 'POST':
        try:
            checkin_id = request.POST.get('checkin_id')
            latitude = float(request.POST.get('latitude', 0))
            longitude = float(request.POST.get('longitude', 0))
            notes = request.POST.get('notes', '')
            
            # Get the original check-in
            original_checkin = get_object_or_404(
                CheckIn,
                id=checkin_id,
                employee=user,
                type=CheckIn.CheckInType.CHECK_IN
            )
            
            # Create check-out record
            checkout = CheckIn.objects.create(
                employee=user,
                attendance_group=original_checkin.attendance_group,
                period=original_checkin.period,
                latitude=latitude,
                longitude=longitude,
                type=CheckIn.CheckInType.CHECK_OUT,
                notes=notes,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Successfully checked out at {checkout.timestamp.strftime("%H:%M")}')
            
            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Check-out failed: {str(e)}'
            })
    
    context = {
        'available_checkins': available_checkins,
    }
    
    return render(request, 'attendance/check_out.html', context)


@login_required
def history(request):
    """
    Attendance history view.
    """
    user = request.user
    
    # Get date range from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days
    if not start_date:
        start_date = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().date().strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = timezone.now().date() - timedelta(days=30)
        end_date_obj = timezone.now().date()
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # Get check-ins for the date range
    checkins = CheckIn.objects.filter(
        employee=user,
        timestamp__date__gte=start_date_obj,
        timestamp__date__lte=end_date_obj
    ).select_related('attendance_group', 'period').order_by('-timestamp')
    
    # Get attendance summaries
    summaries = AttendanceSummary.objects.filter(
        employee=user,
        date__gte=start_date_obj,
        date__lte=end_date_obj
    ).select_related('attendance_group', 'first_checkin', 'last_checkout').order_by('-date')
    
    context = {
        'checkins': checkins,
        'summaries': summaries,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance/history.html', context)


@login_required
def check_in_list(request):
    """
    List view for HR to see all check-ins (requires HR permissions).
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get all check-ins for the user's company with filtering options
    checkins_queryset = CheckIn.objects.filter(
        attendance_group__company=request.user.company
    ).select_related(
        'employee', 'attendance_group', 'period'
    ).order_by('-timestamp')
    
    # Add filtering options
    employee_filter = request.GET.get('employee')
    type_filter = request.GET.get('type')
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    
    if employee_filter:
        checkins_queryset = checkins_queryset.filter(
            employee__username__icontains=employee_filter
        )
    
    if type_filter:
        checkins_queryset = checkins_queryset.filter(type=type_filter)
    
    if status_filter:
        checkins_queryset = checkins_queryset.filter(status=status_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            checkins_queryset = checkins_queryset.filter(timestamp__date=filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Pagination
    paginator = Paginator(checkins_queryset, 25)  # Show 25 check-ins per page
    page = request.GET.get('page')
    
    try:
        checkins = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        checkins = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        checkins = paginator.page(paginator.num_pages)
    
    # Get filter options for the template
    employees = get_accessible_employees(request.user).filter(
        checkins__attendance_group__company=request.user.company
    ).distinct().order_by('first_name', 'last_name')
    
    context = {
        'checkins': checkins,
        'employees': employees,
        'type_choices': CheckIn.CheckInType.choices,
        'status_choices': CheckIn.CheckInStatus.choices,
        'current_filters': {
            'employee': employee_filter,
            'type': type_filter,
            'status': status_filter,
            'date': date_filter,
        }
    }
    
    return render(request, 'attendance/checkin_list.html', context)


@login_required
def reports(request):
    """
    Reports view for HR (requires HR permissions).
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    # This will be implemented with more detailed reporting
    context = {
        'title': 'Attendance Reports',
    }
    
    return render(request, 'attendance/reports.html', context)


# ==========================================
# ATTENDANCE GROUP MANAGEMENT
# ==========================================

@login_required
def group_list(request):
    """List all attendance groups for the user's company"""
    user = request.user
    
    # Check permissions
    if not user.can_manage_hr:
        messages.error(request, 'You do not have permission to view attendance groups.')
        return redirect('dashboard:dashboard')
    
    # Get attendance groups based on user role
    if user.role == 'SUPER_ADMIN':
        groups = AttendanceGroup.objects.all()
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        # HR managers see groups for their branch only
        groups = AttendanceGroup.objects.filter(branch=user.managed_branch)
    else:
        # Company managers see all groups for their company
        groups = AttendanceGroup.objects.filter(company=user.company)
    
    groups = groups.select_related('company', 'branch').prefetch_related(
        'periods', 'employees'
    ).annotate(
        period_count=models.Count('periods', distinct=True),
        employee_count=models.Count('employees', distinct=True)
    ).order_by('company__name', 'name')
    
    context = {
        'groups': groups,
        'can_create': user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
                     (user.role == 'HR_EMPLOYEE' and user.managed_branch),
    }
    
    return render(request, 'attendance/group_list.html', context)


@login_required
def group_detail(request, group_id):
    """View attendance group details"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        group = get_object_or_404(AttendanceGroup, id=group_id, branch=user.managed_branch)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Get periods for this group
    periods = group.periods.filter(is_active=True).order_by('start_time')
    
    # Get assigned employees through membership
    employee_memberships = AttendanceGroupMembership.objects.filter(
        attendance_group=group,
        is_active=True
    ).select_related('employee')
    employees = [membership.employee for membership in employee_memberships]
    
    # Get recent check-ins (last 10)
    recent_checkins = CheckIn.objects.filter(
        attendance_group=group
    ).select_related('employee', 'period').order_by('-timestamp')[:10]
    
    context = {
        'group': group,
        'periods': periods,
        'employees': employees,
        'recent_checkins': recent_checkins,
        'can_edit': user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
                   (user.role == 'HR_EMPLOYEE' and user.managed_branch == group.branch),
    }
    
    return render(request, 'attendance/group_detail.html', context)


@login_required
def group_create(request):
    """Create a new attendance group"""
    user = request.user
    
    # Check permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
           (user.role == 'HR_EMPLOYEE' and user.managed_branch)):
        messages.error(request, 'You do not have permission to create attendance groups.')
        return redirect('attendance:group_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            branch_id = request.POST.get('branch')
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()
            radius = request.POST.get('radius', '').strip()
            
            # Validate required fields
            if not all([name, branch_id, latitude, longitude, radius]):
                messages.error(request, 'All required fields must be filled.')
                return render(request, 'attendance/group_create.html', {
                    'branches': get_user_branches(user)
                })
            
            # Validate coordinates and radius
            try:
                lat_val = float(latitude)
                lng_val = float(longitude)
                radius_val = int(radius)
                
                if not (-90 <= lat_val <= 90) or not (-180 <= lng_val <= 180):
                    raise ValueError("Invalid coordinates")
                if not (10 <= radius_val <= 5000):
                    raise ValueError("Radius must be between 10 and 5000 meters")
            except ValueError as e:
                messages.error(request, f'Invalid input: {str(e)}')
                return render(request, 'attendance/group_create.html', {
                    'branches': get_user_branches(user)
                })
            
            # Get branch and validate access
            branch = get_object_or_404(
                Branch, 
                id=branch_id, 
                company=user.company if user.role != 'SUPER_ADMIN' else None
            )
            
            # Additional validation: ensure HR managers can only select their assigned branch
            if user.role == 'HR_EMPLOYEE' and user.managed_branch:
                if branch.id != user.managed_branch.id:
                    messages.error(request, 'You can only create attendance groups in your assigned branch.')
                    return render(request, 'attendance/group_create.html', {
                        'branches': get_user_branches(user)
                    })
            
            # Check if group name already exists in this company
            if AttendanceGroup.objects.filter(
                company=branch.company, name=name
            ).exists():
                messages.error(request, f'An attendance group named "{name}" already exists in this company.')
                return render(request, 'attendance/group_create.html', {
                    'branches': get_user_branches(user)
                })
            
            # Create the attendance group
            group = AttendanceGroup.objects.create(
                name=name,
                description=description,
                company=branch.company,
                branch=branch,
                latitude=lat_val,
                longitude=lng_val,
                radius=radius_val
            )
            
            messages.success(request, f'Attendance group "{group.name}" created successfully!')
            return redirect('attendance:group_detail', group_id=group.id)
            
        except Exception as e:
            messages.error(request, f'Error creating attendance group: {str(e)}')
    
    # GET request - show form
    context = {
        'branches': get_user_branches(user),
    }
    
    return render(request, 'attendance/group_create.html', context)


@login_required
def group_edit(request, group_id):
    """Edit an attendance group"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        group = get_object_or_404(AttendanceGroup, id=group_id, branch=user.managed_branch)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Check edit permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
           (user.role == 'HR_EMPLOYEE' and user.managed_branch == group.branch)):
        messages.error(request, 'You do not have permission to edit this attendance group.')
        return redirect('attendance:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            branch_id = request.POST.get('branch')
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()
            radius = request.POST.get('radius', '').strip()
            
            # Validate required fields
            if not all([name, branch_id, latitude, longitude, radius]):
                messages.error(request, 'All required fields must be filled.')
                return render(request, 'attendance/group_edit.html', {
                    'group': group,
                    'branches': get_user_branches(user)
                })
            
            # Validate coordinates and radius
            try:
                lat_val = float(latitude)
                lng_val = float(longitude)
                radius_val = int(radius)
                
                if not (-90 <= lat_val <= 90) or not (-180 <= lng_val <= 180):
                    raise ValueError("Invalid coordinates")
                if not (10 <= radius_val <= 5000):
                    raise ValueError("Radius must be between 10 and 5000 meters")
            except ValueError as e:
                messages.error(request, f'Invalid input: {str(e)}')
                return render(request, 'attendance/group_edit.html', {
                    'group': group,
                    'branches': get_user_branches(user)
                })
            
            # Get branch and validate access
            branch = get_object_or_404(
                Branch, 
                id=branch_id, 
                company=user.company if user.role != 'SUPER_ADMIN' else None
            )
            
            # Additional validation: ensure HR managers can only select their assigned branch
            if user.role == 'HR_EMPLOYEE' and user.managed_branch:
                if branch.id != user.managed_branch.id:
                    messages.error(request, 'You can only edit attendance groups in your assigned branch.')
                    return render(request, 'attendance/group_edit.html', {
                        'group': group,
                        'branches': get_user_branches(user)
                    })
            
            # Check if group name already exists (excluding current group)
            if AttendanceGroup.objects.filter(
                company=branch.company, name=name
            ).exclude(id=group.id).exists():
                messages.error(request, f'An attendance group named "{name}" already exists in this company.')
                return render(request, 'attendance/group_edit.html', {
                    'group': group,
                    'branches': get_user_branches(user)
                })
            
            # Update the attendance group
            group.name = name
            group.description = description
            group.branch = branch
            group.company = branch.company
            group.latitude = lat_val
            group.longitude = lng_val
            group.radius = radius_val
            group.save()
            
            messages.success(request, f'Attendance group "{group.name}" updated successfully!')
            return redirect('attendance:group_detail', group_id=group.id)
            
        except Exception as e:
            messages.error(request, f'Error updating attendance group: {str(e)}')
    
    # GET request - show form
    context = {
        'group': group,
        'branches': get_user_branches(user),
    }
    
    return render(request, 'attendance/group_edit.html', context)


@login_required
@require_POST
def group_delete(request, group_id):
    """Delete an attendance group (soft delete by deactivating)"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Check delete permissions
    if user.role not in ['COMPANY_MANAGER', 'SUPER_ADMIN']:
        messages.error(request, 'You do not have permission to delete attendance groups.')
        return redirect('attendance:group_detail', group_id=group.id)
    
    # Check if group has active check-ins
    active_checkins = CheckIn.objects.filter(
        attendance_group=group,
        timestamp__date=timezone.now().date()
    ).count()
    
    if active_checkins > 0:
        messages.error(request, 
            f'Cannot delete attendance group "{group.name}" because it has {active_checkins} active check-ins today. '
            'Please wait until all employees have checked out.')
        return redirect('attendance:group_detail', group_id=group.id)
    
    try:
        group_name = group.name
        
        # Soft delete by deactivating
        group.is_active = False
        group.save()
        
        # Also deactivate all periods
        group.periods.update(is_active=False)
        
        messages.success(request, f'Attendance group "{group_name}" has been deactivated successfully.')
        return redirect('attendance:group_list')
        
    except Exception as e:
        messages.error(request, f'Error deleting attendance group: {str(e)}')
        return redirect('attendance:group_detail', group_id=group.id)


# Helper function to get branches based on user role
def get_user_branches(user):
    """Get branches accessible to the user based on their role"""
    from apps.companies.models import Branch
    
    if user.role == 'SUPER_ADMIN':
        return Branch.objects.filter(is_active=True).select_related('company')
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        return Branch.objects.filter(id=user.managed_branch.id)
    else:
        return Branch.objects.filter(
            company=user.company, is_active=True
        ).select_related('company')


# ==========================================
# PERIOD MANAGEMENT
# ==========================================

@login_required
def period_create(request, group_id):
    """Create a new period for an attendance group"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        group = get_object_or_404(AttendanceGroup, id=group_id, branch=user.managed_branch)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Check permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
           (user.role == 'HR_EMPLOYEE' and user.managed_branch == group.branch)):
        messages.error(request, 'You do not have permission to create periods for this group.')
        return redirect('attendance:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            start_time = request.POST.get('start_time', '').strip()
            end_time = request.POST.get('end_time', '').strip()
            weekdays = request.POST.getlist('weekdays')
            late_checkin_grace = request.POST.get('late_checkin_grace_minutes', '15')
            early_checkout_grace = request.POST.get('early_checkout_grace_minutes', '15')
            
            # Validate required fields
            if not all([name, start_time, end_time]) or not weekdays:
                messages.error(request, 'All required fields must be filled.')
                return render(request, 'attendance/period_create.html', {
                    'group': group
                })
            
            # Validate time format and logic
            try:
                from datetime import datetime
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                if start_time_obj >= end_time_obj:
                    messages.error(request, 'End time must be after start time.')
                    return render(request, 'attendance/period_create.html', {
                        'group': group
                    })
            except ValueError:
                messages.error(request, 'Invalid time format. Use HH:MM format.')
                return render(request, 'attendance/period_create.html', {
                    'group': group
                })
            
            # Validate grace periods
            try:
                late_grace = int(late_checkin_grace)
                early_grace = int(early_checkout_grace)
                if late_grace < 0 or late_grace > 120 or early_grace < 0 or early_grace > 120:
                    raise ValueError("Grace periods must be between 0 and 120 minutes")
            except ValueError as e:
                messages.error(request, f'Invalid grace period: {str(e)}')
                return render(request, 'attendance/period_create.html', {
                    'group': group
                })
            
            # Validate weekdays
            valid_weekdays = ['1', '2', '3', '4', '5', '6', '7']
            if not all(day in valid_weekdays for day in weekdays):
                messages.error(request, 'Invalid weekday selection.')
                return render(request, 'attendance/period_create.html', {
                    'group': group
                })
            
            # Check if period name already exists in this group
            if Period.objects.filter(group=group, name=name).exists():
                messages.error(request, f'A period named "{name}" already exists in this group.')
                return render(request, 'attendance/period_create.html', {
                    'group': group
                })
            
            # Create the period
            period = Period.objects.create(
                name=name,
                group=group,
                start_time=start_time_obj,
                end_time=end_time_obj,
                weekdays=','.join(sorted(weekdays)),
                late_checkin_grace_minutes=late_grace,
                early_checkout_grace_minutes=early_grace
            )
            
            messages.success(request, f'Period "{period.name}" created successfully!')
            return redirect('attendance:group_detail', group_id=group.id)
            
        except Exception as e:
            messages.error(request, f'Error creating period: {str(e)}')
    
    # GET request - show form
    context = {
        'group': group,
    }
    
    return render(request, 'attendance/period_create.html', context)


@login_required
def period_edit(request, period_id):
    """Edit a period"""
    user = request.user
    
    # Get the period with access control
    if user.role == 'SUPER_ADMIN':
        period = get_object_or_404(Period, id=period_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        period = get_object_or_404(Period, id=period_id, group__branch=user.managed_branch)
    else:
        period = get_object_or_404(Period, id=period_id, group__company=user.company)
    
    # Check edit permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
           (user.role == 'HR_EMPLOYEE' and user.managed_branch == period.group.branch)):
        messages.error(request, 'You do not have permission to edit this period.')
        return redirect('attendance:group_detail', group_id=period.group.id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            start_time = request.POST.get('start_time', '').strip()
            end_time = request.POST.get('end_time', '').strip()
            weekdays = request.POST.getlist('weekdays')
            late_checkin_grace = request.POST.get('late_checkin_grace_minutes', '15')
            early_checkout_grace = request.POST.get('early_checkout_grace_minutes', '15')
            
            # Validate required fields
            if not all([name, start_time, end_time]) or not weekdays:
                messages.error(request, 'All required fields must be filled.')
                return render(request, 'attendance/period_edit.html', {
                    'period': period
                })
            
            # Validate time format and logic
            try:
                from datetime import datetime
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                if start_time_obj >= end_time_obj:
                    messages.error(request, 'End time must be after start time.')
                    return render(request, 'attendance/period_edit.html', {
                        'period': period
                    })
            except ValueError:
                messages.error(request, 'Invalid time format. Use HH:MM format.')
                return render(request, 'attendance/period_edit.html', {
                    'period': period
                })
            
            # Validate grace periods
            try:
                late_grace = int(late_checkin_grace)
                early_grace = int(early_checkout_grace)
                if late_grace < 0 or late_grace > 120 or early_grace < 0 or early_grace > 120:
                    raise ValueError("Grace periods must be between 0 and 120 minutes")
            except ValueError as e:
                messages.error(request, f'Invalid grace period: {str(e)}')
                return render(request, 'attendance/period_edit.html', {
                    'period': period
                })
            
            # Validate weekdays
            valid_weekdays = ['1', '2', '3', '4', '5', '6', '7']
            if not all(day in valid_weekdays for day in weekdays):
                messages.error(request, 'Invalid weekday selection.')
                return render(request, 'attendance/period_edit.html', {
                    'period': period
                })
            
            # Check if period name already exists (excluding current period)
            if Period.objects.filter(
                group=period.group, name=name
            ).exclude(id=period.id).exists():
                messages.error(request, f'A period named "{name}" already exists in this group.')
                return render(request, 'attendance/period_edit.html', {
                    'period': period
                })
            
            # Update the period
            period.name = name
            period.start_time = start_time_obj
            period.end_time = end_time_obj
            period.weekdays = ','.join(sorted(weekdays))
            period.late_checkin_grace_minutes = late_grace
            period.early_checkout_grace_minutes = early_grace
            period.save()
            
            messages.success(request, f'Period "{period.name}" updated successfully!')
            return redirect('attendance:group_detail', group_id=period.group.id)
            
        except Exception as e:
            messages.error(request, f'Error updating period: {str(e)}')
    
    # GET request - show form
    weekday_choices = [
        (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'),
        (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')
    ]
    
    context = {
        'period': period,
        'weekday_choices': weekday_choices,
    }
    
    return render(request, 'attendance/period_edit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def group_manage_employees(request, group_id):
    """Manage employees assigned to an attendance group"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        group = get_object_or_404(AttendanceGroup, id=group_id, branch=user.managed_branch)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Check permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
            (user.role == 'HR_EMPLOYEE' and user.managed_branch == group.branch)):
        messages.error(request, "You don't have permission to manage employees for this group.")
        return redirect('attendance:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        employee_ids = request.POST.getlist('employee_ids')
        
        if action == 'assign':
            # Assign selected employees to the group
            assigned_count = 0
            for employee_id in employee_ids:
                try:
                    employee = get_accessible_employees(user).get(id=employee_id)
                    membership, created = AttendanceGroupMembership.objects.get_or_create(
                        employee=employee,
                        attendance_group=group,
                        defaults={'is_active': True}
                    )
                    if created or not membership.is_active:
                        membership.is_active = True
                        membership.removed_at = None
                        membership.save()
                        assigned_count += 1
                except CustomUser.DoesNotExist:
                    continue
            
            if assigned_count > 0:
                messages.success(request, f"Successfully assigned {assigned_count} employee(s) to {group.name}.")
            else:
                messages.info(request, "No new employees were assigned.")
        
        elif action == 'remove':
            # Remove selected employees from the group
            removed_count = 0
            for employee_id in employee_ids:
                try:
                    membership = AttendanceGroupMembership.objects.get(
                        employee_id=employee_id,
                        attendance_group=group,
                        is_active=True
                    )
                    membership.deactivate()
                    removed_count += 1
                except AttendanceGroupMembership.DoesNotExist:
                    continue
            
            if removed_count > 0:
                messages.success(request, f"Successfully removed {removed_count} employee(s) from {group.name}.")
            else:
                messages.info(request, "No employees were removed.")
        
        return redirect('attendance:group_detail', group_id=group.id)
    
    # GET request - show the management interface
    # Get currently assigned employees
    current_memberships = AttendanceGroupMembership.objects.filter(
        attendance_group=group,
        is_active=True
    ).select_related('employee')
    assigned_employees = [membership.employee for membership in current_memberships]
    assigned_employee_ids = [emp.id for emp in assigned_employees]
    
    # Get available employees (not currently assigned)
    available_employees = get_accessible_employees(user).exclude(
        id__in=assigned_employee_ids
    ).filter(is_active=True)
    
    context = {
        'group': group,
        'assigned_employees': assigned_employees,
        'available_employees': available_employees,
    }
    
    return render(request, 'attendance/group_manage_employees.html', context)


@login_required
@require_http_methods(["POST"])
def group_remove_employee(request, group_id, employee_id):
    """Remove a single employee from an attendance group"""
    user = request.user
    
    # Get the group with access control
    if user.role == 'SUPER_ADMIN':
        group = get_object_or_404(AttendanceGroup, id=group_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        group = get_object_or_404(AttendanceGroup, id=group_id, branch=user.managed_branch)
    else:
        group = get_object_or_404(AttendanceGroup, id=group_id, company=user.company)
    
    # Check permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
            (user.role == 'HR_EMPLOYEE' and user.managed_branch == group.branch)):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        membership = AttendanceGroupMembership.objects.get(
            employee_id=employee_id,
            attendance_group=group,
            is_active=True
        )
        membership.deactivate()
        return JsonResponse({
            'success': True, 
            'message': f'Employee removed from {group.name}'
        })
    except AttendanceGroupMembership.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Employee is not assigned to this group'
        })


@login_required
@require_POST
def period_delete(request, period_id):
    """Delete a period (soft delete by deactivating)"""
    user = request.user
    
    # Get the period with access control
    if user.role == 'SUPER_ADMIN':
        period = get_object_or_404(Period, id=period_id)
    elif user.role == 'HR_EMPLOYEE' and user.managed_branch:
        period = get_object_or_404(Period, id=period_id, group__branch=user.managed_branch)
    else:
        period = get_object_or_404(Period, id=period_id, group__company=user.company)
    
    # Check delete permissions
    if not (user.role in ['COMPANY_MANAGER', 'SUPER_ADMIN'] or 
           (user.role == 'HR_EMPLOYEE' and user.managed_branch == period.group.branch)):
        messages.error(request, 'You do not have permission to delete this period.')
        return redirect('attendance:group_detail', group_id=period.group.id)
    
    # Check if period has active check-ins today
    active_checkins = CheckIn.objects.filter(
        period=period,
        timestamp__date=timezone.now().date()
    ).count()
    
    if active_checkins > 0:
        messages.error(request, 
            f'Cannot delete period "{period.name}" because it has {active_checkins} active check-ins today. '
            'Please wait until all employees have checked out.')
        return redirect('attendance:group_detail', group_id=period.group.id)
    
    try:
        period_name = period.name
        group_id = period.group.id
        
        # Soft delete by deactivating
        period.is_active = False
        period.save()
        
        messages.success(request, f'Period "{period_name}" has been deactivated successfully.')
        return redirect('attendance:group_detail', group_id=group_id)
        
    except Exception as e:
        messages.error(request, f'Error deleting period: {str(e)}')
        return redirect('attendance:group_detail', group_id=period.group.id)
