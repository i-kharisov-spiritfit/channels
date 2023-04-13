from channels.middleware import BaseMiddleware
from channels.security.websocket import WebsocketDenier
from django.core.exceptions import ObjectDoesNotExist
from channels.db import database_sync_to_async
from main.models.chat import Line
from main import ACCESS_STATUS
from urllib.parse import parse_qs
from main.tools.crm import UserAccess


class AccessToLineBaseMiddleware(BaseMiddleware):
    @database_sync_to_async
    def check_line(self, line_id):
        line = Line.objects.get(id=line_id)
        return line

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        if not scope["url_route"]["kwargs"].get("line_id"):
            scope["line_id"] = "online_coach_connector"
        else:
            scope["line_id"] = scope["url_route"]["kwargs"]["line_id"]

        try:
            line = await self.check_line(scope["line_id"])
        except ObjectDoesNotExist:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)

        headers = dict(scope['headers'])
        A = UserAccess
        if b'authorization' in headers:
            token = headers[b'authorization'].decode()
            a = await database_sync_to_async(A)(
                {
                    "mobile_token":token
                },
                line
            )
        else:
            query_str = parse_qs(scope["query_string"].decode())

            if not "login" in query_str or not "token" in query_str:
                denier = WebsocketDenier()
                return await denier(scope, receive, send)

            login = query_str.get("login")[0] if isinstance(query_str.get("login"), list) and len(query_str.get("login"))>0 else None
            token = query_str.get("token")[0] if isinstance(query_str.get("token"), list) and len(query_str.get("token"))>0 else None

            if not login or not token:
                denier = WebsocketDenier()
                return await denier(scope, receive, send)

            a = await database_sync_to_async(A)(
                {
                    "login": login,
                    "token": token
                },
                line
            )

        scope['access'] = a.access
        if not scope['access']:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)


        return await super().__call__(scope, receive, send)

class AccessToLineFromCrmMiddleware(BaseMiddleware):
    @database_sync_to_async
    def check_line(self, line_id):
        line = Line.objects.get(id=line_id)
        line = line.cast()
        return line

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        if scope.get("access") == ACCESS_STATUS.ALLOW:
            return await super().__call__(scope, receive, send)
        elif scope.get("access") == ACCESS_STATUS.DENIED:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)

        if not scope.get("line_id"):
            if not scope["url_route"]["kwargs"].get("line_id"):
                scope["line_id"] = "online_coach_connector"
            else:
                scope["line_id"] = scope["url_route"]["kwargs"]["line_id"]

        try:
            line = await self.check_line(scope["line_id"])
        except ObjectDoesNotExist:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)

        A = UserAccess
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            token = headers[b'authorization'].decode()
            a = await database_sync_to_async(A)(
                {
                    "mobile_token": token
                },
                line
            )

            scope['access'] = a.access
        else:
            query_str = parse_qs(scope["query_string"].decode())

            # with open("logs.log", 'a', encoding='utf-8') as file:
            #     file.write(str(query_str)+"\n")

            if not "login" in query_str or not "token" in query_str:
                denier = WebsocketDenier()
                return await denier(scope, receive, send)

            login = query_str.get("login")[0] if isinstance(query_str.get("login"), list) else None
            token = query_str.get("token")[0] if isinstance(query_str.get("token"), list) else None

            # with open("logs.log", 'a', encoding='utf-8') as file:
            #     file.write(str((login, token))+"\n")

            if not login or not token:
                denier = WebsocketDenier()
                return await denier(scope, receive, send)

            a = await database_sync_to_async(A)(
                {
                    "login": login,
                    "token": token
                },
                line
            )

            scope['access'] = a.check_line_access_by_token()

        if not scope['access']:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)

        scope['line'] = line
        scope['user'] = a.user

        return await super().__call__(scope, receive, send)