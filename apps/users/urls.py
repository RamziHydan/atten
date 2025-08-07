from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User profile and settings
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    
    # Employee management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Department management
    path('departments/', views.department_management, name='department_management'),
    path('departments/assign/', views.assign_department, name='assign_department'),
    path('departments/remove/', views.remove_department, name='remove_department'),
]
