from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse


class CustomLoginView(auth_views.LoginView):
    """
    Custom login view that redirects users based on their role.
    Employees go to check-in page, others go to dashboard.
    """
    
    def get_success_url(self):
        """
        Redirect users based on their role after successful login.
        """
        user = self.request.user
        
        # Redirect employees directly to check-in page
        if user.role == 'EMPLOYEE':
            return reverse('attendance:check_in')
        
        # Redirect all other roles to dashboard
        return reverse('dashboard:dashboard')
