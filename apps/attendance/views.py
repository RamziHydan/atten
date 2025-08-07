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
    List view for HR to see all check-ins (requires HR permissions).
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    # Get all check-ins for the user's company
    checkins = CheckIn.objects.filter(
        attendance_group__company=request.user.company
    ).select_related(
        'employee', 'attendance_group', 'period'
    ).order_by('-timestamp')[:100]  # Limit to last 100 for performance
    
    context = {
        'checkins': checkins,
    }
    
    return render(request, 'attendance/checkin_list.html', context)


@login_required
def reports(request):
    """
    Reports view for HR (requires HR permissions).
    """
    if not request.user.can_manage_hr:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    # This will be implemented with more detailed reporting
    context = {
        'title': 'Attendance Reports',
    }
    
    return render(request, 'attendance/reports.html', context)
