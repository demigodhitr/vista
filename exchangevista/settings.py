
from pathlib import Path
import os  

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

SESSION_COOKIE_AGE = 1500
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

AUTH_USER_MODEL = 'app.CustomUser'
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-@rm)oj%)9l21y3#bezexqqf0e)#ruri*gr7wes*ljbu6=kr$%!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'home',
    
    'django.contrib.humanize',
    # 'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'webpack_loader',

    #third party apps
    'social_django',
]

SITE_ID = 1
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    # 'facebook': {
    #     'METHOD': 'oauth2',
    #     'SCOPE': ['email', 'public_profile', 'user_friends'],
    #     'AUTH_PARAMS': {'auth_type':'reauthenticate'},
    #     'INIT_PARAMS': {'cookie': True},
    #     }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'app.middleware.update_balances.UpdateBalanceMiddleware',
]

ROOT_URLCONF = 'exchangevista.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'exchangevista.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ERROR LOGGING CONFIG
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'django_errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'app.management.commands.increase_profits': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

G_RECAPTCHA_SECRET = '6LeG4CgqAAAAAH54NdeR59PYva1DmKW9e3Vz4EnF'
# Application definition


EXCHANGE_KEY = '08e90217d43f932b9acb53f2'

ADMIN_EMAIL = 'support@exchangevista.com'
# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app/embedded/build/static'),
]

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'embedded/',  # Folder where bundles are stored
        'STATS_FILE': os.path.join(BASE_DIR, 'app/embedded/webpack-stats.json'),  # Path to webpack-stats.json
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS_ALLOW_ALL_ORIGINS = True

# CSRF_TRUSTED_ORIGINS = [
#     'http://localhost:1000',
#     'https://exchangevista.com',
# ]


# EMAILBACKEND 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.exchangevista.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'alerts@exchangevista.com'
EMAIL_HOST_PASSWORD = 'Dy5z20m+DV4rQ!'
DEFAULT_FROM_EMAIL = 'alerts@exchangevista.com'
SERVER_EMAIL = 'alerts@exchangevista.com'

# FIREBASE & GOOGLE O-AUTH SECRETS
FIREBASE_ADMIN = BASE_DIR / 'exchangevista' / 'firebase-admin-key.json'
OAUTH_SECRET = BASE_DIR / 'exchangevista' / 'oauth-client-secret.json'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '644563502959-iqv5j9ie2rjdpqd2t62dq8eh2gmb6097.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'email',
    'profile',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://localhost:8080/oauth/complete/google-oauth2/'  # for local testing

#PIPELINE
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    # 'social_core.pipeline.user.get_username',
    # 'social_core.pipeline.user.create_user',  
    'app.pipeline.save_profile', # custom pipeline function
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
# AUTHENTICATION BACKEND
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
)

#default profile picture
DEFAULT_AVATAR = BASE_DIR / 'app' / 'static' / 'default-avatar.png'



# LOGIN REDIRECT PATH.
LOGIN_REDIRECT_URL = '/app/'
LOGOUT_REDIRECT_URL = '/app/'

FACEBOOK_APP_ID = '490627753425286'
FACEBOOK_APP_SECRET = '399a9fab546c89f97fe37c2ae17e7536'

# # CUSTOM ADAPTER
# ACCOUNT_ADAPTER = 'app.adapters.CustomSocialAccountAdapter'
# SOCIALACCOUNT_ADAPTER = 'app.adapters.CustomSocialAccountAdapter'
