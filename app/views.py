from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from .models import *
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError
import requests
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
import random
import json
from decimal import Decimal, ROUND_HALF_UP
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.utils.safestring import mark_safe
import secrets
import string
from itertools import chain
from operator import attrgetter
from django.db.models import F, Value, CharField
from django.db.models import Sum
from firebase_admin import messaging, credentials, initialize_app
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.cache import cache
from io import BytesIO
from PIL import Image
import requests
import logging
import os
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger('django')

cred = credentials.Certificate(settings.FIREBASE_ADMIN)
initialize_app(cred)

def fetch_exchange_rates(user):
    cache_key = 'exchange_rates'
    cache_timeout = 12 * 60 * 60

    exchange_rates = cache.get(cache_key)
    if exchange_rates:
        gbp_to_usd = exchange_rates['USD']
        gbp_to_eur = exchange_rates['EUR']
        update_user_balances(gbp_to_usd, gbp_to_eur)
        return exchange_rates
    

    api_key = settings.EXCHANGE_KEY
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/GBP'
    try:
        response = requests.get(url).json()
    except requests.ConnectionError:
        logger.error('Could not fetch the latest exchange rates: ', exc_info=True)
        return None
    if response['result'] == 'success':
        gbp_to_usd = Decimal(response['conversion_rates']['USD'])
        gbp_to_eur = Decimal(response['conversion_rates']['EUR'])

        exchange_rates = {
            'USD': gbp_to_usd,
            'EUR': gbp_to_eur,
        }
        
        # Cache the data
        cache.set(cache_key, exchange_rates, cache_timeout)

        Currencies.objects.update_or_create(
            code='USD',
            defaults={
            'exchange_rate': gbp_to_usd, 
            'name': 'US Dollar',
            'sign': '$'
            })
        Currencies.objects.update_or_create(
            code='EUR', 
            defaults={
            'exchange_rate': gbp_to_eur,
            'name': 'Euro',
            'sign': '€'
            })
        Currencies.objects.update_or_create(
            code='GBP',
            defaults={
            'exchange_rate': 1,
            'name': 'British Pound',
            'sign': '£'
        })
        update_user_balances(gbp_to_usd, gbp_to_eur)
        
        return exchange_rates

    return None

def update_user_balances(gbp_to_usd, gbp_to_eur):
    for profile in Profiles.objects.all():
        usd_balance, created = BalanceUSD.objects.get_or_create(profile=profile)
        eur_balance, created = BalanceEUR.objects.get_or_create(profile=profile)
        usd_balance.deposits = profile.deposits * gbp_to_usd
        usd_balance.bonus = profile.bonus * gbp_to_usd
        usd_balance.profits = profile.profits * gbp_to_usd
        usd_balance.save()
        eur_balance.deposits = profile.deposits * gbp_to_eur
        eur_balance.bonus = profile.bonus * gbp_to_eur
        eur_balance.profits = profile.profits * gbp_to_eur
        eur_balance.save()

def landing(request):
    return render(request, 'landing.html')

def create_referral_code():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    chars = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )
    return timestamp + chars

def get_referral_code():
    while True:
        referral_code = create_referral_code()
        if not Referrals.objects.filter(referral_id=referral_code).exists():
            return referral_code

@login_required
def index(request): 
    user = request.user
    try:
        user_profile = Profiles.objects.get(user=user)
        dp = user_profile.profile_pic.url
    except Profiles.DoesNotExist:
        logout(request)
        return redirect('login')
    except Exception as e:
        default_image_path = settings.DEFAULT_AVATAR
        with open(default_image_path, 'rb') as f:
            picture = f.read()
            user_profile = Profiles.objects.get(user=user)
            user_profile.profile_pic.save('default_avatar.png', ContentFile(picture))
            dp = user_profile.profile_pic.url
    usd_balance = BalanceUSD.objects.get(profile=user_profile)
    eur_balance = BalanceEUR.objects.get(profile=user_profile)
    cards = CryptoCards.objects.filter(user=user)
    notifications = Notifications.objects.filter(user=user, seen=False)
    withdrawals = WithdrawalRequest.objects.filter(user=user).order_by('-created_at')
    deposits = Deposits.objects.filter(user=user).order_by('-created_at')
    investments = Investments.objects.filter(investor=user).order_by('-date')
    earnings = EarningsHistory.objects.filter(user=user).order_by('-timestamp')
    total_invested = investments.aggregate(total_amount=Sum('amount'))['total_amount']
     # Handle the case where total_invested is None
    if total_invested is None:
        total_invested = Decimal('0.00')  
    else:
        total_invested = Decimal(total_invested) 
    
    # Currency conversion based on user's preferred currency
    if user_profile.preferred_currency == 'USD':
        rate = Decimal(Currencies.objects.get(code='USD').exchange_rate)
        total_invested = total_invested * rate
        total_invested = total_invested.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  
        code = Currencies.objects.get(code='USD').code
    elif user_profile.preferred_currency == 'EUR':
        rate = Decimal(Currencies.objects.get(code='EUR').exchange_rate)
        total_invested = total_invested * rate
        total_invested = total_invested.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
        code = Currencies.objects.get(code='EUR').code
    else:
        code = '£'

    card_requests = CardRequest.objects.filter(user=user).order_by('-date')
    all_activities = sorted(
        chain(
            withdrawals.annotate(activity_date=F('created_at'), activity_type=Value('Withdrawal', output_field=CharField())),
            deposits.annotate(activity_date=F('created_at'), activity_type=Value('Deposit', output_field=CharField())),
            investments.annotate(activity_date=F('date'), activity_type=Value('Investment', output_field=CharField())),
            card_requests.annotate(activity_date=F('date'), activity_type=Value('Card Request', output_field=CharField())),
            earnings.annotate(activity_date=F('timestamp'), activity_type=Value('Earnings', output_field=CharField()))
        ),
        key=attrgetter('activity_date'),
        reverse=True
    )
    cache_key = 'coins_data'
    coins_data = cache.get(cache_key)
    if not coins_data:
        key = 'CG-ijyB17U95TbbzxurdFzBKi6H'
        gecko_endpoint = 'https://api.coingecko.com/api/v3/coins/markets'
        crypto_ids = [
        "bitcoin", "ethereum", "tether", "binancecoin", "cardano",
        "solana", "ripple", "polkadot", "dogecoin", "usd-coin",
        "terra-luna", "chainlink", "bitcoin-cash", "litecoin", "matic-network",
        "stellar", "ethereum-classic", "vechain", "theta-token", "eos",
        "aave", "crypto-com-chain", "filecoin", "tron", "shiba-inu",
        "tezos", "monero", "neo", "dash", "pancakeswap-token",
        "elrond-erd-2", "compound-ether", "ethereum-classic", "ftx-token", "compound-governance-token",
        "the-sandbox", "havven", "uma", "amp"
        ]

        coins_param = {
            'vs_currency': 'GBP',
            'ids': ','.join(crypto_ids),
            'order': 'market_cap_desc',
            'sparkline': 'true',
            'price_change_percentage': '24h',
            'key': key,
        }
        try:
            gecko_response = requests.get(gecko_endpoint, params=coins_param)
        except Exception as e:
            gecko_response = None
            logger.error('Error fetching coins', exc_info=True)

        if gecko_response and gecko_response.status_code == 200:
            coins_data = gecko_response.json()
            cache.set(cache_key, coins_data, 24*60*60)  # cache for 1 hour
        else:
            coins_data = []
    context = {
        'total_invested':total_invested,
        'investments':investments,
        'cards': cards,
        'activities': all_activities,
        'notifications': notifications,
        'coins': coins_data,
        'profile': user_profile,
        'usd_balance': usd_balance,
        'eur_balance': eur_balance,
        'code':code,
        'dp': dp,
    }
    return render(request, 'index.html', context)

