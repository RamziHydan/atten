from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from apps.subscriptions.models import CompanySubscription


def subscription_required(feature_check=None, redirect_url='subscriptions:pricing'):
    """
    Decorator to check if user's subscription supports a specific feature.
    
    Args:
        feature_check: Function that takes a subscription plan and returns True if feature is allowed
        redirect_url: URL to redirect to if feature is not allowed
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if not user.is_authenticated:
                messages.error(request, 'Please log in to access this feature.')
                return redirect('login')
            
            if not user.company:
                messages.error(request, 'You must be associated with a company.')
                return redirect('dashboard:home')
            
            try:
                subscription = CompanySubscription.objects.get(company=user.company)
                plan = subscription.plan
                
                # Check if subscription is active
                if subscription.status != 'ACTIVE':
                    messages.warning(request, 
                        'Your subscription is not active. Please renew your subscription to access this feature.')
                    return redirect(redirect_url)
                
                # If no specific feature check, just verify active subscription
                if feature_check is None:
                    return view_func(request, *args, **kwargs)
                
                # Run the feature check
                if not feature_check(plan):
                    messages.warning(request, 
                        f'This feature is not available in your current plan ({plan.name}). '
                        f'Please upgrade to access this feature.')
                    return redirect(redirect_url)
                
            except CompanySubscription.DoesNotExist:
                messages.warning(request, 
                    'No active subscription found. Please subscribe to a plan to access this feature.')
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_employee_limit(plan):
    """Check if plan allows more employees"""
    def checker(request):
        from apps.users.models import CustomUser
        current_count = CustomUser.objects.filter(
            company=request.user.company,
            role__in=['EMPLOYEE', 'HR_EMPLOYEE']
        ).count()
        
        if plan.max_employees == -1:  # Unlimited
            return True
        return current_count < plan.max_employees
    return checker


def check_branch_limit(plan):
    """Check if plan allows more branches"""
    def checker(request):
        from apps.companies.models import Branch
        current_count = Branch.objects.filter(company=request.user.company).count()
        
        if plan.max_branches == -1:  # Unlimited
            return True
        return current_count < plan.max_branches
    return checker


def check_attendance_group_limit(plan):
    """Check if plan allows more attendance groups"""
    def checker(request):
        from apps.attendance.models import AttendanceGroup
        current_count = AttendanceGroup.objects.filter(company=request.user.company).count()
        
        if plan.max_attendance_groups == -1:  # Unlimited
            return True
        return current_count < plan.max_attendance_groups
    return checker


def check_advanced_reporting(plan):
    """Check if plan has advanced reporting"""
    return plan.has_advanced_reporting


def check_api_access(plan):
    """Check if plan has API access"""
    return plan.has_api_access


def check_data_export(plan):
    """Check if plan has data export"""
    return plan.has_data_export


def check_custom_branding(plan):
    """Check if plan has custom branding"""
    return plan.has_custom_branding
