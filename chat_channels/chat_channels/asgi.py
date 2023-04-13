"""
ASGI config for chat_channels project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

import django
from channels.routing import get_default_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_channels.settings')
os.environ.setdefault('SERVER_GATEWAY_INTERFACE', 'ASGI')
django.setup()

application = get_default_application()
