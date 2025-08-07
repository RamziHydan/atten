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
    
    # Get user's attendance groups
    user_attendance_groups = AttendanceGroup.objects.filter(
        employees=user,
        is_active=True
    ).select_related('company', 'branch')
    
    # Today's status
    today_checkins = CheckIn.objects.filter(
        employee=user,
        timestamp__date=today
    ).order_by('timestamp')
    
    today_status = today_checkins.exists()
    last_checkin = today_checkins.last() if today_checkins.exists() else None
    
    # Week statistics
    week_start = today - timedelta(days=today.weekday())
    week_summaries = AttendanceSummary.objects.filter(
        employee=user,
        date__gte=week_start,
        date__lte=today
    )
    
    week_stats = {
        'days_present': week_summaries.filter(is_present=True).count(),
        'total_days': min((today - week_start).days + 1, 5),  # Only count weekdays
        'hours_worked': week_summaries.aggregate(total=Sum('total_hours'))['total'] or 0,
        'percentage': 0
    }
    
    if week_stats['total_days'] > 0:
        week_stats['percentage'] = round((week_stats['days_present'] / week_stats['total_days']) * 100)
    
    # Month statistics
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
    
    month_stats = {
        'days_present': month_summaries.filter(is_present=True).count(),
        'total_days': working_days_in_month,
        'hours_worked': month_summaries.aggregate(total=Sum('total_hours'))['total'] or 0,
        'percentage': 0
    }
    
    if month_stats['total_days'] > 0:
        month_stats['percentage'] = round((month_stats['days_present'] / month_stats['total_days']) * 100)
    
    # Average daily hours
    avg_daily_hours = month_summaries.filter(is_present=True).aggregate(
        avg=Avg('total_hours')
    )['avg'] or 0
    avg_daily_hours = round(avg_daily_hours, 1)
    
    # Recent check-ins (last 10)
    recent_checkins = CheckIn.objects.filter(
        employee=user
    ).select_related('attendance_group', 'period').order_by('-timestamp')[:10]
    
    # User's periods for today
    user_periods = []
    for group in user_attendance_groups:
        periods = group.periods.filter(is_active=True)
        for period in periods:
            if period.is_applicable_today():
                user_periods.append(period)
    
    context = {
        'today_status': today_status,
        'last_checkin': last_checkin,
        'week_stats': week_stats,
        'month_stats': month_stats,
        'avg_daily_hours': avg_daily_hours,
        'recent_checkins': recent_checkins,
        'user_periods': user_periods,
        'attendance_groups': user_attendance_groups,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile(request):
    """
    User profile view.
    """
    # This will be implemented later
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def settings(request):
    """
    User settings view.
    """
    # This will be implemented later
    return render(request, 'users/settings.html', {'user': request.user})