def signin(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        request.session.setdefault('attempts', 0)
        request.session.setdefault('counter', 4)
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if not username or not password:
            return JsonResponse({'error': 'Cannot authenticate ghost user'}, status=400)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                v_obj = is_verified.objects.get(user=user)
            except is_verified.DoesNotExist:
                email = user.email
                return JsonResponse({'verify': 'There was a problem authenticating you. perhaps, you have not verified your account email', 'email':email}, status=400)
            if not v_obj.verified:
                email = v_obj.email
                request.session.setdefault('email', email)
                return JsonResponse({'verify': f'Looks like you have not verified your email: {email}. Please verify it now to ensure you are a legitimate user.', 'email':email}, status=400)
            else:
                user_profile = Profiles.objects.get(user=user)
                if not user_profile.can_login:
                    return JsonResponse({'error': 'Your account has been found to be in violation of our terms of use.Please contact our support team for assistance.'})
                else:
                    request.session.clear()
                    login(request, user)
                    return JsonResponse({'success': 'Fetching your account balances, please wait...'}, status=200)
        else:
            request.session['attempts'] += 1
            request.session['counter'] -= 1
            if request.session['attempts'] >= 4:
                try:
                    user = CustomUser.objects.get(username=username)
                    profile = Profiles.objects.get(user=user)
                    profile.can_login = False
                    profile.save()
                    request.session.setdefault('risky', True)
                    return JsonResponse({'error': 'Maximum attempts exceeded, your account has been disabled. Please contact support for help.', 'disable': 'true'}, status=400)
                except CustomUser.DoesNotExist:
                    request.session.setdefault('risky', True)
                    return JsonResponse({'error': f'Invalid username or password. Further requests will no longer be processed until after some time.', 'disable': 'true'}, status=403)
                except Profiles.DoesNotExist:
                    user.delete()
                    return JsonResponse({'error': 'You do not have a profile instance. Perhaps, you\'re not a regisered user, Please restart your registration'}, status=403)
                
            else: 
                counter = request.session['counter']
                return JsonResponse({'error': f'Incorrect username or password. You have {counter} more attempts left.'}, status=400)
            
    risky = request.session.get('risky', None)
    if risky:
        request.session.setdefault('clear_session', 0)
        request.session['clear_session'] += 1
        if request.session['clear_session'] >= 5:
            request.session.clear()
            return render(request, 'login.html')
        return render(request, 'login.html', {'disable': True})
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname', None)
        lastname = request.POST.get('lastname', None)
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        picture = request.FILES.get('picture', None)
        password1 = request.POST.get('password1', None)
        password2 = request.POST.get('password2', None)
        consent = request.POST.get('consent', None)
        nationality = request.POST.get('nationality', None)
        referrer_code = request.POST.get('referral', None)
        if not (firstname and lastname and username and email and password1 and password2 and picture and consent and nationality):
            return JsonResponse({'error': 'Required field is missing'}, status=400)
        
        if password1 != password2:
            return JsonResponse({'error': 'Password mismatch'}, status=400)
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username used. perhaps you want to log in?'}, status=400)
        
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'error': ' email already used, perhaps you want to log in?'}, status=400)
        
        user = CustomUser.objects.create_user(username=username, email=email, password=password1, firstname=firstname, lastname=lastname)
        user.save()
        profile= Profiles.objects.create(user=user, nationality=nationality, profile_pic=picture,)
        
        MinimumDeposit.objects.create(user=user, amount=500)
        generated_code = get_referral_code()
        Referrals.objects.create(user=user, referral_id=generated_code)
        if referrer_code is not None:
            try:
                referrer = Referrals.objects.get(referral_id=referrer_code)
                referrer.referrals.add(user)
                profile.bonus += Decimal('100.40')
                profile.save()
                referrer.save()
                referrer_profile = Profiles.objects.get(user=referrer.user)
                referrer_profile.bonus += Decimal('100.50')
                referrer_profile.save()
                title = f'You received a bonus for referring {firstname} {lastname}!'
                message = f'{firstname} {lastname} just registered at Vista using your referral code. You\'ve been rewarded with 100.50 bonus for your referral to our platform. We say thank you for your referral and we really appreciate good deeds like this, continue referring investors to earn more bonus and unlock more oppurtunities that awaits you!'
                Notifications.objects.create(user=referrer.user, title=title, message=message)      
            except Referrals.DoesNotExist:
                Notifications.objects.create(
                    user=user,
                    title='Referrer does not exist',
                    message='The referral code you provided does not belong to a registered user within our platform. As a result of this, we could not correctly give you the full referree benefits.'
                )
                pass
            except Profiles.DoesNotExist:
                return JsonResponse({'error': 'Misconfiguration, please check and try again'})
        request.session.setdefault('email', email)
        return JsonResponse({'verify':f'Now, simply verify {email} to continue to your account.', 'email':email})
    ref = request.session.get('id', None)
    return render(request, 'register.html', {'ref':ref})

def register_as_referred(request, id):
    request.session.setdefault('id', id)
    return redirect('register')

def facebook_login(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        token = data['token']
        nationality = data['nationality']
        if not (token and nationality):
            return JsonResponse({'error': 'Missing token or nationality'}, status=403)
        
        url = f"https://graph.facebook.com/me?fields=id,name,first_name,last_name,picture&access_token={token}"
        response = requests.get(url)
        data = response.json()

        if 'email' in data:
            email = data['email']
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            facebook_id = data.get('id')
            picture = data.get('picture', None)
            try:
                user = CustomUser.objects.get(email=email)
                profile = Profiles.objects.get(user=user)
                if profile.can_login:
                    user.username = f'fb-{facebook_id}'
                    user.save()
                    login(request, user)
                    print('Login successful')
                    return JsonResponse({'success': 'User successfully authenticated'})
                else:
                    return JsonResponse({'disabled': 'Your account has been locked. Please contact support.'})
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    username= f'fb-{facebook_id}',
                    email=email,
                    firstname=first_name,
                    lastname=last_name,
                )
                profile = Profiles.objects.create(
                    user=user, 
                    nationality=nationality
                )
                referral_ID = get_referral_code()
                Referrals.objects.create(user=user, referral_id=referral_ID)
                MinimumDeposit.objects.create(user=user, amount=500)   
                if picture:
                    try:
                        response = requests.get(picture)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            with NamedTemporaryFile() as temp_image:
                                img.save(temp_image, format=img.format)
                                temp_image.flush()
                                temp_image.seek(0)  
                                profile_pic_format = img.format.lower()
                                profile_pic_name = f'{facebook_id}.{profile_pic_format}'
                                profile.profile_pic.save(profile_pic_name, ContentFile(temp_image.read()), save=True)
                        else:
                            print('Failed to download image')
                    except Exception as e:
                        logger.exception(f"Failed to download or save profile picture: {e}")
                        default_image_path = settings.DEFAULT_AVATAR
                        with open(default_image_path, 'rb') as f:
                            profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
                else:
                    default_image_path = settings.DEFAULT_AVATAR
                    with open(default_image_path, 'rb') as f:
                        profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)

                referral_ID = get_referral_code()
                Referrals.objects.create(user=user, referral_id=referral_ID)

            profile.save()
            login(request, user)
            return JsonResponse({'success': True, 'redirect_url': 'home'}, status=200)
        else:
            return JsonResponse({'error': 'Invalid token'})
        
    return JsonResponse({'error': 'Invalid request'}, status=500)

