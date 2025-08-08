from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Check-in/Check-out functionality
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('api/today-status/', views.today_status_api, name='today_status_api'),
    path('history/', views.history, name='history'),
    path('checkins/', views.check_in_list, name='check_in_list'),
    path('reports/', views.reports, name='reports'),
    
    # Attendance Group Management
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),
    
    # Period management
    path('groups/<int:group_id>/periods/create/', views.period_create, name='period_create'),
    path('periods/<int:period_id>/edit/', views.period_edit, name='period_edit'),
    path('periods/<int:period_id>/delete/', views.period_delete, name='period_delete'),
    
    # Employee management
    path('groups/<int:group_id>/employees/', views.group_manage_employees, name='group_manage_employees'),
    path('groups/<int:group_id>/employees/<int:employee_id>/remove/', views.group_remove_employee, name='group_remove_employee'),
]
