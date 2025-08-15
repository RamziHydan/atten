from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from apps.subscriptions.models import CompanySubscription


class SubscriptionRequiredMixin:
    """
    Mixin to check subscription limits for class-based views
    """
    subscription_feature_check = None
    subscription_redirect_url = 'subscriptions:pricing'
    subscription_error_message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.check_subscription_access(request):
            return redirect(self.subscription_redirect_url)
        return super().dispatch(request, *args, **kwargs)
    
    def check_subscription_access(self, request):
        user = request.user
        
        if not user.is_authenticated:
            messages.error(request, 'Please log in to access this feature.')
            return False
        
        if not user.company:
            messages.error(request, 'You must be associated with a company.')
            return False
        
        try:
            subscription = CompanySubscription.objects.get(company=user.company)
            plan = subscription.plan
            
            # Check if subscription is active
            if subscription.status != 'ACTIVE':
                messages.warning(request, 
                    'Your subscription is not active. Please renew your subscription to access this feature.')
                return False
            
            # If no specific feature check, just verify active subscription
            if self.subscription_feature_check is None:
                return True
            
            # Run the feature check
            if not self.subscription_feature_check(plan, request):
                error_msg = self.subscription_error_message or (
                    f'This feature is not available in your current plan ({plan.name}). '
                    f'Please upgrade to access this feature.'
                )
                messages.warning(request, error_msg)
                return False
                
        except CompanySubscription.DoesNotExist:
            messages.warning(request, 
                'No active subscription found. Please subscribe to a plan to access this feature.')
            return False
        
        return True


def check_employee_limit(plan, request):
    """Check if plan allows more employees"""
    from apps.users.models import CustomUser
    current_count = CustomUser.objects.filter(
        company=request.user.company,
        role__in=['EMPLOYEE', 'HR_EMPLOYEE']
    ).count()
    
    if plan.max_employees == -1:  # Unlimited
        return True
    return current_count < plan.max_employees


def check_branch_limit(plan, request):
    """Check if plan allows more branches"""
    from apps.companies.models import Branch
    current_count = Branch.objects.filter(company=request.user.company).count()
    
    if plan.max_branches == -1:  # Unlimited
        return True
    return current_count < plan.max_branches


def check_attendance_group_limit(plan, request):
    """Check if plan allows more attendance groups"""
    from apps.attendance.models import AttendanceGroup
    current_count = AttendanceGroup.objects.filter(company=request.user.company).count()
    
    if plan.max_attendance_groups == -1:  # Unlimited
        return True
    return current_count < plan.max_attendance_groups


def check_advanced_reporting(plan, request):
    """Check if plan has advanced reporting"""
    return plan.has_advanced_reporting


def check_api_access(plan, request):
    """Check if plan has API access"""
    return plan.has_api_access


def check_data_export(plan, request):
    """Check if plan has data export"""
    return plan.has_data_export


def check_custom_branding(plan, request):
    """Check if plan has custom branding"""
    return plan.has_custom_branding
