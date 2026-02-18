from apps.subscriptions.models import CompanySubscription
from apps.companies.models import Branch
from apps.users.models import CustomUser
from apps.attendance.models import AttendanceGroup


def subscription_limits(request):
    """
    Add subscription limit data to template context for JavaScript validation
    """
    if not request.user.is_authenticated or not request.user.company:
        return {}
    
    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        plan = subscription.plan
        
        # Get current counts
        current_employees = CustomUser.objects.filter(
            company=request.user.company,
            role__in=['EMPLOYEE', 'HR_EMPLOYEE']
        ).count()
        
        current_branches = Branch.objects.filter(company=request.user.company).count()
        
        current_groups = AttendanceGroup.objects.filter(company=request.user.company).count()
        
        return {
            'subscription_limits': {
                'plan_name': plan.name,
                'current_employees': current_employees,
                'max_employees': plan.max_employees,
                'current_branches': current_branches,
                'max_branches': plan.max_branches,
                'current_groups': current_groups,
                'max_groups': plan.max_attendance_groups,
                'has_advanced_reporting': plan.has_advanced_reporting,
                'has_api_access': plan.has_api_access,
                'has_data_export': plan.has_data_export,
                'has_custom_branding': plan.has_custom_branding,
            }
        }
    except CompanySubscription.DoesNotExist:
        return {
            'subscription_limits': {
                'plan_name': 'No Plan',
                'current_employees': 0,
                'max_employees': 0,
                'current_branches': 0,
                'max_branches': 0,
                'current_groups': 0,
                'max_groups': 0,
                'has_advanced_reporting': False,
                'has_api_access': False,
                'has_data_export': False,
                'has_custom_branding': False,
            }
        }
