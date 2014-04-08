from socialoauth import SocialSites
from django.conf import settings

social_sites = SocialSites(settings.SOCIALOAUTH_SITES)
