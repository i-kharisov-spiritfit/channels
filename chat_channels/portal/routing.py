from django.urls import path, re_path
from .consumers import Consumer
from channels.routing import URLRouter
from main.middlewares.access import AccessToLineFromCrmMiddleware

urlpatterns = [
    path('', AccessToLineFromCrmMiddleware(Consumer.as_asgi())),
]

app = URLRouter(
    urlpatterns
)