def google_login(request):
    if request.method == 'POST':
        print('post received')
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        picture_url = data.get('picture', None)
        google_id = data.get('sub')
        nationality = data.get('nationality')

        if not(email and firstname and lastname and picture_url and google_id):
            return JsonResponse({'error': 'Missing google credentials'}) 
        try:
            user = CustomUser.objects.get(email=email)
            profile = Profiles.objects.get(user=user)
            if profile.can_login:
                user.username = f'{user.firstname}-{google_id}'
                user.save()
                login(request, user)
                print('Login successful')
                return JsonResponse({'success': 'User authenticated','redirect_url': 'home'})
            else:
                return JsonResponse({'disabled': 'Your account has been locked. Please contact support.'})
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(
                username= f'{firstname}-{google_id}',
                email=email,
                firstname=firstname,
                lastname=lastname,
            )
            profile = Profiles.objects.create(
                user=user, 
                nationality=nationality
            )
            referral_ID = get_referral_code()
            Referrals.objects.create(user=user, referral_id=referral_ID)
            MinimumDeposit.objects.create(user=user, amount=500)   
            if picture_url:
                try:
                    response = requests.get(picture_url)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        with NamedTemporaryFile() as temp_image:
                            img.save(temp_image, format=img.format)
                            temp_image.flush()
                            temp_image.seek(0)  # Go back to the start of the file
                            profile_pic_format = img.format.lower()
                            profile_pic_name = f'{google_id}.{profile_pic_format}'
                            profile.profile_pic.save(profile_pic_name, ContentFile(temp_image.read()), save=True)
                    else:
                        print('Failed to download image')
                except Exception as e:
                    logger.exception(f"Failed to download or save profile picture: {e}")
                    default_image_path = settings.DEFAULT_AVATAR
                    with open(default_image_path, 'rb') as f:
                        profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
            else:
                default_image_path = settings.DEFAULT_AVATAR
                with open(default_image_path, 'rb') as f:
                    profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
        profile.save()
        login(request, user)
        return JsonResponse({'success': True, 'redirect_url': 'home'})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
def profile_completion_view(request):
    if not request.session['socialaccount_new_user']:
        return redirect('home')
    if request.method == 'POST':
        try:
            picture = request.FILES.get('picture')
            nationality = request.POST.get('nationality', '')
            profile, created = Profiles.objects.get_or_create(user=request.user)
            profile.profile_pic = picture
            profile.nationality = nationality
            profile.can_login = True
            profile.save()
            return JsonResponse({'success': 'Your profile has been completed successfully'})
        except Exception as e:
            return JsonResponse({'error': 'Some error occurred... ' + str(e)})
    return render(request, 'profile_completion.html')

@login_required
def authorize(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = Profiles.objects.get(user=user)
            data = json.loads(request.body.decode('utf-8'))
            pin = data['pin']
            if not pin:
                return JsonResponse({'error': 'Missing PIN'}, status=400)
            if pin != profile.pin:
                return JsonResponse({'error': 'Your PIN is incorrect'}, status=401)
            else:
                return JsonResponse({'success': 'Authorization successful'}, status=200)
        except Exception as e:
            return JsonResponse({'error': 'Some error occurred... '+ str(e)}, status=403)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=500)

