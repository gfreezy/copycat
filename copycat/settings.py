#coding: utf8
"""
Django settings for copycat project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from socialoauth import SocialSites
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+6uf1bwf@ul6h9w7vsg1&6t+s1i!-ei=x$36ee53)6@nlb4j+&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG
TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]
TEMPLATE_LOADERS = (
    'jingo.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    'django.core.context_processors.request',
    "django.contrib.messages.context_processors.messages",
    'forum.context_processors.global_variables',
)

JINJA_CONFIG = {
    'autoescape': True,
    'extensions': ['pipeline.jinja2.ext.PipelineExtension'],
}

JINGO_EXCLUDE_APPS = (
    'debug_toolbar',
    'admin',
    'admindocs',
    'registration',
    'context_processors',
)


ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'forum',
    'sky_thumbnails',
    'pipeline',
    'django_cron',
    'django_extensions',
    # 'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'copycat.urls'

WSGI_APPLICATION = 'copycat.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'zh-cn'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

HOSTNAME = 'http://a.dev:8000'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static_online")
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS = {
    'main': {
        'source_filenames': (
            'css/bootstrap/bootstrap.min.css',
            'css/base/font-awesome.css',
            'css/summernote.css',
            'css/base/atom.css',
            'css/flag.css',
            'css/main.css',
        ),
        'output_filename': 'css/master.css',
    },
}

PIPELINE_JS = {
    'main': {
        'source_filenames': (
            'js/base/jquery-1.8.3.min.js',
            'js/base/bootstrap.min.js',
            'js/base/jquery.cookie.js',
            'js/base/summernote.js',
            'js/base/summernote-zh-CN.js',
        ),
        'output_filename': 'js/master.js',
    }
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
THUMBNAILS_DELAYED_GENERATION = True


EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'gfreezy@gmail.com'
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True


LOGIN_URL = 'django.contrib.auth.views.login'
AUTH_USER_MODEL = 'forum.User'


CRON_CLASSES = [
    'forum.tasks.economic_events.EconomicEventsJob',
    'forum.tasks.forex.EconomicEventsJob',
    'forum.tasks.central_bank.CentralBankJob',
    'forum.tasks.important_events.EconomicEventsJob',
]

SOCIALOAUTH_SITES = (
    ('weibo', 'socialoauth.sites.weibo.Weibo', u'新浪微博',
        {
          'redirect_uri': HOSTNAME + '/forum/login/weibo',
          'client_id': '1753603767',
          'client_secret': '51eccdf6f40be550bcbe3aecd55e0ac8',
        }
    ),

    ('qq', 'socialoauth.sites.qq.QQ', u'QQ',
        {
          'redirect_uri': HOSTNAME + '/forum/login/qq',
          'client_id': 'YOUR ID',
          'client_secret': 'YOUR SECRET',
        }
    ),
)

