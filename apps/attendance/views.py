from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import AttendanceGroup, CheckIn, AttendanceSummary, Period
from apps.users.models import CustomUser


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
    Advanced check-in list view for HR with filtering and search capabilities.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    # Get filter parameters
    employee_filter = request.GET.get('employee', '')
    date_filter = request.GET.get('date', '')
    group_filter = request.GET.get('group', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    checkins = CheckIn.objects.filter(
        attendance_group__company=request.user.company
    ).select_related(
        'employee', 'attendance_group', 'period'
    )
    
    # Apply filters
    if employee_filter:
        checkins = checkins.filter(
            Q(employee__first_name__icontains=employee_filter) |
            Q(employee__last_name__icontains=employee_filter) |
            Q(employee__username__icontains=employee_filter)
        )
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            checkins = checkins.filter(timestamp__date=filter_date)
        except ValueError:
            pass
    
    if group_filter:
        checkins = checkins.filter(attendance_group_id=group_filter)
    
    if type_filter:
        checkins = checkins.filter(type=type_filter)
    
    # Status filtering (today's activity)
    today = timezone.now().date()
    if status_filter == 'present':
        # Employees who checked in today
        present_employees = CheckIn.objects.filter(
            timestamp__date=today,
            type=CheckIn.CheckInType.CHECK_IN,
            attendance_group__company=request.user.company
        ).values_list('employee_id', flat=True)
        checkins = checkins.filter(employee_id__in=present_employees)
    elif status_filter == 'absent':
        # This would require more complex logic to determine absent employees
        pass
    
    # Order and paginate
    checkins = checkins.order_by('-timestamp')[:200]  # Limit for performance
    
    # Get filter options
    attendance_groups = AttendanceGroup.objects.filter(
        company=request.user.company,
        is_active=True
    )
    
    # Calculate statistics
    stats = {
        'total_checkins': checkins.count(),
        'today_checkins': CheckIn.objects.filter(
            attendance_group__company=request.user.company,
            timestamp__date=today
        ).count(),
        'present_today': CheckIn.objects.filter(
            attendance_group__company=request.user.company,
            timestamp__date=today,
            type=CheckIn.CheckInType.CHECK_IN
        ).values('employee').distinct().count(),
    }
    
    context = {
        'checkins': checkins,
        'attendance_groups': attendance_groups,
        'employee_filter': employee_filter,
        'date_filter': date_filter,
        'group_filter': group_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'stats': stats,
        'checkin_types': CheckIn.CheckInType.choices,
    }
    
    return render(request, 'attendance/checkin_list.html', context)


@login_required
def reports(request):
    """
    Comprehensive attendance reports and analytics for HR.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    company = request.user.company
    
    # Get date range parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'summary')
    department_filter = request.GET.get('department', '')
    
    # Default to current month
    if not start_date:
        start_date = timezone.now().date().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().date().strftime('%Y-%m-%d')
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = timezone.now().date().replace(day=1)
        end_date_obj = timezone.now().date()
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # Base queryset for employees in company
    from apps.users.models import CustomUser
    employees = CustomUser.objects.filter(
        company=company,
        is_active=True
    ).select_related('company')
    
    # Apply department filter
    if department_filter:
        employees = employees.filter(
            departmentmembership__department_id=department_filter,
            departmentmembership__is_active=True
        )
    
    # Calculate comprehensive statistics
    stats = calculate_attendance_stats(company, start_date_obj, end_date_obj, employees)
    
    # Get department options for filtering
    from apps.companies.models import Department
    departments = Department.objects.filter(
        branch__company=company
    ).select_related('branch')
    
    # Generate specific report data based on type
    report_data = {}
    if report_type == 'summary':
        report_data = generate_summary_report(company, start_date_obj, end_date_obj, employees)
    elif report_type == 'detailed':
        report_data = generate_detailed_report(company, start_date_obj, end_date_obj, employees)
    elif report_type == 'late_arrivals':
        report_data = generate_late_arrivals_report(company, start_date_obj, end_date_obj, employees)
    elif report_type == 'overtime':
        report_data = generate_overtime_report(company, start_date_obj, end_date_obj, employees)
    
    context = {
        'title': 'Attendance Reports',
        'stats': stats,
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
        'department_filter': department_filter,
        'departments': departments,
        'employees': employees,
        'date_range_days': (end_date_obj - start_date_obj).days + 1,
    }
    
    return render(request, 'attendance/reports.html', context)


# Helper functions for attendance analytics
def calculate_attendance_stats(company, start_date, end_date, employees):
    """
    Calculate comprehensive attendance statistics for the given period.
    """
    from django.db.models import Count, Avg, Sum, Q
    
    total_employees = employees.count()
    total_days = (end_date - start_date).days + 1
    
    # Get all check-ins for the period
    checkins = CheckIn.objects.filter(
        attendance_group__company=company,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    )
    
    # Basic statistics
    total_checkins = checkins.count()
    unique_checkin_days = checkins.values('timestamp__date').distinct().count()
    
    # Check-in types breakdown
    checkin_breakdown = checkins.values('type').annotate(
        count=Count('id')
    ).order_by('type')
    
    # Daily attendance rates
    daily_checkins = checkins.filter(
        type=CheckIn.CheckInType.CHECK_IN
    ).values('timestamp__date').annotate(
        count=Count('employee', distinct=True)
    ).order_by('timestamp__date')
    
    # Calculate average daily attendance
    if daily_checkins:
        avg_daily_attendance = sum(day['count'] for day in daily_checkins) / len(daily_checkins)
        attendance_rate = (avg_daily_attendance / total_employees * 100) if total_employees > 0 else 0
    else:
        avg_daily_attendance = 0
        attendance_rate = 0
    
    # Late arrivals (assuming 9:00 AM is standard start time)
    from datetime import time
    standard_start_time = time(9, 0)
    late_checkins = checkins.filter(
        type=CheckIn.CheckInType.CHECK_IN,
        timestamp__time__gt=standard_start_time
    ).count()
    
    # Get attendance summaries for more detailed stats
    summaries = AttendanceSummary.objects.filter(
        employee__company=company,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Calculate total hours worked
    total_hours = summaries.aggregate(
        total=Sum('hours_worked')
    )['total'] or 0
    
    # Average hours per employee
    avg_hours_per_employee = (total_hours / total_employees) if total_employees > 0 else 0
    
    return {
        'total_employees': total_employees,
        'total_days': total_days,
        'total_checkins': total_checkins,
        'unique_checkin_days': unique_checkin_days,
        'avg_daily_attendance': round(avg_daily_attendance, 1),
        'attendance_rate': round(attendance_rate, 1),
        'late_checkins': late_checkins,
        'late_rate': round((late_checkins / total_checkins * 100) if total_checkins > 0 else 0, 1),
        'total_hours': round(total_hours, 1),
        'avg_hours_per_employee': round(avg_hours_per_employee, 1),
        'checkin_breakdown': list(checkin_breakdown),
        'daily_checkins': list(daily_checkins),
    }


def generate_summary_report(company, start_date, end_date, employees):
    """
    Generate a summary report with key metrics and trends.
    """
    from django.db.models import Count, Q, Sum
    
    # Employee attendance summary
    employee_stats = []
    for employee in employees[:50]:  # Limit for performance
        checkins = CheckIn.objects.filter(
            employee=employee,
            attendance_group__company=company,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        checkin_days = checkins.values('timestamp__date').distinct().count()
        total_days = (end_date - start_date).days + 1
        attendance_rate = (checkin_days / total_days * 100) if total_days > 0 else 0
        
        # Get hours worked from summaries
        summaries = AttendanceSummary.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        )
        total_hours = summaries.aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0
        
        employee_stats.append({
            'employee': employee,
            'checkin_days': checkin_days,
            'attendance_rate': round(attendance_rate, 1),
            'total_hours': round(total_hours, 1),
            'avg_hours_per_day': round(total_hours / checkin_days, 1) if checkin_days > 0 else 0,
        })
    
    # Sort by attendance rate
    employee_stats.sort(key=lambda x: x['attendance_rate'], reverse=True)
    
    return {
        'employee_stats': employee_stats,
        'top_performers': employee_stats[:10],
        'needs_attention': [emp for emp in employee_stats if emp['attendance_rate'] < 80],
    }


def generate_detailed_report(company, start_date, end_date, employees):
    """
    Generate a detailed report with daily breakdown.
    """
    from django.db.models import Q
    from collections import defaultdict
    
    # Daily attendance breakdown
    daily_data = defaultdict(lambda: {
        'date': None,
        'total_employees': 0,
        'present': 0,
        'late': 0,
        'checkins': [],
    })
    
    # Get all check-ins for the period
    checkins = CheckIn.objects.filter(
        attendance_group__company=company,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date,
        type=CheckIn.CheckInType.CHECK_IN
    ).select_related('employee', 'attendance_group').order_by('timestamp')
    
    # Process daily data
    current_date = start_date
    while current_date <= end_date:
        daily_data[current_date]['date'] = current_date
        daily_data[current_date]['total_employees'] = employees.count()
        current_date += timedelta(days=1)
    
    # Standard start time for late calculation
    from datetime import time
    standard_start_time = time(9, 0)
    
    for checkin in checkins:
        date = checkin.timestamp.date()
        daily_data[date]['present'] += 1
        daily_data[date]['checkins'].append(checkin)
        
        if checkin.timestamp.time() > standard_start_time:
            daily_data[date]['late'] += 1
    
    # Convert to list and calculate rates
    daily_list = []
    for date, data in sorted(daily_data.items()):
        attendance_rate = (data['present'] / data['total_employees'] * 100) if data['total_employees'] > 0 else 0
        late_rate = (data['late'] / data['present'] * 100) if data['present'] > 0 else 0
        
        daily_list.append({
            'date': date,
            'total_employees': data['total_employees'],
            'present': data['present'],
            'late': data['late'],
            'attendance_rate': round(attendance_rate, 1),
            'late_rate': round(late_rate, 1),
            'checkins': data['checkins'][:20],  # Limit for performance
        })
    
    return {
        'daily_breakdown': daily_list,
        'summary': {
            'total_days': len(daily_list),
            'avg_attendance_rate': round(sum(day['attendance_rate'] for day in daily_list) / len(daily_list), 1) if daily_list else 0,
            'avg_late_rate': round(sum(day['late_rate'] for day in daily_list) / len(daily_list), 1) if daily_list else 0,
        }
    }


def generate_late_arrivals_report(company, start_date, end_date, employees):
    """
    Generate a report focused on late arrivals.
    """
    from datetime import time
    
    standard_start_time = time(9, 0)
    
    # Get late check-ins
    late_checkins = CheckIn.objects.filter(
        attendance_group__company=company,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date,
        type=CheckIn.CheckInType.CHECK_IN,
        timestamp__time__gt=standard_start_time
    ).select_related('employee', 'attendance_group').order_by('-timestamp')
    
    # Group by employee
    from collections import defaultdict
    employee_late_stats = defaultdict(lambda: {
        'employee': None,
        'late_count': 0,
        'total_checkins': 0,
        'late_checkins': [],
        'avg_late_minutes': 0,
    })
    
    for checkin in late_checkins:
        emp_id = checkin.employee.id
        if not employee_late_stats[emp_id]['employee']:
            employee_late_stats[emp_id]['employee'] = checkin.employee
        
        employee_late_stats[emp_id]['late_count'] += 1
        employee_late_stats[emp_id]['late_checkins'].append(checkin)
        
        # Calculate minutes late
        checkin_time = checkin.timestamp.time()
        minutes_late = (checkin_time.hour - standard_start_time.hour) * 60 + (checkin_time.minute - standard_start_time.minute)
        employee_late_stats[emp_id]['avg_late_minutes'] += minutes_late
    
    # Calculate total check-ins for each employee and finalize stats
    for emp_id, stats in employee_late_stats.items():
        total_checkins = CheckIn.objects.filter(
            employee=stats['employee'],
            attendance_group__company=company,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date,
            type=CheckIn.CheckInType.CHECK_IN
        ).count()
        
        stats['total_checkins'] = total_checkins
        stats['late_rate'] = round((stats['late_count'] / total_checkins * 100) if total_checkins > 0 else 0, 1)
        stats['avg_late_minutes'] = round(stats['avg_late_minutes'] / stats['late_count'], 1) if stats['late_count'] > 0 else 0
    
    # Convert to list and sort by late rate
    late_stats_list = list(employee_late_stats.values())
    late_stats_list.sort(key=lambda x: x['late_rate'], reverse=True)
    
    return {
        'late_employees': late_stats_list,
        'total_late_checkins': late_checkins.count(),
        'chronic_late_employees': [emp for emp in late_stats_list if emp['late_rate'] > 20],
        'recent_late_checkins': list(late_checkins[:50]),
    }


def generate_overtime_report(company, start_date, end_date, employees):
    """
    Generate a report focused on overtime and working hours.
    """
    # Get attendance summaries for the period
    summaries = AttendanceSummary.objects.filter(
        employee__company=company,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('employee').order_by('-hours_worked')
    
    # Standard working hours per day
    standard_hours = 8.0
    
    # Calculate overtime statistics
    overtime_stats = []
    for summary in summaries:
        overtime_hours = max(0, summary.hours_worked - standard_hours)
        
        overtime_stats.append({
            'employee': summary.employee,
            'date': summary.date,
            'hours_worked': summary.hours_worked,
            'overtime_hours': round(overtime_hours, 1),
            'status': summary.status,
        })
    
    # Group by employee for summary
    from collections import defaultdict
    employee_overtime = defaultdict(lambda: {
        'employee': None,
        'total_hours': 0,
        'total_overtime': 0,
        'days_worked': 0,
        'overtime_days': 0,
    })
    
    for stat in overtime_stats:
        emp_id = stat['employee'].id
        if not employee_overtime[emp_id]['employee']:
            employee_overtime[emp_id]['employee'] = stat['employee']
        
        employee_overtime[emp_id]['total_hours'] += stat['hours_worked']
        employee_overtime[emp_id]['total_overtime'] += stat['overtime_hours']
        employee_overtime[emp_id]['days_worked'] += 1
        
        if stat['overtime_hours'] > 0:
            employee_overtime[emp_id]['overtime_days'] += 1
    
    # Convert to list and calculate averages
    employee_overtime_list = []
    for emp_data in employee_overtime.values():
        avg_hours = emp_data['total_hours'] / emp_data['days_worked'] if emp_data['days_worked'] > 0 else 0
        overtime_rate = (emp_data['overtime_days'] / emp_data['days_worked'] * 100) if emp_data['days_worked'] > 0 else 0
        
        employee_overtime_list.append({
            'employee': emp_data['employee'],
            'total_hours': round(emp_data['total_hours'], 1),
            'total_overtime': round(emp_data['total_overtime'], 1),
            'days_worked': emp_data['days_worked'],
            'overtime_days': emp_data['overtime_days'],
            'avg_hours': round(avg_hours, 1),
            'overtime_rate': round(overtime_rate, 1),
        })
    
    # Sort by total overtime
    employee_overtime_list.sort(key=lambda x: x['total_overtime'], reverse=True)
    
    return {
        'daily_overtime': overtime_stats[:100],  # Limit for performance
        'employee_overtime': employee_overtime_list,
        'high_overtime_employees': [emp for emp in employee_overtime_list if emp['total_overtime'] > 40],
        'total_overtime_hours': sum(emp['total_overtime'] for emp in employee_overtime_list),
    }


# Additional Attendance Management Views
@login_required
def attendance_analytics(request):
    """
    Advanced analytics dashboard for attendance data.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    company = request.user.company
    today = timezone.now().date()
    
    # Get analytics for different time periods
    periods = {
        'today': (today, today),
        'week': (today - timedelta(days=7), today),
        'month': (today.replace(day=1), today),
        'quarter': (today - timedelta(days=90), today),
    }
    
    analytics_data = {}
    for period_name, (start_date, end_date) in periods.items():
        employees = CustomUser.objects.filter(company=company, is_active=True)
        analytics_data[period_name] = calculate_attendance_stats(
            company, start_date, end_date, employees
        )
    
    # Get trending data for charts
    chart_data = generate_chart_data(company, today - timedelta(days=30), today)
    
    context = {
        'analytics_data': analytics_data,
        'chart_data': chart_data,
        'company': company,
    }
    
    return render(request, 'attendance/analytics.html', context)


@login_required
def bulk_actions(request):
    """
    Bulk actions for attendance management.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'approve_overtime':
            # Approve overtime for selected attendance summaries
            AttendanceSummary.objects.filter(
                id__in=selected_ids,
                employee__company=request.user.company
            ).update(overtime_approved=True)
            messages.success(request, f'Approved overtime for {len(selected_ids)} records.')
        
        elif action == 'mark_excused':
            # Mark absences as excused
            AttendanceSummary.objects.filter(
                id__in=selected_ids,
                employee__company=request.user.company
            ).update(status='EXCUSED')
            messages.success(request, f'Marked {len(selected_ids)} absences as excused.')
        
        elif action == 'generate_report':
            # Generate custom report for selected items
            return redirect('attendance:reports')
    
    # Get recent attendance summaries for bulk actions
    recent_summaries = AttendanceSummary.objects.filter(
        employee__company=request.user.company
    ).select_related('employee').order_by('-date')[:100]
    
    context = {
        'recent_summaries': recent_summaries,
    }
    
    return render(request, 'attendance/bulk_actions.html', context)


@login_required
def attendance_groups(request):
    """
    Manage attendance groups.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    groups = AttendanceGroup.objects.filter(
        company=request.user.company
    ).select_related('company').prefetch_related('employees')
    
    context = {
        'groups': groups,
    }
    
    return render(request, 'attendance/groups.html', context)


@login_required
def create_attendance_group(request):
    """
    Create a new attendance group.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            latitude = float(request.POST.get('latitude', 0))
            longitude = float(request.POST.get('longitude', 0))
            radius = int(request.POST.get('radius', 100))
            description = request.POST.get('description', '')
            
            group = AttendanceGroup.objects.create(
                name=name,
                company=request.user.company,
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                description=description
            )
            
            messages.success(request, f'Attendance group "{name}" created successfully!')
            return redirect('attendance:group_detail', group_id=group.id)
            
        except Exception as e:
            messages.error(request, f'Error creating attendance group: {str(e)}')
    
    context = {}
    return render(request, 'attendance/create_group.html', context)


@login_required
def attendance_group_detail(request, group_id):
    """
    View attendance group details.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    group = get_object_or_404(
        AttendanceGroup,
        id=group_id,
        company=request.user.company
    )
    
    # Get recent check-ins for this group
    recent_checkins = CheckIn.objects.filter(
        attendance_group=group
    ).select_related('employee').order_by('-timestamp')[:50]
    
    # Get group statistics
    today = timezone.now().date()
    stats = {
        'total_employees': group.employees.count(),
        'today_checkins': recent_checkins.filter(timestamp__date=today).count(),
        'total_periods': group.periods.count(),
    }
    
    context = {
        'group': group,
        'recent_checkins': recent_checkins,
        'stats': stats,
    }
    
    return render(request, 'attendance/group_detail.html', context)


@login_required
def edit_attendance_group(request, group_id):
    """
    Edit an attendance group.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    group = get_object_or_404(
        AttendanceGroup,
        id=group_id,
        company=request.user.company
    )
    
    if request.method == 'POST':
        try:
            group.name = request.POST.get('name', group.name)
            group.latitude = float(request.POST.get('latitude', group.latitude))
            group.longitude = float(request.POST.get('longitude', group.longitude))
            group.radius = int(request.POST.get('radius', group.radius))
            group.description = request.POST.get('description', group.description)
            group.is_active = request.POST.get('is_active') == 'on'
            group.save()
            
            messages.success(request, f'Attendance group "{group.name}" updated successfully!')
            return redirect('attendance:group_detail', group_id=group.id)
            
        except Exception as e:
            messages.error(request, f'Error updating attendance group: {str(e)}')
    
    context = {
        'group': group,
    }
    
    return render(request, 'attendance/edit_group.html', context)


@login_required
def periods_management(request):
    """
    Manage attendance periods/schedules.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    periods = Period.objects.filter(
        group__company=request.user.company
    ).select_related('group').order_by('group__name', 'start_time')
    
    context = {
        'periods': periods,
    }
    
    return render(request, 'attendance/periods.html', context)


@login_required
def create_period(request):
    """
    Create a new attendance period.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            group_id = request.POST.get('group')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            weekdays = ','.join(request.POST.getlist('weekdays'))
            
            group = get_object_or_404(
                AttendanceGroup,
                id=group_id,
                company=request.user.company
            )
            
            period = Period.objects.create(
                name=name,
                group=group,
                start_time=start_time,
                end_time=end_time,
                weekdays=weekdays
            )
            
            messages.success(request, f'Period "{name}" created successfully!')
            return redirect('attendance:periods')
            
        except Exception as e:
            messages.error(request, f'Error creating period: {str(e)}')
    
    groups = AttendanceGroup.objects.filter(
        company=request.user.company,
        is_active=True
    )
    
    context = {
        'groups': groups,
        'weekdays': [
            ('1', 'Monday'),
            ('2', 'Tuesday'),
            ('3', 'Wednesday'),
            ('4', 'Thursday'),
            ('5', 'Friday'),
            ('6', 'Saturday'),
            ('7', 'Sunday'),
        ]
    }
    
    return render(request, 'attendance/create_period.html', context)


@login_required
def edit_period(request, period_id):
    """
    Edit an attendance period.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:dashboard')
    
    period = get_object_or_404(
        Period,
        id=period_id,
        group__company=request.user.company
    )
    
    if request.method == 'POST':
        try:
            period.name = request.POST.get('name', period.name)
            period.start_time = request.POST.get('start_time', period.start_time)
            period.end_time = request.POST.get('end_time', period.end_time)
            period.weekdays = ','.join(request.POST.getlist('weekdays'))
            period.is_active = request.POST.get('is_active') == 'on'
            period.save()
            
            messages.success(request, f'Period "{period.name}" updated successfully!')
            return redirect('attendance:periods')
            
        except Exception as e:
            messages.error(request, f'Error updating period: {str(e)}')
    
    context = {
        'period': period,
        'current_weekdays': period.weekdays.split(',') if period.weekdays else [],
        'weekdays': [
            ('1', 'Monday'),
            ('2', 'Tuesday'),
            ('3', 'Wednesday'),
            ('4', 'Thursday'),
            ('5', 'Friday'),
            ('6', 'Saturday'),
            ('7', 'Sunday'),
        ]
    }
    
    return render(request, 'attendance/edit_period.html', context)


@login_required
def export_attendance_csv(request):
    """
    Export attendance data as CSV.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to access this feature.')
        return redirect('dashboard:dashboard')
    
    import csv
    from django.http import HttpResponse
    
    # Get date range from query parameters
    start_date = request.GET.get('start_date', timezone.now().date().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().date().strftime('%Y-%m-%d'))
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('attendance:reports')
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'Employee Name',
        'Employee ID',
        'Date',
        'Check In Time',
        'Check Out Time',
        'Hours Worked',
        'Status',
        'Attendance Group',
        'Notes'
    ])
    
    # Get attendance summaries for the period
    summaries = AttendanceSummary.objects.filter(
        employee__company=request.user.company,
        date__gte=start_date_obj,
        date__lte=end_date_obj
    ).select_related('employee', 'attendance_group', 'first_checkin', 'last_checkout').order_by('date', 'employee__last_name')
    
    # Write data rows
    for summary in summaries:
        writer.writerow([
            summary.employee.get_full_name(),
            summary.employee.username,
            summary.date.strftime('%Y-%m-%d'),
            summary.first_checkin.timestamp.strftime('%H:%M:%S') if summary.first_checkin else '',
            summary.last_checkout.timestamp.strftime('%H:%M:%S') if summary.last_checkout else '',
            summary.hours_worked,
            summary.get_status_display(),
            summary.attendance_group.name if summary.attendance_group else '',
            summary.notes or ''
        ])
    
    return response


@login_required
def export_attendance_pdf(request):
    """
    Export attendance data as PDF report.
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to access this feature.')
        return redirect('dashboard:dashboard')
    
    # This would require a PDF library like ReportLab
    # For now, redirect to CSV export
    messages.info(request, 'PDF export is coming soon. Using CSV export instead.')
    return redirect('attendance:export_csv')


def generate_chart_data(company, start_date, end_date):
    """
    Generate data for attendance charts and graphs.
    """
    from django.db.models import Count
    
    # Daily attendance trend
    daily_checkins = CheckIn.objects.filter(
        attendance_group__company=company,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date,
        type=CheckIn.CheckInType.CHECK_IN
    ).values('timestamp__date').annotate(
        count=Count('employee', distinct=True)
    ).order_by('timestamp__date')
    
    # Department-wise attendance
    from apps.companies.models import Department
    dept_attendance = {}
    departments = Department.objects.filter(branch__company=company)
    
    for dept in departments:
        dept_checkins = CheckIn.objects.filter(
            attendance_group__company=company,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date,
            type=CheckIn.CheckInType.CHECK_IN,
            employee__departmentmembership__department=dept,
            employee__departmentmembership__is_active=True
        ).values('employee').distinct().count()
        
        dept_attendance[dept.name] = dept_checkins
    
    return {
        'daily_trend': list(daily_checkins),
        'department_breakdown': dept_attendance,
        'period': f'{start_date} to {end_date}'
    }
