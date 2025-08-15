"""
Subscription utility functions for enforcing plan limits and access control.
"""
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from .models import CompanySubscription, SubscriptionPlan


class SubscriptionLimitExceeded(Exception):
    """Exception raised when subscription limits are exceeded"""
    pass


def get_company_subscription(company):
    """
    Get the active subscription for a company.
    Returns the subscription or None if no active subscription exists.
    """
    try:
        subscription = CompanySubscription.objects.get(company=company)
        if subscription.is_active or subscription.is_trial:
            return subscription
    except CompanySubscription.DoesNotExist:
        pass
    
    # If no subscription exists, assign free plan
    try:
        free_plan = SubscriptionPlan.objects.get(plan_type='FREE')
        subscription = CompanySubscription.objects.create(
            company=company,
            plan=free_plan,
            status='ACTIVE'
        )
        return subscription
    except SubscriptionPlan.DoesNotExist:
        return None


def check_employee_limit(company, exclude_user=None):
    """
    Check if company can add more employees based on subscription.
    
    Args:
        company: Company instance
        exclude_user: User to exclude from count (for updates)
    
    Returns:
        bool: True if can add employee, False otherwise
    
    Raises:
        SubscriptionLimitExceeded: If limit would be exceeded
    """
    subscription = get_company_subscription(company)
    if not subscription:
        raise SubscriptionLimitExceeded("No active subscription found")
    
    plan = subscription.plan
    if plan.max_employees == 0:  # Unlimited
        return True
    
    # Count current employees
    employee_count = company.employees.filter(is_active=True).count()
    if exclude_user:
        employee_count -= 1
    
    if employee_count >= plan.max_employees:
        raise SubscriptionLimitExceeded(
            f"Employee limit reached. Your {plan.name} plan allows up to {plan.max_employees} employees."
        )
    
    return True


def check_branch_limit(company):
    """
    Check if company can add more branches based on subscription.
    
    Args:
        company: Company instance
    
    Returns:
        bool: True if can add branch, False otherwise
    
    Raises:
        SubscriptionLimitExceeded: If limit would be exceeded
    """
    subscription = get_company_subscription(company)
    if not subscription:
        raise SubscriptionLimitExceeded("No active subscription found")
    
    plan = subscription.plan
    if plan.max_branches == 0:  # Unlimited
        return True
    
    branch_count = company.branches.filter(is_active=True).count()
    if branch_count >= plan.max_branches:
        raise SubscriptionLimitExceeded(
            f"Branch limit reached. Your {plan.name} plan allows up to {plan.max_branches} branches."
        )
    
    return True


def check_attendance_group_limit(company):
    """
    Check if company can add more attendance groups based on subscription.
    
    Args:
        company: Company instance
    
    Returns:
        bool: True if can add attendance group, False otherwise
    
    Raises:
        SubscriptionLimitExceeded: If limit would be exceeded
    """
    subscription = get_company_subscription(company)
    if not subscription:
        raise SubscriptionLimitExceeded("No active subscription found")
    
    plan = subscription.plan
    if plan.max_attendance_groups == 0:  # Unlimited
        return True
    
    group_count = company.attendance_groups.filter(is_active=True).count()
    if group_count >= plan.max_attendance_groups:
        raise SubscriptionLimitExceeded(
            f"Attendance group limit reached. Your {plan.name} plan allows up to {plan.max_attendance_groups} attendance groups."
        )
    
    return True


def check_feature_access(company, feature_name):
    """
    Check if company has access to a specific feature based on subscription.
    
    Args:
        company: Company instance
        feature_name: Feature name (e.g., 'has_advanced_reporting', 'has_api_access')
    
    Returns:
        bool: True if feature is available, False otherwise
    """
    subscription = get_company_subscription(company)
    if not subscription:
        return False
    
    return getattr(subscription.plan, feature_name, False)


