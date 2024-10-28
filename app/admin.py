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

class InvestmentInline(admin.StackedInline):
    model = Investments
    can_delete = True
    extra = 0

class LimitInline(admin.StackedInline):
    model = MinimumDeposit
    can_delete = True
    extra = 0

class ReferralsInline(admin.StackedInline):
    model = Referrals
    can_delete = True
    extra = 0


class CustomUserAdmin(UserAdmin):
    inlines = [
        AccountInfoInline, 
        LimitInline,
        DepositsInline,
        WithdrawalRequestInline,
        InvestmentInline,
        CryptoCardsInline, 
        NotificationsInline, 
        EmailMessageInline,
        VerificationInline,
        ReferralsInline,
    ]

    # Specify the fields to display in the admin list view
    list_display = ('username', 'firstname', 'lastname', 'email', 'is_staff')

    # Specify the fields to display in the admin detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('firstname', 'lastname', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Use search fields and filters for easier access to users
    search_fields = ('firstname', 'lastname', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register([
    Profiles,
    Deposits,
    WalletAddress,
    MinimumDeposit,
    Investments,
    EarningsHistory,
    CardRequest,
    CryptoCards,
    Referrals,
    WithdrawalRequest,
    Verification,
    Activities,
])