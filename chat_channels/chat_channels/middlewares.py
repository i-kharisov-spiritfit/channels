from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from chat.functions import check_client
from urllib.parse import parse_qs

class Auth1CMiddleware(BaseMiddleware):
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])

        if not b'authorization' in headers:
            query_str = parse_qs(scope["query_string"].decode())
            if "login" in query_str and "token" in query_str:
                login = query_str.get("login")[0]
                token = query_str.get("token")[0]

                scope['client'] = await database_sync_to_async(check_client)(
                    {
                        "login": login,
                        "token": token
                    }
                )
            else:
                scope['client'] = False

            # if not b'login' in headers or not b'id1c' in headers:
            #     scope['client'] = False
            # else:
            #     login = headers[b'login'].decode()
            #     password = headers[b'password']
            #
            #     scope['client'] = await database_sync_to_async(check_client)(
            #         {
            #             "login":login,
            #             "token":password
            #         }
            #     )
        else:
            token = headers[b'authorization'].decode()
            scope['client'] = await database_sync_to_async(check_client)(
                token
            )


        return await super().__call__(scope, receive, send)