from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company management
    path('<int:company_id>/', views.company_detail, name='company_detail'),
    
    # Branch management
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<int:branch_id>/', views.branch_detail, name='branch_detail'),
    path('branches/<int:branch_id>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:branch_id>/delete/', views.branch_delete, name='branch_delete'),
    
    # Department management within branches
    path('branches/<int:branch_id>/departments/create/', views.department_create, name='department_create'),
]
