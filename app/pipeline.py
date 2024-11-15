from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import Profiles, Referrals, MinimumDeposit, send_email, is_verified, Notifications
from django.core.files.base import ContentFile
from django.conf import settings
from .views import get_referral_code
import requests
from PIL import Image
from io import BytesIO
from tempfile import NamedTemporaryFile
import logging
from .models import CustomUser
from social_core.exceptions import AuthForbidden

logger = logging.getLogger(__name__)

def save_profile(backend, user, response, *args, **kwargs):
    nationality = backend.strategy.session_get('nationality')
    print(response)
    # Extract user information from the response based on backend
    if backend.name == 'google-oauth2':
        email = response.get('email')
        firstname = response.get('given_name')
        lastname = response.get('family_name')
        picture_url = response.get('picture')  
        social_id = response.get('sub')
    elif backend.name == 'facebook':
        full_name = response.get('name', '')
        social_id = response.get('id')
        picture_url = None 
    
        email = f'{social_id}@facebook.com'
        if full_name:
            name_parts = full_name.split(' ', 1)
            firstname = name_parts[0]
            lastname = name_parts[1] if len(name_parts) > 1 else ''
        else:
            firstname = 'FacebookUser'
            lastname = ''


    try:
        # Check if the user exists
        user = CustomUser.objects.get(email=email)
        profile, profile_created = Profiles.objects.get_or_create(
            user=user, 
            defaults={
                'can_login': True,
                'nationality': nationality if nationality else 'Not specified',
            }
        )

        # Handle if the user's login is disabled
        if not profile.can_login:
            send_email.objects.create(
                user=user,
                Subject='Attention Required! Login not allowed!',
                Message='We noticed a login attempt for your user account at Vista, However, due to unusual activities detected on your account, we\'ve disabled. To rectify this issue, please contact our live support team via live chat on the website or by sending a mail to support@exchangevista.com'
            )
            raise AuthForbidden("Account suspended.")
    
    except CustomUser.DoesNotExist:
        # Create a new user if one doesn't exist
        user = CustomUser.objects.create_user(
            email=email,
            username=f'{firstname or "user"}-{social_id}',  
            firstname=firstname,
            lastname=lastname,
        )

        # Create a new profile for the new user
        profile, profile_created = Profiles.objects.get_or_create(
            user=user, 
            defaults={
                'can_login': True,
                'nationality': nationality if nationality else 'Not specified',
            }
        )
        if backend.name == 'facebook':
            Notifications.objects.create(
                user=user,
                title='Please request an email update on your account',
                message='Welcome to Vista, your flexible investment account. Please request an email update on your account to stay informed on important changes and alerts related to your account. the current email attached to your account is not eligible for use within our platform. engage the support team via live chat to request this change'
            )


        # Create related instances
        referral_ID = get_referral_code()
        Referrals.objects.get_or_create(user=user, defaults={'referral_id': referral_ID})
        MinimumDeposit.objects.get_or_create(user=user, defaults={'amount': 500})
        is_verified.objects.get_or_create(user=user, defaults={
            'verified': True, 
            'email': user.email,
            'verification_code': 0,
        })

    # Handle profile picture url if provided
    if picture_url:
        try:
            response = requests.get(picture_url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                with NamedTemporaryFile() as temp_image:
                    img.save(temp_image, format=img.format)
                    temp_image.flush()
                    temp_image.seek(0) 
                    profile_pic_format = img.format.lower()
                    profile_pic_name = f'{social_id}.{profile_pic_format}'
                    profile.profile_pic.save(profile_pic_name, ContentFile(temp_image.read()), save=True)
        except Exception as e:
            logger.exception(f"Failed to download or save profile picture: {e}")
            default_image_path = settings.DEFAULT_AVATAR
            with open(default_image_path, 'rb') as f:
                profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
    elif not profile.profile_pic:
        default_image_path = settings.DEFAULT_AVATAR
        with open(default_image_path, 'rb') as f:
            profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)

    # Update nationality
    profile.nationality = nationality if nationality else 'Not specified'
    profile.save()

    return {'user': user, 'profile': profile}
