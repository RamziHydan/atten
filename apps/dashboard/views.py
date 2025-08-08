from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg
from apps.attendance.models import CheckIn, AttendanceSummary, AttendanceGroup, Period
from apps.users.models import CustomUser


@login_required
def dashboard(request):
    """
    Main dashboard view showing attendance statistics and recent activity.
    """
    user = request.user
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Get user's attendance groups through the membership relationship
    user_attendance_groups = AttendanceGroup.objects.filter(
        attendancegroupmembership__employee=user,
        attendancegroupmembership__is_active=True,
        is_active=True
    ).select_related('company', 'branch').distinct()
    
    # Today's status
    today_checkins = CheckIn.objects.filter(
        employee=user,
        timestamp__date=today
    ).select_related('attendance_group').order_by('timestamp')
    
    today_status = today_checkins.exists()
    last_checkin = today_checkins.last() if today_checkins.exists() else None
    
    # Calculate today's work hours
    today_hours = 0
    if today_checkins.count() >= 2:
        checkins = list(today_checkins)
        for i in range(0, len(checkins) - 1, 2):
            if i + 1 < len(checkins):
                check_in = checkins[i]
                check_out = checkins[i + 1]
                if check_in.type == 'IN' and check_out.type == 'OUT':
                    duration = check_out.timestamp - check_in.timestamp
                    today_hours += duration.total_seconds() / 3600
    
    # Week statistics - calculate from CheckIn records if AttendanceSummary doesn't exist
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Try to get from AttendanceSummary first
    week_summaries = AttendanceSummary.objects.filter(
        employee=user,
        date__gte=week_start,
        date__lte=today
    )
    
    if week_summaries.exists():
        week_stats = {
            'days_present': week_summaries.filter(is_present=True).count(),
            'total_days': min((today - week_start).days + 1, 5),  # Only count weekdays
            'hours_worked': week_summaries.aggregate(total=Sum('total_hours'))['total'] or 0,
            'percentage': 0
        }
    else:
        # Calculate from CheckIn records
        week_checkins = CheckIn.objects.filter(
            employee=user,
            timestamp__date__gte=week_start,
            timestamp__date__lte=today
        ).order_by('timestamp__date', 'timestamp')
        
        # Count unique days with check-ins
        days_with_checkins = week_checkins.values('timestamp__date').distinct().count()
        
        # Calculate total hours worked this week
        week_hours = 0
        checkins_by_date = {}
        for checkin in week_checkins:
            date_key = checkin.timestamp.date()
            if date_key not in checkins_by_date:
                checkins_by_date[date_key] = []
            checkins_by_date[date_key].append(checkin)
        
        for date_checkins in checkins_by_date.values():
            for i in range(0, len(date_checkins) - 1, 2):
                if i + 1 < len(date_checkins):
                    check_in = date_checkins[i]
                    check_out = date_checkins[i + 1]
                    if check_in.type == 'IN' and check_out.type == 'OUT':
                        duration = check_out.timestamp - check_in.timestamp
                        week_hours += duration.total_seconds() / 3600
        
        # Count working days in current week up to today
        working_days = 0
        current_date = week_start
        while current_date <= today:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                working_days += 1
            current_date += timedelta(days=1)
        
        week_stats = {
            'days_present': days_with_checkins,
            'total_days': working_days,
            'hours_worked': round(week_hours, 1),
            'percentage': 0
        }
    
    if week_stats['total_days'] > 0:
        week_stats['percentage'] = round((week_stats['days_present'] / week_stats['total_days']) * 100)
    
    # Month statistics - calculate from CheckIn records if AttendanceSummary doesn't exist
    month_start = today.replace(day=1)
    month_summaries = AttendanceSummary.objects.filter(
        employee=user,
        date__gte=month_start,
        date__lte=today
    )
    
    # Calculate working days in month (excluding weekends)
    working_days_in_month = 0
    current_date = month_start
    while current_date <= today:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            working_days_in_month += 1
        current_date += timedelta(days=1)
    
    if month_summaries.exists():
        month_stats = {
            'days_present': month_summaries.filter(is_present=True).count(),
            'total_days': working_days_in_month,
            'hours_worked': month_summaries.aggregate(total=Sum('total_hours'))['total'] or 0,
            'percentage': 0
        }
        avg_daily_hours = month_summaries.filter(is_present=True).aggregate(
            avg=Avg('total_hours')
        )['avg'] or 0
    else:
        # Calculate from CheckIn records
        month_checkins = CheckIn.objects.filter(
            employee=user,
            timestamp__date__gte=month_start,
            timestamp__date__lte=today
        ).order_by('timestamp__date', 'timestamp')
        
        # Count unique days with check-ins
        days_with_checkins = month_checkins.values('timestamp__date').distinct().count()
        
        # Calculate total hours worked this month
        month_hours = 0
        daily_hours = []
        checkins_by_date = {}
        for checkin in month_checkins:
            date_key = checkin.timestamp.date()
            if date_key not in checkins_by_date:
                checkins_by_date[date_key] = []
            checkins_by_date[date_key].append(checkin)
        
        for date_checkins in checkins_by_date.values():
            day_hours = 0
            for i in range(0, len(date_checkins) - 1, 2):
                if i + 1 < len(date_checkins):
                    check_in = date_checkins[i]
                    check_out = date_checkins[i + 1]
                    if check_in.type == 'IN' and check_out.type == 'OUT':
                        duration = check_out.timestamp - check_in.timestamp
                        day_hours += duration.total_seconds() / 3600
            if day_hours > 0:
                daily_hours.append(day_hours)
                month_hours += day_hours
        
        month_stats = {
            'days_present': days_with_checkins,
            'total_days': working_days_in_month,
            'hours_worked': round(month_hours, 1),
            'percentage': 0
        }
        
        # Calculate average daily hours
        avg_daily_hours = sum(daily_hours) / len(daily_hours) if daily_hours else 0
    
    if month_stats['total_days'] > 0:
        month_stats['percentage'] = round((month_stats['days_present'] / month_stats['total_days']) * 100)
    
    avg_daily_hours = round(avg_daily_hours, 1)
    
    # Recent check-ins (last 10)
    recent_checkins = CheckIn.objects.filter(
        employee=user
    ).select_related('attendance_group').order_by('-timestamp')[:10]
    
    # User's periods for today
    user_periods = []
    for group in user_attendance_groups:
        periods = group.periods.filter(is_active=True)
        for period in periods:
            if hasattr(period, 'is_applicable_today') and period.is_applicable_today():
                user_periods.append(period)
    
    # Current status (checked in or out)
    is_currently_checked_in = False
    if last_checkin:
        is_currently_checked_in = last_checkin.type == 'IN'
    
    # Quick stats for today
    today_stats = {
        'total_checkins': today_checkins.count(),
        'hours_worked': round(today_hours, 1),
        'is_checked_in': is_currently_checked_in,
        'first_checkin': today_checkins.first() if today_checkins.exists() else None,
        'last_checkin': last_checkin
    }
    
    context = {
        'today_status': today_status,
        'today_stats': today_stats,
        'last_checkin': last_checkin,
        'week_stats': week_stats,
        'month_stats': month_stats,
        'avg_daily_hours': avg_daily_hours,
        'recent_checkins': recent_checkins,
        'user_periods': user_periods,
        'attendance_groups': user_attendance_groups,
        'current_time': current_time,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile(request):
    """
    User profile view with update functionality.
    """
    from django.contrib import messages
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update basic profile information
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Validate email uniqueness (excluding current user)
            if email and CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'This email address is already in use.')
            else:
                # Update user fields
                user.first_name = first_name
                user.last_name = last_name
                if email:
                    user.email = email
                user.save()
                messages.success(request, 'Profile updated successfully!')
        
        elif action == 'change_password':
            # Handle password change
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.replace("_", " ").title()}: {error}')
    
    # Get user's attendance groups and recent activity
    user_attendance_groups = AttendanceGroup.objects.filter(
        employees=user,
        is_active=True
    ).select_related('company', 'branch')
    
    recent_checkins = CheckIn.objects.filter(
        employee=user
    ).select_related('attendance_group').order_by('-timestamp')[:5]
    
    context = {
        'user': user,
        'attendance_groups': user_attendance_groups,
        'recent_checkins': recent_checkins,
        'password_form': PasswordChangeForm(user),
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def settings(request):
    """
    User settings view.
    """
    # This will be implemented later
    return render(request, 'users/settings.html', {'user': request.user})
