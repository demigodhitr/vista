from django.urls import path
from .views import *



urlpatterns = [
    path('', home, name='web'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('faqs/', faqs, name='faqs'),
    path('pricing/', pricing, name='pricing'),
    path('services/', services, name='services'),
    path('team/', team, name='team'),
    path('signals/', signals, name='signals'),
    path('purchase/<int:journal_id>/', signal_detail, name='purchase'),
    path('payment/<int:journal_id>/', payment, name='payment'),
    path('api/check_payment/<int:payment_id>', check_payment, name='payment_status'),
    path('api/check_eligibility/<int:purchase_id>', check_eligibility, name='check_eligibility'),
    path('downloads/', downloads, name='downloads'),
]