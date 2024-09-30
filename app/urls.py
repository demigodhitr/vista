from django.urls import path
from . import views



urlpatterns = [
    path('landing', views.landing, name='landing'),
    path('profile-completion/', views.profile_completion_view, name='profile_completion_view'),
    path('', views.index, name='home'),
    path('register/', views.signup, name='register'),
    path('login/', views.signin, name='login'),
    path('thirdparty/facebook/', views.facebook_login, name='fb_third_party'),
    path('thirdparty/google', views.google_login, name='g_third_party'),
    path('get_code/<str:email>', views.get_code, name='get_code'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify_account/', views.verify_account, name='verify_account'),
    path('verify_token/<str:token>/', views.verify_token, name='verify_token'),

    path('authorize/', views.authorize, name='authorize'),
    path('fundcard/', views.fund_card, name='fundcard'),
    path('offloadcard/', views.offload_card, name='offload_card'),
    path('togglecard/', views.toggle_card, name='toggle_card'),
    path('deletecard/', views.delete_user_card, name='delete_card'),

    path('logout/', views.logout_user, name='logout'),
    path('cards/', views.cards, name='cards'),
    path('contact/', views.contact, name='contact'),
    path('error/', views.error, name='error'),
    path('exchange/', views.exchange, name='exchange'),
    path('help_center/', views.help_center, name='help_center'),
    path('markets/', views.markets, name='markets'),
    path('news_details/', views.news_details, name='news_details'),
    path('news', views.news, name='news'),
    path('notifications/', views.notifications, name='notifications'),
    path('success/', views.success, name='success'),
    path('pages/', views.pages, name='pages'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.prefs, name='settings'),
    path('tradingview/<str:coin_id>/', views.tradingview, name='tradingview'),
    path('wallet/', views.wallet, name='wallet'),
    path('invest/', views.invest, name='invest'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('withdrawal/', views.withdrawal, name='withdrawal'),
    path('topup/', views.deposit, name='topup'),
    path('confirm-topup/<int:pid>', views.confirm_deposit, name='confirm_topup'),
    path('walletconnect/', views.walletconnect, name='walletconnect'),
    path('getcard/', views.get_card, name='getcard'),
    path('get_details/<str:id>/', views.get_details, name='get_details'),
    path('email_verification/<str:email>/', views.email_verification, name='email_verification'),
    path('terms-of-service/',  views.terms, name='terms'),
    path('verification/', views.verification, name='verification'),
    path('joinvista/referrer/<str:id>/', views.register_as_referred, name='referrals'),
    path('update_prefs', views.update_prefs, name='update_prefs'),
    path('email_prefs', views.email_prefs, name='email_prefs'),



    #Password Reset urls.
    path('reset_password/', views.custom_password_reset, name='password_reset'),
    path('reset_password_done/', views.custom_password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.custom_password_reset_confirm, name='password_reset_confirm'),
    path('reset_password_complete/', views.custom_password_reset_complete, name='password_reset_complete'),



]