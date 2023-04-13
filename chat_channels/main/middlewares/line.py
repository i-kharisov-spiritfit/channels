# from channels.db import database_sync_to_async
# from main.models.chat import Line
# from django.core.exceptions import ObjectDoesNotExist
# from main.middlewares.access import AccessToLineBaseMiddleware
# from portal.models.chat import prtl_Line
# from portal.routing import app
# from main.consumers import Consumer
#
# class LineRouterMiddleware:
#
#     @database_sync_to_async
#     def check_line(self, line_id):
#         line = Line.objects.get(id=line_id)
#         return line
#
#     async def __call__(self, scope, receive, send):
#         if not scope["url_route"]["kwargs"].get("line_id"):
#             scope["line_id"] = "online_coach_connector"
#         else:
#             scope["line_id"] = scope["url_route"]["kwargs"]["line_id"]
#
#
#
#         try:
#             line = await self.check_line(scope["line_id"])
#         except ObjectDoesNotExist:
#             return AccessToLineBaseMiddleware(Consumer.as_asgi())
#
#
#
#         if isinstance(line, prtl_Line):
#             return app
#         else:
#             return AccessToLineBaseMiddleware(Consumer.as_asgi())