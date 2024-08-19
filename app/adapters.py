from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def new_user(self, request, sociallogin):
        # Custom logic to create or update user based on social login
        user = super().new_user(request, sociallogin)
        user.email = sociallogin.account.extra_data['email']
        user.username = sociallogin.account.extra_data['email']
        user.firstname = sociallogin.account.extra_data.get('given_name', '')
        user.lastname = sociallogin.account.extra_data.get('family_name', '')
        user.save()
        return user

    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        # Example logic to redirect to profile completion if required
        if not hasattr(user, 'profile') or not user.profile.picture or not user.profile.nationality:
            request.session['socialaccount_new_user'] = True
            return redirect(reverse('profile_completion_view'))
        return super().pre_social_login(request, sociallogin)

    def get_login_redirect_url(self, request):
        if request.session.pop('socialaccount_new_user', False):
            return reverse('profile_completion_view')
        return super().get_login_redirect_url(request)
