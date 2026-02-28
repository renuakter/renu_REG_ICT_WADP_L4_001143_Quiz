"""
ASGI config for renu_REG_ICT_WADP_L4_001143_Quiz project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'renu_REG_ICT_WADP_L4_001143_Quiz.settings')

application = get_asgi_application()