def get_subscription_status_context(company):
    """
    Get subscription status context for templates.
    
    Args:
        company: Company instance
    
    Returns:
        dict: Context dictionary with subscription information
    """
    subscription = get_company_subscription(company)
    if not subscription:
        return {
            'has_subscription': False,
            'subscription_status': 'No subscription',
            'plan_name': 'No Plan',
            'days_remaining': 0,
        }
    
    plan = subscription.plan
    employee_count = company.employees.filter(is_active=True).count()
    branch_count = company.branches.filter(is_active=True).count()
    group_count = company.attendance_groups.filter(is_active=True).count()
    
    return {
        'has_subscription': True,
        'subscription': subscription,
        'plan': plan,
        'subscription_status': subscription.get_status_display(),
        'plan_name': plan.name,
        'days_remaining': subscription.days_remaining,
        'is_trial': subscription.is_trial,
        'usage': {
            'employees': {
                'current': employee_count,
                'limit': plan.max_employees,
                'unlimited': plan.max_employees == 0,
                'percentage': (employee_count / plan.max_employees * 100) if plan.max_employees > 0 else 0,
                'near_limit': employee_count >= (plan.max_employees * 0.8) if plan.max_employees > 0 else False,
            },
            'branches': {
                'current': branch_count,
                'limit': plan.max_branches,
                'unlimited': plan.max_branches == 0,
                'percentage': (branch_count / plan.max_branches * 100) if plan.max_branches > 0 else 0,
                'near_limit': branch_count >= (plan.max_branches * 0.8) if plan.max_branches > 0 else False,
            },
            'attendance_groups': {
                'current': group_count,
                'limit': plan.max_attendance_groups,
                'unlimited': plan.max_attendance_groups == 0,
                'percentage': (group_count / plan.max_attendance_groups * 100) if plan.max_attendance_groups > 0 else 0,
                'near_limit': group_count >= (plan.max_attendance_groups * 0.8) if plan.max_attendance_groups > 0 else False,
            },
        },
        'features': {
            'advanced_reporting': plan.has_advanced_reporting,
            'api_access': plan.has_api_access,
            'custom_branding': plan.has_custom_branding,
            'priority_support': plan.has_priority_support,
            'data_export': plan.has_data_export,
        }
    }


def require_subscription_feature(feature_name):
    """
    Decorator to require a specific subscription feature for view access.
    
    Args:
        feature_name: Feature name to check (e.g., 'has_advanced_reporting')
    
    Usage:
        @require_subscription_feature('has_advanced_reporting')
        def advanced_reports_view(request):
            # View logic here
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Get user's company
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if user.role == 'SUPER_ADMIN':
                return view_func(request, *args, **kwargs)
            
            if not user.company:
                raise PermissionDenied("No company associated with user")
            
            if not check_feature_access(user.company, feature_name):
                raise PermissionDenied(f"This feature requires a subscription upgrade")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def subscription_limit_check(limit_type):
    """
    Decorator to check subscription limits before allowing creation.
    
    Args:
        limit_type: Type of limit to check ('employee', 'branch', 'attendance_group')
    
    Usage:
        @subscription_limit_check('employee')
        def create_employee_view(request):
            # View logic here
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Get user's company
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if user.role == 'SUPER_ADMIN':
                return view_func(request, *args, **kwargs)
            
            if not user.company:
                raise PermissionDenied("No company associated with user")
            
            try:
                if limit_type == 'employee':
                    check_employee_limit(user.company)
                elif limit_type == 'branch':
                    check_branch_limit(user.company)
                elif limit_type == 'attendance_group':
                    check_attendance_group_limit(user.company)
                else:
                    raise ValueError(f"Unknown limit type: {limit_type}")
                
                return view_func(request, *args, **kwargs)
                
            except SubscriptionLimitExceeded as e:
                messages.error(request, str(e))
                # Redirect to subscription management page
                from django.shortcuts import redirect
                return redirect('subscriptions:manage')
                
        return wrapper
    return decorator
