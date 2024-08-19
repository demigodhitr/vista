from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin


class AccountInfoInline(admin.StackedInline):
    model = Profiles
    can_delete = True
    extra = 0

class CryptoCardsInline(admin.StackedInline):
    model = CryptoCards
    extra = 0
    

class NotificationsInline(admin.StackedInline):
    model = Notifications
    can_delete = True
    extra = 0

class WithdrawalRequestInline(admin.StackedInline):
    model = WithdrawalRequest
    can_delete = True
    extra = 0

class DepositsInline(admin.StackedInline):
    model = Deposits
    can_delete = True
    extra = 0
class VerificationInline(admin.StackedInline):
    model = Verification
    can_delete = True
    extra = 0

class EmailMessageInline(admin.StackedInline):
    model = send_email
    can_delete = True
    extra = 0

class LimitInline(admin.StackedInline):
    model = MinimumDeposit
    can_delete = True
    extra = 0
class RefferalsInline(admin.StackedInline):
    model = Referrals
    can_delete = True
    extra = 0

class CustomUserAdmin(UserAdmin):
    inlines = [
        AccountInfoInline, 
        CryptoCardsInline, 
        WithdrawalRequestInline, 
        NotificationsInline, 
        DepositsInline,
        VerificationInline,
        EmailMessageInline,
        LimitInline,
        RefferalsInline,
        ]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register([
     Profiles,
     Deposits,
     WalletAddress, 
     ExchangeRates, 
     MinimumDeposit, 
     Investments, 
     CardRequest,
     Referrals,
     WithdrawalRequest,
     Verification
     ])

# Register your models here.
