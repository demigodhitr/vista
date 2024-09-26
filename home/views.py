from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from datetime import datetime
from .models import *
from app.views import signin, signup
from app.models import WalletAddress
import logging
import requests
import random
import secrets
import string
import json
logger = logging.getLogger('django')
from django.contrib.auth.decorators import login_required

def custom404(request, exception):
    return render(request, '404.html', {}, status=404)

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def get_ticket_id():
    letters = string.ascii_uppercase + string.digits
    ticket_id = ''.join(secrets.choice(letters) for i in range(10))
    while True:
        if not Enquiries.objects.filter(ticket_id=ticket_id).exists():
            return ticket_id

def contact(request):
    request.session.setdefault('contacts', 0)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        captcha = request.POST.get('g-recaptcha-response')

        if not captcha:
            return JsonResponse({'error': 'reCAPTCHA verification token is missing'}, status=500)
        
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
           'secret': settings.G_RECAPTCHA_SECRET,
           'response': captcha,
           'remoteip': request.META['REMOTE_ADDR']
        }
        try:
            call = requests.post(url, data=values)
            response = call.json()
        except requests.RequestException as e:
            return JsonResponse({'error': f'Error while verifying reCAPTCHA: {str(e)}' }, status=500)
        except ValueError as e:  
            return JsonResponse({'error': f'Error parsing reCAPTCHA response: {str(e)}'}, status=500)
        
        if not response['success']:
            return JsonResponse({'error': 'reCAPTCHA verification failed please try again'}, status=403)

        if not (name or email or subject or message):
            return JsonResponse({'error': 'All fields are required'}, status=500)
        

        if len(name) < 5:
            return JsonResponse({'error': 'Please use your full name'}, status=400)
        
        if len(message) < 60:
            return JsonResponse({'error': 'Please provide a detailed message'}, status=400)
        request.session['contacts'] += 1
        
        if request.session['contacts'] >= 3:
            return JsonResponse({'request_error': 'Too many submissions. Please try again later.'}, status=429)
        ticket_id = get_ticket_id()

        enquiry = Enquiries.objects.create(
            name=name, 
            email=email, 
            subject=subject, 
            message=message,
            ticket_id=ticket_id,
            timestamp=datetime.now()
            )
        subject = 'Your ticket has been created'
        body = f'Hello ! Thank your for contacting us at Exchange Vista. One of our team members will reach out soon. to add more information, please reply to this email. For reference, your ticket ID is <h4><strong>{ticket_id}</strong></h4>'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        email_message = EmailMultiAlternatives(subject, body, from_email, recipient_list)
        email_message.content_subtype = 'html'
        try:
            email_message.send()
        except Exception as e:
            logger.error('Error sending email', exc_info=True)
        return JsonResponse({'success': 'Your message has been sent successfully. We will get back to you soon.'}, status=200)
    return render(request, 'contact.html')

def faqs(request):
    return render(request, 'faq.html')

def pricing(request):
    return render(request, 'pricing.html')

def services(request):
    return render(request, 'services.html')

def signin(request):
    return render(request, 'signin.html')

def signup(request):
    return render(request, 'signup.html')

def team(request):
    return render(request, 'team.html')

def signals(request):
    journals = TradingJournals.objects.all()
    return render(request, 'signals.html',{'journals':journals})

def signal_detail(request, journal_id):
    journal = get_object_or_404(TradingJournals, pk=journal_id)
    journals = TradingJournals.objects.exclude(pk=journal.pk)
    file = journal.file.size
    return render(request, 'signals-detail.html', {'journal':journal, 'journals':journals})

def payment(request, journal_id):
    if not request.user.is_authenticated:
        next_url = reverse('payment', args=[journal_id])
        return redirect(f'/app/login/?next={next_url}')
    journal = get_object_or_404(TradingJournals, pk=journal_id)
    addresses = WalletAddress.objects.all()
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf8'))
        network = data['network']
        address = data['address']
        amount = journal.price
        if not (network and address):
            return JsonResponse({'error': 'Missing credentials from user'})
        payment = JournalPayments.objects.create(
            user=request.user,
            journal=journal,
            amount_paid=amount,
            payment_network=network,
            payment_address=address,
            payment_date=datetime.now(),
            payment_received=False,
            )
        payment.save()
        payment_id = payment.pk
        return JsonResponse({'success': 'Thank you for your payment...', 'pid':payment_id}, status=200)
    return render(request, 'payment.html', {'journal':journal, 'addresses':addresses})


@login_required
def check_payment(request, payment_id):
    payment = get_object_or_404(JournalPayments, pk=payment_id)
    if payment:
        if payment.payment_received:
            new_purchase = JournalPurchase.objects.create(
                user=request.user, 
                journal=payment.journal, 
                price_at_purchase=payment.journal.price,
                allowed_downloads=3
            )
            new_purchase.save()  
            return JsonResponse({'success': 'Payment received successfully...', 'purchase_id':new_purchase.pk}, status=200)
        
        else:
            return JsonResponse({'error': 'Payment not confirmed yet...'}, status=412)
    else:
        return JsonResponse({'error': 'Payment not found...'}, status=403)
    

    
@login_required  
def check_eligibility(request, purchase_id):
    purchase = get_object_or_404(JournalPurchase, pk=purchase_id)
    if purchase.allowed_downloads > 0:
        purchase.allowed_downloads -= 1
        purchase.save()
        return JsonResponse({'success': 'eligible', 'download_url':purchase.journal.file.url}, status=200)
    else:
        return JsonResponse({'error': 'Payment exhausted...'}, status=500)

@login_required
def downloads(request):
    journals = JournalPurchase.objects.filter(user=request.user)
    return render(request, 'downloads.html', {'journals':journals})
    






# Create your views here.
