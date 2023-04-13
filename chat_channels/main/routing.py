from channels.security.websocket import WebsocketDenier
from django.urls import path, re_path
from .consumers import Consumer
from .middlewares.access import AccessToLineBaseMiddleware
from channels.routing import URLRouter
from channels.db import database_sync_to_async
from main.models.chat import Line
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps


@database_sync_to_async
def check_line(line_id):
    line = Line.objects.get(id=line_id)
    return line


class LineRouterMiddleware:
    async def __call__(self, scope, recv, send):
        scope['path_remaining'] = scope['path'].replace('ws/', '')

        if not scope["url_route"]["kwargs"].get("line_id"):
            scope["line_id"] = "online_coach_connector"
        else:
            scope["line_id"] = scope["url_route"]["kwargs"]["line_id"]

        try:
            line = await check_line(scope["line_id"])
        except ObjectDoesNotExist:
            return await AccessToLineBaseMiddleware(Consumer.as_asgi())(scope, recv, send)

        REAL_TYPE = await database_sync_to_async(line.cast)()
        if REAL_TYPE._meta.app_label == "main":
            return await AccessToLineBaseMiddleware(Consumer.as_asgi())(scope, recv, send)

        cfg = apps.get_app_config(REAL_TYPE._meta.app_label)
        return await cfg.routing(scope, recv, send)


websocket_urlpatterns = [
    re_path(r'^(?P<path>.*)/$', LineRouterMiddleware()),
    path('', LineRouterMiddleware()),
]

app = URLRouter(
    websocket_urlpatterns
)