@login_required
def fund_card(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = Profiles.objects.get(user=user)
            card = CryptoCards.objects.filter(user=user).first()
            data = json.loads(request.body.decode('utf-8'))
            if not data['account'] or not data['amount']:
                return JsonResponse({'error': 'Missing Credentials'}, status=400)
            account_value = data['account']
            amount = Decimal(data['amount'])
            if amount < Decimal('100'):
                return JsonResponse({'error': 'The minimum amount you can fund your card with is £100.00'},  status=400)
            if account_value == 'deposit':
                profile.deposits -= amount
                if profile.deposits < Decimal('100'):
                    return JsonResponse({'error': f'Insufficient funds. Please top up your deposit account to continue'}, status=400)
            elif account_value == 'profits':
                profile.profits -= amount
                if profile.profits < Decimal('100'):
                    return JsonResponse({'error': f'Insufficient funds. Please top up your profits account to continue'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid account'}, status=403)
            
            profile.save()
            card.available_amount += amount
            card.save()
            activity = Activities.objects.create(
                user=user,
                activity_type='Card Funding',
                activity_value=amount,
                activity_description=f"Funded card: {card.card_number} with £{amount} from {account_value} account.",
            )
            activity.save()
            return JsonResponse({'success': 'You have successfully funded your card', 'amount': amount}, status=200)
        except Exception as e:
            logger.exception(f'An error occurred while funding {user.username}\'s card: ' + str(e))
            return JsonResponse({'error': 'Failed to fund card, '+ str(e)}, status=403)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=500)

@login_required
def offload_card(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = Profiles.objects.get(user=user)
            card = CryptoCards.objects.filter(user=user).first()
            data = json.loads(request.body.decode('utf-8'))
            if not data['account'] or not data['amount']:
                return JsonResponse({'error': 'Missing Credentials'}, status=400)
            
            account_value = data['account']
            amount = Decimal(data['amount'])

            card.available_amount -= amount

            if card.available_amount < 0:
                return JsonResponse({'error': 'Insufficient funds to offload. Please top up your card to continue'}, status=400)
            if account_value == 'deposit':
                profile.deposits += amount
            elif account_value == 'profits':
                profile.profits += amount
            else:
                return JsonResponse({'error': 'Invalid account'}, status=400)
            card.save()
            profile.save()
            activity = Activities.objects.create(
                user=user,
                activity_type='Card Offload',
                activity_value=amount,
                activity_description=f"Offloaded card: {card.card_number} with £{amount} and credited to {account_value} account.",
            )
            activity.save()
            return JsonResponse({'success': 'You have successfully offloaded your card', 'amount': amount}, status=200)
        except Exception as e:
            logger.exception(f'An error occurred while offloading {user.username}\'s card: ' + str(e))
            return JsonResponse({'error': 'Failed to offload card, '+ str(e)}, status=403)

@login_required
def toggle_card(request):
    if request.method == 'POST':
        try:
            user = request.user
            data = json.loads(request.body.decode('utf-8'))
            status = data['status']
            if not status or not status in ['activate', 'deactivate']:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            card = CryptoCards.objects.filter(user=user).first()
            if status == 'activate':
                card.card_status = 'Activated'
            elif status == 'deactivate':
                card.card_status = 'Blocked'
            
            card.save()
            return JsonResponse({'success': f'Your card is now {card.card_status}'})
        except Exception as e:
            logger.exception(f'An error occurred while updating {user.username}\'s card status: ' + str(e))
            return JsonResponse({'error': 'Failed to update card status, '+ str(e)}, status=403)

@login_required
def delete_user_card(request):
    try:
        user = request.user
        card = CryptoCards.objects.filter(user=user).first()
        if card:
            if card.available_amount > Decimal('1.00'):
                return JsonResponse({'error': 'Please offload your card to 0.00 then try again.'},status=400)
            
            activity = Activities.objects.create(
                user=user,
                activity_type='Card Deletion',
                activity_description=f"Deleted card: {card.card_number}.")
            activity.save()
            card.delete()
            return JsonResponse({'success': 'Your card has been deleted. You may not be able to withdraw or use some of our services without a transaction card. You can request a new transaction card by clicking the generic card'}, status=200)
        return JsonResponse({'error': 'No transaction card found for this user'}, status=404)
    except Exception as e:
        logger.exception(f'An error occurred while deleting {user.username}\'s card: ' + str(e))
        return JsonResponse({'error': 'Failed to delete card, '+ str(e)}, status=403)

def get_code(request, email):   
    try:
        user = CustomUser.objects.get(email=email)
        verification_code = random.randint(100000, 999999)
        object, created = is_verified.objects.get_or_create(user=user, defaults={
            'email': email,
            'verified': False,
            'verification_code': verification_code
        })
             
        object.verified = False
        object.verification_code = verification_code
        object.email = email
        object.creation_time = timezone.now()
        object.save()

        subject = 'Verify your account'
        body = f'You just requested for a verification code to your Email address: {email}. please enter this code <h4 style="border: 1px solid yellow;"><strong> {verification_code} </strong></h4> To continue.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        email_message = EmailMultiAlternatives(subject, body, from_email, recipient_list)
        email_message.content_subtype = 'html'
        try:
            email_message.send()
        except Exception as e:
            return JsonResponse({'error': 'There was a problem sending the verification code. Please try again later.'})
        return JsonResponse({'success': f"verification code has been sent to {email}"})
    except CustomUser.DoesNotExist:
       return JsonResponse({'success': "You will get a verification code if your email is registered"})

def verify_email(request):
    request.session.setdefault('verification_trials', 0)
    if request.method == 'POST':
        request.session['verification_trials'] +=1
        if request.session['verification_trials'] == 4:
            return JsonResponse({'error': "Multiple verification requests received within a short period of time, please slow down. ", 'disable': True})
        
        loads = request.body.decode('utf-8')
        data = json.loads(loads)
        email = data['email']
        code = data['code']
        if not code:
            return JsonResponse({'error': 'Please submit the verification code sent to your registered account email.'}, status=403)
        try:
            verified_object = is_verified.objects.get(email=email, verification_code=code)
        except is_verified.DoesNotExist:
            return JsonResponse({'error': 'Invalid verification code'}, status=404)

        currentTime = timezone.now()
        timeoutDuration = timedelta(minutes=15)
        if currentTime - verified_object.creation_time > timeoutDuration:
            return JsonResponse({'error': 'Verification code expired. Please get a new code'}, status=415)

        verified_object.verified = True
        verified_object.account_verified = False
        verified_object.verification_code = 0
        verified_object.save()

        user = verified_object.user
        login(request, user)
        request.session['email'] = ''
        return JsonResponse({'success': 'Email verified successfully, fetching your account...'}, status=200)
    
    return JsonResponse({'error': 'Invalid request method'}, status=403)

@login_required
def verify_account(request):
    request.session.setdefault('verification_trials', 0)
    if request.method == 'POST':
        request.session['verification_trials'] +=1
        if request.session['verification_trials'] == 4:
            return JsonResponse({'error': "Multiple verification requests received within a short period of time, please slow down. ", 'disable': True})
        
        loads = request.body.decode('utf-8')
        data = json.loads(loads)
        email = data['email']
        code = data['code']
        if not code:
            return JsonResponse({'error': 'Please submit the verification code sent to your registered account email.'}, status=403)
        
        try:
            verified_object = is_verified.objects.get(email=email, verification_code=code)
        except is_verified.DoesNotExist:
            return JsonResponse({'error': 'Invalid verification code'}, status=404)

        currentTime = timezone.now()
        timeoutDuration = timedelta(minutes=15)
        if currentTime - verified_object.creation_time > timeoutDuration:
            return JsonResponse({'error': 'Verification code expired. Please get a new code'}, status=415)

        verified_object.verified = True
        verified_object.account_verified = True
        verified_object.verification_code = 0
        verified_object.save()

        user = verified_object.user
        login(request, user)
        request.session['email'] = ''
        return JsonResponse({'success': 'Email verified successfully, fetching your account...'}, status=200)
    
    return JsonResponse({'error': 'Invalid request method'}, status=403)

def email_verification(request, email):
    return render(request, 'verify-email.html', email)

def logout_user(request):
    logout(request)
    # return render(request, 'logout.html')
    return redirect('login')



@login_required
def cards(request):
    user = request.user
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    notifications = Notifications.objects.filter(user=user, seen=False)
    cards = CryptoCards.objects.filter(user=user)
    activities = Activities.objects.filter(user=user).order_by('-date')
    card_requests = CardRequest.objects.filter(user=user).order_by('-date')


    context = {
        'user': user,
        'profile': profile,
        'dp': dp,
        'notifications': notifications,
        'cards': cards,
        'activities': activities
    }
    return render(request, 'cards.html', context)


def contact(request):
    return render(request, 'contact.html')

def error(request):
    return render(request, 'error.html')


def exchange(request):
    return render(request, 'exchange.html')


def forgot_password(request):
    return render(request, 'forgot-password.html')

@login_required
def help_center(request):
    notifications = Notifications.objects.filter(user=request.user, seen=False)
    try:
        profile = Profiles.objects.get(user=request.user)
        dp = profile.profile_pic.url
    except Profiles.DoesNotExist:
        dp = None
    return render(request, 'help-center.html', {'notifications': notifications, 'dp': dp})

@login_required
def markets(request):
    user = request.user
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    notifications = Notifications.objects.filter(user=user, seen=False)

    cache_key = 'coins'
    coins_data = cache.get(cache_key)
    if not coins_data:
        key = 'CG-ijyB17U95TbbzxurdFzBKi6H'
        gecko_endpoint = 'https://api.coingecko.com/api/v3/coins/markets'     
        crypto_ids = [
            "bitcoin", "ethereum", "tether", "binancecoin", "cardano",
            "solana", "ripple", "polkadot", "dogecoin", "usd-coin",
            "terra-luna", "chainlink", "bitcoin-cash", "litecoin", "matic-network",
            "stellar", "ethereum-classic", "vechain", "theta-token", "eos",
            "aave", "crypto-com-chain", "filecoin", "tron", "shiba-inu",
            "tezos", "monero", "neo", "dash", "pancakeswap-token",
            "elrond-erd-2", "compound-ether", "ftx-token", "compound-governance-token",
            "the-sandbox", "havven", "uma", "amp", "uniswap", "wrapped-bitcoin",
            "zcash", "maker", "harmony", "huobi-token", "arweave", "okb",
            "helium", "convex-finance", "thorchain", "enjincoin", "kusama",
            "flow", "chiliz", "sushi", "huobi-btc", "waves", "safemoon",
            "paxos-standard", "thorchain", "celsius-degree-token", "quant-network",
            "blockstack", "synthetix-network-token", "zcash", "decentraland",
            "yearn-finance", "ravencoin", "basic-attention-token", "bitcoin-sv",
            "holo", "hedera-hashgraph", "iotex", "icon", "nem", "arweave",
            "qtum", "bittorrent-2", "ocean-protocol", "zilliqa", "wax", "revain",
            "siacoin", "iotex", "loopring", "celo", "perpetual-protocol",
            "digibyte", "nexo", "livepeer", "0x", "nervos-network", "nano",
            "ren", "fetch-ai", "curve-dao-token", "reserve-rights-token",
            "holotoken", "ontology", "singularitynet", "stormx", "injective-protocol",
            "band-protocol", "bancor", "civic", "funfair", "dent"
        ]
        if profile.preferred_currency == "USD":
            currency = 'USD'
        elif profile.preferred_currency == "EUR":
            currency = 'EUR'
        else:
            currency = 'GBP'   
        coins_param = {
            'vs_currency': currency,
            'ids': ','.join(crypto_ids),
            'order': 'market_cap_desc',
            'sparkline': 'true',
            'price_change_percentage': '24h',
            'key': key,
        }
        try:
            gecko_response = requests.get(gecko_endpoint, params=coins_param)
        except Exception as e:
            gecko_response = None

        if gecko_response and gecko_response.status_code == 200:
            coins_data = gecko_response.json()
            cache.set(cache_key, coins_data, timeout=24*60*60)  
        else:
            coins_data = []

    context = {
        'user': user,
        'profile': profile,
        'dp': dp,
        'coins': coins_data,
        'notifications': notifications,
        'notifications_count': notifications.count()
    }
    return render(request, 'markets.html', context)

def news_details(request):
    return render(request, 'news-details.html')

def news(request):
    return render(request, 'news.html')

@login_required
def notifications(request):
    user = request.user 
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    notifications = Notifications.objects.filter(user=user).order_by('-created_at')
    context = {
        'user': user,
        'profile': profile,
        'dp': dp,
        'notifications': notifications
    }
    return render(request, 'notifications.html', context)

@login_required
def get_details(request, id):
    user = request.user
    try:
        notification = Notifications.objects.get(pk=id)
        notification.seen = True
        notification.save()
    except Notifications.DoesNotExist:
        return JsonResponse({'error': 'Notification does not exist'}, status=404)
    print('Returning data...')
    return JsonResponse({'success': 'Notification marked as read', 'title': notification.title, 'body': notification.message}, status=200)   

@login_required
def success(request):
    return render(request, 'order-successful.html')

def pages(request):
    return render(request, 'pages.html')

@login_required
def profile(request):
    session_id = request.session.get('session_id', None)
    if not session_id:
        session_id = generate_reference(10)
        request.session.setdefault('session_id', session_id)
    else:
        session_id = session_id 
    user = request.user
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    investments = Investments.objects.filter(investor=user)
    notifications = Notifications.objects.filter(user=user, seen=False)
    referrals = user.referrals.referrals.all()
    referred_users = [r.username for r in referrals]
    total_invested = investments.aggregate(total_amount=Sum('amount'))['total_amount']
    usd_balance = BalanceUSD.objects.get(profile=profile)
    eur_balance = BalanceEUR.objects.get(profile=profile)
    if total_invested is None:
        total_invested = 0.00
    else:
        total_invested = float(total_invested)
    
    context = {
        'user': user,
        'profile': profile,
        'dp': dp,
        'session': session_id,
        'total_invested': total_invested,
        'usd_balance': usd_balance,
        'eur_balance': eur_balance,
        'notifications': notifications,
        'notifications_count': notifications.count(),
        'referrals': referred_users
    }
    if request.method == 'POST':
        user = request.user
        user_details = CustomUser.objects.get(pk=user.pk)
        user_profile= Profiles.objects.get(user=user)
        username = request.POST.get('username')
        pic = request.FILES.get('dp')
        old_password = request.POST.get('old-password', None)
        new_password1 = request.POST.get('new-password1', None)
        new_password2 = request.POST.get('new-password2', None)

        if username or pic or new_password1:
            if username:
                if not old_password:
                    messages.error(request, 'To change your username, You must provide your existing password.')
                    return render(request, 'profile.html', context)
                if not user_details.check_password(old_password):
                    messages.error(request, 'Old password is incorrect')
                    return render(request, 'profile.html', context)
                
                if len(username) < 7:
                    messages.error(request, 'Choose a longer username without spaces')
                    return render(request, 'profile.html', context)
                
                if username == user.username:
                    messages.error(request, 'You\'re already using this username')
                    return render(request, 'profile.html', context)
                if CustomUser.objects.filter(username=username).exists():
                    messages.error(request, 'Username already taken')
                    return render(request, 'profile.html', context)
                user_details.username = username
                title = 'Username changed'
                message = f'Your username has been changed to {username}. If you did not change your username, please contact support team immediately.'
                Notifications.objects.create(user=user, title=title, message=message, seen=False)

            if pic:
                user_profile.profile_pic = pic

            if new_password1 or new_password2:
                if not old_password:
                    messages.error(request, 'To change your password, You must provide your existing password.')
                    return render(request, 'profile.html', context)
                
                if new_password1 != new_password2:
                    messages.error(request, 'New passwords do not match',)
                    return render(request, 'profile.html', context)
                
                request.session.setdefault('update_password', True)
                request.session.setdefault('password_attempt', 0)
                if not user_details.check_password(old_password):
                    request.session['password_attempt'] += 1
                    if request.session['password_attempt'] >= 5:
                        request.session['update_password'] = False
                        messages.error(request, 'You can no longer change your password. please try again later')
                        return render(request, 'profile.html', context)               
                    messages.error(request, 'Old password is incorrect')
                    return render(request, 'profile.html', context)
                
                if len(new_password1) < 6:
                    messages.error(request, 'Password must be at least 6 characters long', extra_tags='profile')
                    return render(request, 'profile.html', context)
                
                
                if not request.session['update_password']:
                    messages.error(request, 'You cannot change your password because of multiple failed attempts. Please try again later')
                    return render(request, 'profile.html', context)
                
                user_details.set_password(new_password1)
                user_details.save()

            user_details.save()
            user_profile.save()
            messages.success(request, 'Changes saved')
            return render(request, 'profile.html', context)
        else:
            messages.error(request, 'No changes made')
            return render(request, 'profile.html', context)
                   
    return render(request, 'profile.html', context)

def email_verification(request, email):
    return render(request, 'email-verification.html', {'email': email})

def register(request):
    return render(request, 'register.html')

@login_required
def prefs(request):
    notifications = Notifications.objects.filter(user=request.user, seen=False)
    return render(request, 'settings.html', {'notifications': notifications})

@login_required
def update_prefs(request):
    if not request.method == 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    code = data['code']
    if not code:
        return JsonResponse({'error': 'Missing param [code]'}, status=400)
    user = request.user
    profile = Profiles.objects.get(user=user)
    profile.preferred_currency = code
    profile.save()
    return JsonResponse({'success': f'Your primary currency have been changed to {code}' }, status=200)

@login_required
def email_prefs(request):
    if not request.method == 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    pref = data['pref']
    if not pref:
        return JsonResponse({'error': 'Missing param [pref]'}, status=400)
    user = request.user
    profile = Profiles.objects.get(user=user)
    profile.email_alerts = True if pref == 'true' else False
    profile.save()
    return JsonResponse({'success': f'Email alerts have been turned {"on" if pref == "true" else "off"}' }, status=200)

@login_required
def tradingview(request, coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true&sparkline=true"
    headers = {
        "accept": "application/json",
        "x-cg-api-key": "CG-wsrubTnsaQakvY2oCJNFEyhh"
    }
    response = requests.get(url, headers=headers)
    if response and response.status_code == 200:
        data = response.json()
        symbol = data["symbol"]
        market_data = data["market_data"]
        current_price = market_data["current_price"]
        amount = current_price['gbp']
        price_change_24h = market_data["price_change_24h_in_currency"]
        change = price_change_24h['gbp']
        high_24h = market_data["high_24h"]
        high_24h_gbp = high_24h['gbp']
        change_percentage = market_data['price_change_percentage_24h']    
    else:
        data = []
    notifications = Notifications.objects.filter(user=request.user, seen=False)
    context = {
        'data': data,
        'amount': amount,
        'change': change,
        'high': high_24h_gbp,
        'percentage': change_percentage,
        'symbol': symbol,
        'notifications': notifications,
        }
    return render(request, 'tradingview.html', context)

@login_required
def wallet(request):
    user = request.user
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    notifications = Notifications.objects.filter(user=user, seen=False).order_by('-created_at')
    history = Deposits.objects.filter(user=user)
    addresses = WalletAddress.objects.all()
    balanceEUR = BalanceEUR.objects.get(profile=profile)
    balanceUSD = BalanceUSD.objects.get(profile=profile)

    withdrawals = WithdrawalRequest.objects.filter(user=user).order_by('-created_at')
    deposits = Deposits.objects.filter(user=user).order_by('-created_at')
    investments = Investments.objects.filter(investor=user).order_by('-date')
    earnings = EarningsHistory.objects.filter(user=user).order_by('-timestamp')
    card_requests = CardRequest.objects.filter(user=user).order_by('-date')
    total_invested = investments.aggregate(total_amount=Sum('amount'))['total_amount']
    if total_invested is None:
        total_invested = 0.00
    else:
        total_invested = float(total_invested)

    all_activities = sorted(
        chain(
            withdrawals.annotate(activity_date=F('created_at'), activity_type=Value('Withdrawal', output_field=CharField())),
            deposits.annotate(activity_date=F('created_at'), activity_type=Value('Deposit', output_field=CharField())),
            investments.annotate(activity_date=F('date'), activity_type=Value('Investment', output_field=CharField())),
            card_requests.annotate(activity_date=F('date'), activity_type=Value('Card Request', output_field=CharField())),
            earnings.annotate(activity_date=F('timestamp'), activity_type=Value('Earnings', output_field=CharField()))
            
        ),
        key=attrgetter('activity_date'),
        reverse=True
    )

    context = {
        'user': user,
        'profile': profile,
        'notifications': notifications,
        'history': history,
        'activities': all_activities,
        'addresses': addresses,
        'balanceEUR': balanceEUR,
        'balanceUSD': balanceUSD,
        'dp':dp
    }

    return render(request, 'wallet.html', context)

@login_required
def withdraw(request):
    user = request.user 
    cards = CryptoCards.objects.filter(user=user) 
    notifications = Notifications.objects.filter(user=user, seen=False).order_by('-created_at')
    profile = Profiles.objects.get(user=user)
    dp = profile.profile_pic.url
    if profile.preferred_currency == 'USD':
        ex_obj = Currencies.objects.get(code='USD')
        exchange_rate = ex_obj.exchange_rate
        min_withd = profile.withdrawal_limit * ex_obj.exchange_rate
    elif profile.preferred_currency == 'EUR':
        ex_obj = Currencies.objects.get(code='EUR')
        exchange_rate = ex_obj.exchange_rate
        min_withd = profile.withdrawal_limit * ex_obj.exchange_rate
    else:
        exchange_rate = None
        min_withd = profile.withdrawal_limit

    min_withd = float(min_withd)
    context = {
        'user': user,
        'min_withd': min_withd,
        'exchange_rate': exchange_rate,
        'cards': cards,
        'notifications': notifications,
        'profile': profile,
        'dp':dp
    }
    return render(request, 'withdraw.html', context)

    # GET REQUEST IDs

def generate_reference(length):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


@login_required
def withdrawal(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=403)
    user = request.user
    request.session.setdefault('withdrawal_attempts', 0)
    request.session.setdefault('withdrawal_counter', 3)
    UserDetails = Profiles.objects.get(user=user)
    UserInfo = CustomUser.objects.get(pk=user.pk)
    cards = CryptoCards.objects.filter(user=user)
    cards_count = cards.count()
    card_status = cards.first() 

    address = request.POST.get('address')
    network = request.POST.get('network')
    source = request.POST.get('source')
    payfrom = request.POST.get('card')
    amount = request.POST.get('amount')
    pin = request.POST.get('pin')
    request_id = generate_reference(25)
    if not(source and payfrom and network and pin):
        return JsonResponse({'error':'Please check for any required field that is still empty.'})
    
    if source != 'everything' and not amount:
        return JsonResponse({'error': 'Please enter the amount to withdraw'})
    
    if not UserDetails.can_withraw:
        return JsonResponse({'error': "You're not eligible for withdrawal at this moment. Try again later."})
    
    pin = int(pin)
    if source == 'everything':
        amount = UserDetails.profits + UserDetails.deposits + UserDetails.bonus
    else:
        amount = Decimal(amount)

    if pin != UserDetails.pin:
        request.session['withdrawal_attempts'] += 1
        request.session['withdrawal_counter'] -= 1
        counter = request.session['withdrawal_counter']
        if request.session['withdrawal_attempts'] >= 3:
            UserDetails.can_withraw =  False
            UserDetails.save()
            request.session['withdrawal_attempts'] = 0
            request.session['withdrawal_counter'] = 3
            return JsonResponse({'error': 'You can no longer access this function. Please contact support for help.', 'blocked': True})
        return JsonResponse({'error': f'Incorrect authorization pin. You have {counter} attempts left. Please try again.'})
    
    
    if WithdrawalRequest.objects.filter(user=user, status__in=['Under review', 'Processing']).exists():
        return JsonResponse({'error': 'You already have a pending withdrawal request under review or processing. Please wait until it is processed before making another request.'})

    if UserDetails.trade_status == 'Active':
        return JsonResponse({'error': "You cannot make withdrawals when you have an active investment. Please wait until your trade is completed."})


    if cards_count == 0:
        return JsonResponse({'error': 'Please activate at least one transaction card on your account to process your request.'})
    
    if card_status.card_status == 'Blocked':
        return JsonResponse({'error': 'Your transaction card is blocked. Please contact your administrator'})
    
    if card_status.card_status == 'Not activated':
        return JsonResponse({'error': 'Your transaction card is not activated. Thus, withdrawal cannot be processed'})
    
    withdrawal_limit = Decimal(UserDetails.withdrawal_limit)
    amount = Decimal(amount)
    if amount < withdrawal_limit:
        return JsonResponse({'error': f"You requested to withdraw less than your withdraw limit. your trading account lotsize is currently high.Try withdrawing a minimum of £{UserDetails.withdrawal_limit}"})
    
    
    if  UserDetails.verification_status == "Under review":
        return JsonResponse({'error': 'Your verification is still under review. please try again later'})
        

    if UserDetails.verification_status == "Awaiting" or UserDetails.verification_status == "Failed":     
        status = 'Verification Required'
        subject = 'Please verify your account!'
        context = {'user': user, 'amount': amount, 'address': address, 'request_id':generate_reference(25), 'network':network, 'status':status}
        html_message = render_to_string('verification_email.html', context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        email = EmailMultiAlternatives(subject, plain_message, from_email,  recipient_list)
        email.attach_alternative(html_message, "text/html")
        email.send()
        return JsonResponse({'verify': 'Withdrawals are restricted to verified users only. Please verify your account to continue'})   

    tracker = BalanceTracker.objects.create(
        user=user,
        last_deposit=UserDetails.deposits,
        last_profits=UserDetails.profits,
        last_bonus=UserDetails.bonus,
    )

    if source == 'profit':
        amount = Decimal(amount)
        if amount > UserDetails.profits:
            return JsonResponse({'error': 'Insufficient profits for withdrawal.'})
        UserDetails.profits -= amount

    elif source == 'bonus':
        amount = Decimal(amount)
        if amount > UserDetails.bonus:
            return JsonResponse({'error': 'Insufficient bonus for withdrawal.'})
        UserDetails.bonus -= amount

    elif source == 'deposit':
        amount = Decimal(amount)
        if amount > UserDetails.deposits:
            return JsonResponse({'error': 'Insufficient deposits for withdrawal'})
        UserDetails.deposits -= amount

    elif source == 'everything':
        amount = Decimal(UserDetails.deposits + UserDetails.profits + UserDetails.bonus)
        UserDetails.deposits = 0.00
        UserDetails.bonus = 0.00
        UserDetails.profits = 0.00
    UserDetails.save()

    withdrawal_request = WithdrawalRequest(
        user=user,
        network=network,
        address=address,
        amount=amount,
        status='Under review',
        RequestID=request_id)
    withdrawal_request.save()

    # Update the balance tracker after the withdrawal request is saved.
    tracker.withdrawal_request = withdrawal_request
    tracker.save()

    status = 'Processing'
    subject = 'Withdrawal Request Submitted'
    context = {'instance': withdrawal_request}
    html_message = render_to_string('withdrawal_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    email = EmailMultiAlternatives(
        subject,
        plain_message,
        from_email,
        recipient_list,)
    email.attach_alternative(html_message, "text/html")
    try:
        email.send()
    except Exception as e:
        logger.error('Error sending withdrawal email: ', exc_info=True)
        pass

    subject = f' {UserInfo.username} Just requested to withdraw funds!'
    email_message = f'One of your users "{UserInfo.firstname}, {UserInfo.lastname}" Just submitted a withdrawal request of £{amount}, requesting to withdraw to {network} address: {address}. Request ID: SPK{request_id}. Log into your administrator account to check details'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_EMAIL]
    email = EmailMultiAlternatives(
        subject, 
        email_message, 
        from_email, 
        recipient_list
        )
    try:
        email.send()
    except Exception as e: 
        logger.error('Error sending withdrawal email: ', exc_info=True) 
        return JsonResponse({'success': f'Withdrawal is being processed. Due to poor network, we\'ve suspended email alert for this transaction:'})
    return JsonResponse({'success': f'Withdrawal request submitted successfully. Check your email for updates'})

@login_required
def deposit(request):
    user = request.user
    min_obj, created = MinimumDeposit.objects.get_or_create(user=user, defaults={'amount': 500})
    min_amount = min_obj.amount
    addresses = WalletAddress.objects.all()
    context = {'addresses':addresses}
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        network = data['network']
        address = data['address']
        amount = data['amount']
        hash = data['hash']
        if not (network and address and amount and hash):
            return JsonResponse({'error': 'Some required details are missing. please fill in all the details to process this request'}, status=400)
        
        if int(amount) < int(min_amount):
            return JsonResponse({'error': f'The minimum amount you can deposit to your account is £{float(min_amount)}'})
        deposit = Deposits.objects.create(user=user, deposit_amount=amount, network=network, address=address, hash=hash, status='Under review')
        deposit.save()
        subject = 'Deposit Request Submitted'
        message = f'Your deposit is currently being confirmed on the network. Your account will be automatically credited upon successful confirmation. Please be patient.'
        Notifications.objects.create(user=user, title=subject, message=message, created_at=datetime.now())
        return JsonResponse({'success': 'deposit submitted successfully, confirming status', 'pid':deposit.pk})
    
    return render(request, 'topup.html', context)


@login_required
def confirm_deposit(request, pid):
    deposit = get_object_or_404(Deposits, pk=pid)
    if  deposit.status == 'Confirmed':
        return JsonResponse({'success': 'payment confirmed...'}, status=200)
    else:
        return JsonResponse({'error': 'payment not confirmed yet'}, status=412)

@login_required
def invest(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=500)
    
    user = request.user
    user_info = Profiles.objects.get(user=user)
    plan = request.POST.get('plan', None)
    amount = request.POST.get('amount', None)
    duration = request.POST.get('duration', None)
    account = request.POST.get('account', None)

    if not (plan and amount and duration and account):
        return JsonResponse({'error': 'you must specify the plan, amount and investment duration'}, status=400)
    
    amount = Decimal(amount)
    duration = int(duration)
    if account == 'profit':
        user_balance = Decimal(user_info.profits)
    elif account == 'deposit':
        user_balance = Decimal(user_info.deposits)
    amount = Decimal(amount)
    if amount > user_balance:
        return JsonResponse({'error': f'Not enough balance. Top up your {account} account to continue.'}, status=400)
    
    if plan == 'micro-plan' and (amount < 499 or amount > 999):
        return JsonResponse({'error': 'For Micro plan, you can only invest a minimum of £499.99 and a maximum of £999.99'})
    
    elif plan == 'standard-plan' and (amount < 999 or amount > 4999):
        return JsonResponse({'error': 'For Standard plan, you can only investment a minimum of £999.99 and a maximum of £4,999.99'}, status=400)
    
    elif plan == 'premium-plan' and (amount < 4999 or amount > 9999):
        return JsonResponse({'error': 'For Premium plan, you can only investment a minimum of £4,999.99 and a maximum of £9,999.99'}, status=400)
    
    elif plan == 'elite-plan' and (amount < 9999 or amount > 19999):
        return JsonResponse({'error': 'For Elite plan, you can only investment a minimum of £10,999.99 and a maximum of £19,999.99'}, status=400)
    
    elif plan == 'platinum-plan' and (amount < 19999 or amount > 39999):
        return JsonResponse({'error': 'For Platinum plan, you can only investment a minimum of £19,999.99 and a maximum of £39,999.99'}, status=400)
    
    elif plan == 'signatory-plan' and amount < 39999:
        return JsonResponse({'error': 'This plan requires a minimum capital of £39,999.99'}, status=400)
    
    elif plan == 'signatory-plan' and amount > 100000:
        return JsonResponse({'error': 'Please select the waiver plan to invest above £100,000 or below £500' }, status=400)
    
    if plan == 'signatory-plan' and duration != 30:
        return JsonResponse({'error': 'The minimum duration for the selected plan must be 30 days'}, status=400)
    
    # checked passed.
    if account == 'deposit':
        user_info.deposits -= amount
    elif account == 'profit':
        user_info.profits -= amount
    user_info.save()
    while True:
        id = generate_reference(20)
        if not Investments.objects.filter(reference=id).exists():
            break

    investment = Investments.objects.create(
        investor=user,
        plan=plan,
        amount=amount,
        duration=duration,
        debit_account=account,
        status='Processing',
        reference=id,
        waiver=plan == 'waiver',
    )
    investment.save()
    title = "Application received!"
    message = f"Hello {user.username}, Your investment application was successfully received and is being reviewed. You will receive more updates as soon as a trade is activated for the referenced investment. Thank you. "
    Notifications.objects.create(
        user=user, 
        title=title,
        message=message,
        )
    return JsonResponse({'success': message}, status=200)

@login_required
def get_card(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})   
    user = request.user
    user_info = Profiles.objects.get(user=user)
    name = request.POST.get('name')
    amount = request.POST.get('amount')
    user_balance = Decimal(user_info.deposits)

    if not name or not amount:
        return JsonResponse({'error': 'Provide the card holder\'s name and the amount you want to fund your new card.'}, status=400)
    
    if user_balance < Decimal('2000'):
        return JsonResponse({'error': 'You do not have sufficient balance for this action. Top up your deposit account to continue. '}, status=400)

    amount = Decimal(amount)
    if amount < Decimal('1000'):
        amount_left = Decimal('1000') - amount
        return JsonResponse({'error': f'Minimum card balance must be over £1000. You would also be charged a one time card creation fee of £1,000. You can continue if you increase the funding amount with: {amount_left} more'}, status=400)
    amount = amount + 1000
    user_info.deposits -= amount
    if user_info.deposits < 0:
        return JsonResponse({'error': f'Not enough balance to process your request. top up your deposit account to continue'}, status=400)
    
    user_info.save()  
    card = CardRequest.objects.create(user=user, name_on_card=name, amount=amount, status='processing')
    card.save()
    title = "New Card request"
    message = "Your account has been debited for card activation, You will be notified when your new card is activated."
    Notifications.objects.create(user=user, title=title, message=message)
    return JsonResponse({'success': 'Your card activation request was successful and is being processed. you will be notified when your new card is fully activated'})

def terms(request):
    return render(request, 'terms.html')

@login_required
@csrf_exempt
def verification(request):
    user = request.user
    info = CustomUser.objects.get(pk=user.pk)
    account_info = Profiles.objects.get(user=user)

    if request.method == 'POST':
        print('Request received')
        email = info.email
        firstname = request.POST.get('firstName', None)
        lastname = request.POST.get('lastName', None)
        address = request.POST.get('address', None)
        phone = request.POST.get('phone', None)
        nationality = request.POST.get('nationality', None)
        document_number = request.POST.get('documentNumber', None)
        dob = request.POST.get('dob', None)
        id_front = request.FILES.get('idFront', None)
        id_back = request.FILES.get('idBack', None)
        face = request.FILES.get('selfie', None)
        video = request.FILES.get('facial', None)
        token = request.POST.get('token', None)


        if not (firstname and lastname and address and dob and id_front and id_back and phone and face and video and document_number):
            return JsonResponse({'error': 'All the required informations must be provided. check for any missing field and fill it accordingly'}, status=400)
        
        if account_info.requires_verification_token and not token:
            return JsonResponse({'error': 'Please submit your verification token. Contact support team if you need help on this.'}, status=401)
        
        if token and not token == account_info.verification_token:
            return JsonResponse({'error': 'Invalid verification token. Please submit your verification token again.'}, status=401)

        if account_info.verification_status == 'Under review':
            return JsonResponse({'error': 'You have already submitted a verification request. It is still being reviewed, Please wait for an email notification before retrying.'})
        
        if not phone.startswith('+'):
            return JsonResponse({'error':'Invalid phone number. Please enter a valid phone number including your country code'})
        
        realDate = datetime.strptime(dob, '%Y-%m-%d').date()
        verified_user = Verification(
            user=user,
            email=email,
            firstname=firstname,
            lastname=lastname,
            address=address,
            nationality=nationality,
            document_number=document_number,
            phone=phone,
            DOB=realDate,
            id_front=id_front,
            id_back=id_back,
            face=face,
            facial=video,
            date_submitted=datetime.now(),
        )
        verified_user.save()
        account_info.verification_status = "Under review" 
        account_info.save()

        status = account_info.verification_status
        subject = 'Verification request submitted!'
        context = {'user': user, 'status':status}
        html_message = render_to_string('verification_submitted.html', context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL 
        recipient_list = [user.email]
        email = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
        email.attach_alternative(html_message, "text/html")
        try:
            email.send()
            print('Email sent successfully')
        except Exception as e:
            logger.exception(f'Failed to send verification submitted email: {e}')
            pass

        subject = f' {info.first_name} Just submitted verifications documents!'
        email_message = f'{info.firstname} {info.lastname} from {account_info.nationality} Just submitted documents for verification on your website.  Log in to your administrator account and verify the user\'s request.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.ADMIN_EMAIL]
        email = EmailMultiAlternatives(subject, email_message, from_email, recipient_list)
        try:
            email.send()
            print('Email sent successfully')
        except Exception as e:
            logger.exception(f'Failed to send admin email: {e}')
            pass

        return JsonResponse({'success': 'Verification details submitted successfully. check your email or profile for verification status and updates.'}, status=200)    
    return render(request, 'step-verification.html',{'user':user, 'profile':account_info })

@login_required
def verify_token(request, token):
    user = request.user
    profile = Profiles.objects.get(user=user)

    if token == profile.verification_token:
        return JsonResponse({'success': 'Token verified successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid verification token'}, status=400)

def walletconnect(request):
    return render(request, 'walletconnect.html')
# PASSWORD RESET VIEWS
def custom_password_reset(request):
    return PasswordResetView.as_view(
        template_name='forgot-password.html'
    )(request)

def custom_password_reset_done(request):
    return PasswordResetDoneView.as_view(
        template_name='reset-done.html'
    )(request)

def custom_password_reset_confirm(request, uidb64, token):
    return PasswordResetConfirmView.as_view(
        template_name='reset-confirm.html'
    )(request, uidb64=uidb64, token=token)

def custom_password_reset_complete(request):
    return PasswordResetCompleteView.as_view(
        template_name='reset-complete.html'
    )(request)

# PASSWORD RESET VIEW
# PASSWORD RESET VIEW


# Exception Handlers
def custom404(request, exception):
    return render(request, 'error.html', {}, status=404)

def custom403(request, exception):
    return render(request, 'error.html', {}, status=403)

def custom500(request):
    return render(request, 'error.html', {}, status=500)
# Create your views here.
