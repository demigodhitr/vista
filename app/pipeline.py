from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import Profiles, Referrals, MinimumDeposit, send_email, is_verified
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
    # Extract user information from the response
    email = response.get('email')
    firstname = response.get('given_name')
    lastname = response.get('family_name')
    picture_url = response.get('picture')  
    google_id = response.get('sub')
    

    try:
        user = CustomUser.objects.get(email=email)
        profile, profile_created = Profiles.objects.get_or_create(
            user=user, 
            defaults={
                'can_login': True,
                'nationality': nationality if nationality else 'Not specified',
            })

        if not profile.can_login:
            send_email.objects.create(
                user=user,
                Subject='Attention Required! Login not allowed!',
                Message='Your vista account is currently suspended, Please open a live chat with our support team through our website for resolution.'
            )
            raise AuthForbidden("Your vista account is currently suspended.")
    except CustomUser.DoesNotExist:
        # Create a new user if it doesn't exist
        user = CustomUser.objects.create_user(
            email=email,
            username=f'{firstname}-{google_id}', 
            firstname=firstname,
            lastname=lastname,
        )

        # Create a new profile instance
        profile, profile_created = Profiles.objects.get_or_create(
            user=user, 
            defaults={
                'can_login': True,
                'nationality': nationality if nationality else 'Not specified',
            })
        referral_ID = get_referral_code()
        Referrals.objects.get_or_create(user=user, defaults={'referral_id': referral_ID})
        MinimumDeposit.objects.get_or_create(user=user, defaults={'amount': 500})
        is_verified.objects.get_or_create(user=user, defaults={
            'verified':True, 
            'email':user.email,
            'verification_code':0,
            })
    except Exception as e:
        print(str(e))
        logger.exception(f"Failed to create user or profile: {e}")
        raise e 
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
                    profile_pic_name = f'{google_id}.{profile_pic_format}'
                    profile.profile_pic.save(profile_pic_name, ContentFile(temp_image.read()), save=True)
            else:
                print('Failed to download image')
        except Exception as e:
            logger.exception(f"Failed to download or save profile picture: ")
            default_image_path = settings.DEFAULT_AVATAR
            with open(default_image_path, 'rb') as f:
                profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
    elif not profile.profile_pic.url:
        default_image_path = settings.DEFAULT_AVATAR
        with open(default_image_path, 'rb') as f:
            profile.profile_pic.save('default-avatar.png', ContentFile(f.read()), save=True)
    profile.nationality = nationality if nationality else 'Not specified'
    profile.save()

    return {'user': user, 'profile': profile}
