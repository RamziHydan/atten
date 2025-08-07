from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'users'

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'users/profile.html', {
        'title': 'My Profile',
        'user': request.user
    })

@login_required
def settings(request):
    """User settings view"""
    return render(request, 'users/settings.html', {
        'title': 'Settings',
        'user': request.user
    })

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('settings/', settings, name='settings'),
]
