from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from .middlewares import Auth1CMiddleware

import chat.routing

application = ProtocolTypeRouter({
    'websocket': Auth1CMiddleware(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})