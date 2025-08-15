from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('pricing/', views.pricing, name='pricing'),
    path('contact/', views.contact, name='contact'),
    
    # Subscription management
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('manage/', views.manage_subscription, name='manage'),
]
