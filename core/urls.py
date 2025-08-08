"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from apps.users.auth_views import CustomLoginView

# Redirect root based on user role
def root_redirect(request):
    if request.user.is_authenticated:
        # Redirect employees to check-in, others to dashboard
        if request.user.role == 'EMPLOYEE':
            return redirect('attendance:check_in')
        return redirect('dashboard:dashboard')
    return redirect('login')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Root redirect
    path('', root_redirect, name='root'),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    
    # App URLs
    path('dashboard/', include('apps.dashboard.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('companies/', include('apps.companies.urls')),
    path('users/', include('apps.users.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
