from django.db import models
from app.models import CustomUser
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger('django')

class Enquiries(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    ticket_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class TradingJournals(models.Model):
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    description = models.TextField()
    display_picture = models.ImageField(upload_to='trading_journals/display_pictures')
    file = models.FileField(upload_to='trading_journals/journals', verbose_name='JOURNAL FILE')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    def __str__(self):
        return self.title


class JournalPurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    journal = models.ForeignKey(TradingJournals, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_downloads = models.IntegerField(default=0)
    def __str__(self):
        return f'{self.user.username} - {self.allowed_downloads} left'

    
class JournalPayments(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    journal = models.ForeignKey(TradingJournals, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_network = models.CharField(max_length=10)
    payment_address = models.CharField(max_length=255)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_received = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.payment_network}'
    

@receiver(post_save, sender=JournalPayments)
def notifier(sender, instance, created, **kwargs):
    if created:
        subject = 'New Journal payment'
        body = f'A trading journal with title: "{instance.journal.title}" has just been paid for by <strong>{instance.user.firstname} {instance.user.lastname}.</strong> and the user is waiting for  you to confirm receipt of payment. please login and check the details of the payment and confirm to enable the user complete their purchase. If you don\'t confirm within 50 minutes, the transaction will be timed out on the client side.'

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['support@equinoxtraders.com']
        try:
            send_mail(
            subject,
            body,
            from_email,
            recipient_list,
            html_message=body,
        )
        except Exception as e:
            logger.error("Error sending purchase email: ", exc_info=True)
            pass




# Create your models here.
