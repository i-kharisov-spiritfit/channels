from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
import requests
from chat.models import Client
from django.core.exceptions import ObjectDoesNotExist

@database_sync_to_async
def get_user(token):
    #ПРОВЕРКА ЧЕРЕЗ 1C
    r=requests.get(
        url="https://app.spiritfit.ru/fitness-test1/hs/website/chats",
        headers={
            "Authorization":token
        }
    )

    json_data=r.json()

    response=json_data.get("result")
    if response:
        phone = response['phone']
        name = response['name']
        surname = response['surname']
        photo = response['photo']
        access = response['access']

        try:
            client = Client.objects.get(phone=phone)
            client.online = True
            client.access = access
            client.mobile_token = token
            client.save()
        except ObjectDoesNotExist:
            client = Client(phone=phone, name=name, surname=surname, picture=photo, access=access, online=True, mobile_token=token)
            client.save()
        return client

    return None

class Auth1CMiddleware(BaseMiddleware):
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])

        if not b'authorization' in headers:
            scope['client'] = False
        else:
            token = headers[b'authorization'].decode()
            scope['client'] = await get_user(token)


        return await super().__call__(scope, receive, send)