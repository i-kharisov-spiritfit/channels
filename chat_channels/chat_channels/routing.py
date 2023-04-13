from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path
from main.routing import app


application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/', app)
    ])
})

# application = ProtocolTypeRouter({
#     'websocket': URLRouter([
#         path('ws/', URLRouter([
#             path("chat/",
#                 URLRouter(
#                     [
#                         re_path(r'^(?P<room_name>[^/]+)/$', Auth1CMiddleware(ChatConsumer.as_asgi())),
#                     ]
#                 )
#             ),
#         ]))
#     ])
# })