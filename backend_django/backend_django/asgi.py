"""
ASGI config for backend_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# backend_django/asgi.py
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# from consult.routing import websocket_urlpatterns
# import consult.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_django.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()        # 기본: application = get_asgi_application()

application = ProtocolTypeRouter({      # 연결 유형 검사
    "http": django_asgi_app,
    # "websocket": AllowedHostsOriginValidator(
    #     # AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    #     AuthMiddlewareStack(URLRouter(consult.routing.websocket_urlpatterns))
    # ),  # WebSocket 연결(ws:// 또는 wss://)인 경우 AuthMiddlewareStack에 연결됨
})
