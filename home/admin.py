from django.contrib import admin
from .models import *
from app.models import *


admin.site.register([
    Enquiries,
    TradingJournals,
    JournalPurchase,
    JournalPayments,
])
# Register your models here.
