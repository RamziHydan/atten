from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'companies'

@login_required
def company_detail(request, company_id):
    """Placeholder company detail view"""
    return render(request, 'companies/company_detail.html', {
        'title': 'Company Details',
        'company_id': company_id
    })

urlpatterns = [
    path('company/<int:company_id>/', company_detail, name='company_detail'),
]
