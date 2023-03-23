from . import CRest
import re
from .models import Settings
from channels.db import database_sync_to_async
import redis
import chat_channels.settings as settings
from chat.models import Client
from django.core.exceptions import ObjectDoesNotExist
import requests
from uuid import uuid4



def get_connector_id():
    return settings.CONNECTORS["mobile_app"]["id"]

@database_sync_to_async
def get_line_async():
    try:
        s = Settings.objects.get(pk=1)
        return s.line
    except Exception as err:
        print(err)
        return False

def get_line():
    try:
        s = Settings.objects.get(pk=1)
        return s.line
    except Exception as err:
        print(err)
        return False

def convertBB(var):
    search = [
        r'\[b\](.+)\[/b\]',
        r'\[br\]',
        r'\[i\](.+)\[/i\]',
        r'\[u\](.+)\[/u\]',
        r'\[img\](.+)\[/img\]',
        r'\[url\](.+)\[/url\]',
        r'\[url\=(.+)\](.+)\[/url\]',
    ]

    replace = [
        r'<strong>\1</strong>',
        '<br>',
        r'<em>\1</em>',
        r'<u>\1</u>',
        r'<img src="\1" />',
        r'<a href="\1">\1</a>',
        r'<a href="\1">\2</a>',
    ]

    for i in range(len(search)):
        var = re.sub(search[i], replace[i], var)

    return var

def check_client(auth_params):
    def check_crm_request(headers):
        r = requests.get(
            url="https://1c.spiritfit.ru/fitness-test1/hs/website/chats",
            headers=headers
        )

        json_data = r.json()

        response = json_data.get("result")
        if response and json_data.get("success"):
            return response
        else:
            return None


    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT, db=0)


    if isinstance(auth_params, str):
        access = redis_instance.get(auth_params + "_access")
        redis_instance.close()
        type = "token"

    elif isinstance(auth_params, dict) and auth_params.get("login"):

        if not auth_params.get("id1c"):
            access_token = redis_instance.get(auth_params.get("login") + "_access_token")
            if access_token and access_token.decode() == auth_params.get("token"):
                client = Client.objects.get(phone=auth_params.get("login"))
                redis_instance.delete(auth_params.get("login") + "_access_token")
                return client
            else:
                return None

        access = redis_instance.get(auth_params.get("login") + "_access")
        redis_instance.close()

        if not access == None:
            access = bool(access.decode())
        type = "login"

    else:
        return None

    if access:
        if type=="token":
            try:
                client = Client.objects.get(mobile_token=auth_params)
            except ObjectDoesNotExist:
                response = check_crm_request({"Authorization": auth_params})
                if response:
                    phone = response['phone']
                    name = response['name']
                    surname = response['surname']
                    photo = response['photo']
                    access = response['access']

                    try:
                        client = Client.objects.get(phone=phone)
                        client.access = access
                        client.mobile_token = auth_params
                        client.photo = photo
                        client.save()
                    except ObjectDoesNotExist:
                        client = Client(phone=phone, name=name, surname=surname, picture=photo, access=access, mobile_token=auth_params)
                        client.save()

                    redis_instance.set(auth_params + "_access", str(access), ex=600)
                else:
                    return None

        elif type=="login":
            try:
                client = Client.objects.get(phone=auth_params.get("login"))
            except ObjectDoesNotExist:
                response = check_crm_request({
                        "login": auth_params.get("login"),
                        "id1c": auth_params.get("id1c")
                    })
                if response:
                    phone = response['phone']
                    name = response['name']
                    surname = response['surname']
                    photo = response['photo']
                    access = response['access']

                    try:
                        client = Client.objects.get(phone=phone)
                        client.access = access
                        client.photo = photo
                        client.save()
                    except ObjectDoesNotExist:
                        client = Client(phone=phone, name=name, surname=surname, picture=photo, access=access, mobile_token="")
                        client.save()

                    redis_instance.set(auth_params.get("login") + "_access", str(access), ex=600)
                else:
                    return None

            rand_token = uuid4()
            client.access_token = rand_token
            redis_instance.set(auth_params.get("login") + "_access_token", str(rand_token), ex=60)
        else:
             return None
    else:
        if type == "token":
            response = check_crm_request({"Authorization": auth_params})
            if response:
                phone = response['phone']
                name = response['name']
                surname = response['surname']
                photo = response['photo']
                access = response['access']

                try:
                    client = Client.objects.get(phone=phone)
                    client.access = access
                    client.mobile_token = auth_params
                    client.photo = photo
                    client.save()
                except ObjectDoesNotExist:
                    client = Client(phone=phone, name=name, surname=surname, picture=photo, access=access, mobile_token=auth_params)
                    client.save()

                redis_instance.set(auth_params + "_access", str(access), ex=600)
            else:
                return None
        elif type == "login":
            response = check_crm_request({
                "login": auth_params.get("login"),
                "id1c": auth_params.get("id1c")
            })
            if response:
                phone = response['phone']
                name = response['name']
                surname = response['surname']
                photo = response['photo']
                access = response['access']

                try:
                    client = Client.objects.get(phone=phone)
                    client.access = access
                    client.photo = photo
                    client.save()
                except ObjectDoesNotExist:
                    client = Client(phone=phone, name=name, surname=surname, picture=photo, access=access, mobile_token="")
                    client.save()

                redis_instance.set(auth_params.get("login") + "_access", str(access), ex=600)
            else:
                return None

            rand_token = uuid4()
            client.access_token = rand_token
            redis_instance.set(auth_params.get("login") + "_access_token", str(rand_token), ex=60)
        else:
            return None

    return client

