"""
Subscription mixins for Django views to enforce subscription limits and access control.
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import (
    get_subscription_status_context,
    check_employee_limit,
    check_branch_limit,
    check_attendance_group_limit,
    check_feature_access,
    SubscriptionLimitExceeded
)


class SubscriptionContextMixin:
    """
    Mixin to add subscription context to views.
    Adds subscription information to the template context.
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add subscription context if user has a company
        if hasattr(self.request.user, 'company') and self.request.user.company:
            context['subscription_info'] = get_subscription_status_context(self.request.user.company)
        
        return context


class SubscriptionRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure user has an active subscription.
    Redirects to subscription page if no active subscription.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Super admins bypass subscription checks
        if request.user.role == 'SUPER_ADMIN':
            return super().dispatch(request, *args, **kwargs)
        
        # Check if user has a company
        if not hasattr(request.user, 'company') or not request.user.company:
            messages.error(request, "No company associated with your account.")
            return redirect('subscriptions:home')
        
        # Check if company has an active subscription
        from .utils import get_company_subscription
        subscription = get_company_subscription(request.user.company)
        
        if not subscription or not (subscription.is_active or subscription.is_trial):
            messages.warning(request, "Your subscription has expired. Please renew to continue using the platform.")
            return redirect('subscriptions:manage')
        
        return super().dispatch(request, *args, **kwargs)


class SubscriptionLimitMixin:
    """
    Mixin to check subscription limits before allowing creation.
    Set limit_type attribute to specify which limit to check.
    """
    limit_type = None  # Should be 'employee', 'branch', or 'attendance_group'
    
    def dispatch(self, request, *args, **kwargs):
        # Super admins bypass limit checks
        if request.user.role == 'SUPER_ADMIN':
            return super().dispatch(request, *args, **kwargs)
        
        # Only check limits for POST requests (creation/updates)
        if request.method == 'POST' and self.limit_type:
            try:
                if self.limit_type == 'employee':
                    check_employee_limit(request.user.company)
                elif self.limit_type == 'branch':
                    check_branch_limit(request.user.company)
                elif self.limit_type == 'attendance_group':
                    check_attendance_group_limit(request.user.company)
                
            except SubscriptionLimitExceeded as e:
                messages.error(request, str(e))
                return redirect('subscriptions:manage')
        
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin:
    """
    Mixin to require specific subscription features.
    Set required_feature attribute to specify which feature is required.
    """
    required_feature = None  # Should be feature name like 'has_advanced_reporting'
    
    def dispatch(self, request, *args, **kwargs):
        # Super admins bypass feature checks
        if request.user.role == 'SUPER_ADMIN':
            return super().dispatch(request, *args, **kwargs)
        
        if self.required_feature:
            if not request.user.company:
                raise PermissionDenied("No company associated with user")
            
            if not check_feature_access(request.user.company, self.required_feature):
                messages.error(request, "This feature requires a subscription upgrade.")
                return redirect('subscriptions:pricing')
        
        return super().dispatch(request, *args, **kwargs)


class CompanyOwnerRequiredMixin:
    """
    Mixin to ensure only company owners can access certain views.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Super admins can access everything
        if request.user.role == 'SUPER_ADMIN':
            return super().dispatch(request, *args, **kwargs)
        
        # Only company managers (owners) can access
        if request.user.role != 'COMPANY_MANAGER':
            raise PermissionDenied("Only company owners can access this feature.")
        
        return super().dispatch(request, *args, **kwargs)


class SubscriptionAwareMixin(SubscriptionContextMixin, SubscriptionRequiredMixin):
    """
    Combined mixin that adds subscription context and requires active subscription.
    Use this for most views that need subscription awareness.
    """
    pass
