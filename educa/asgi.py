"""
ASGI config for educa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from chat import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educa.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # класс AuthMiddlewareStack поддерживает встроенную в Django стандартную
    # аутентификацию, при которой детальная информация о пользователе хранится в сеансе
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            # URLRouter используется для соотнесения соединений websocket
            # с шаблонами URL-адресов, определенными в списке websocket_urlpatterns
            URLRouter(routing.websocket_urlpatterns)
        )
    ),
})
