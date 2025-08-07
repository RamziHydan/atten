from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Employee attendance actions
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('history/', views.history, name='history'),
    
    # HR/Manager attendance management
    path('checkins/', views.check_in_list, name='check_in_list'),
    path('reports/', views.reports, name='reports'),
    path('analytics/', views.attendance_analytics, name='analytics'),
    path('bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # Attendance group management
    path('groups/', views.attendance_groups, name='groups'),
    path('groups/create/', views.create_attendance_group, name='create_group'),
    path('groups/<int:group_id>/', views.attendance_group_detail, name='group_detail'),
    path('groups/<int:group_id>/edit/', views.edit_attendance_group, name='edit_group'),
    
    # Period/Schedule management
    path('periods/', views.periods_management, name='periods'),
    path('periods/create/', views.create_period, name='create_period'),
    path('periods/<int:period_id>/edit/', views.edit_period, name='edit_period'),
    
    # Export functionality
    path('export/csv/', views.export_attendance_csv, name='export_csv'),
    path('export/pdf/', views.export_attendance_pdf, name='export_pdf'),
]
