from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.middleware import get_user
from django.contrib.auth.models import AnonymousUser
from app.views import fetch_exchange_rates





class UpdateBalanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = get_user(request)
        
        if user.is_authenticated:
            fetch_exchange_rates(user)