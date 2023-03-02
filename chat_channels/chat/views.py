from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer, channel_layers, DEFAULT_CHANNEL_LAYER
from asgiref.sync import async_to_sync
from .models import Client, Message, Operator, Chat
from django.core.exceptions import ObjectDoesNotExist
import requests

# Create your views here.

import json


def index(request):
    """Главная страница"""
    return "Главная страница"

async def closing_send(room_name, data):
    channel_layer = get_channel_layer()
    # print(channel_layer.__dict__)

    await channel_layer.group_send(room_name, data)
    await channel_layer.close_pools()

@csrf_exempt
def send_to_chat(request):
    """"""
    json_data=json.loads(request.body)

    client_id = json_data["client_id"]
    chat_id = json_data["chat_id"]
    try:
        client=Client.objects.get(pk=client_id)
    except ObjectDoesNotExist:
        return HttpResponse(json.dumps({"result":False, "error":"can't find client"}), status=502)

    try:
        client.chats.get(id=chat_id)
    except ObjectDoesNotExist:
        return HttpResponse(json.dumps({"result":False, "error":"can't find chat"}), status=502)

    try:
        operator = Operator.objects.get(out_id=json_data["user_id"])
        operator.chats.add(json_data["chat_id"])
    except Operator.DoesNotExist:
        #TODO: вызвать рест на битрикс для получения информации о пользователе by json_data["user_id"]
        #https://dev.1c-bitrix.ru/rest_help/users/user_get.php

        operator = Operator(name="un_name", surname="un_surname", out_id=json_data["user_id"])
        operator.save()
        operator.chats.add(json_data["chat_id"])


    message = Message(text=json_data["text"], chat_id=json_data["chat_id"], owner=operator)
    message.save()




    if client.online:
        data={
            'type': 'chat_message',
            'text': json_data["text"],
             'owner':{
                 "type": operator.owner_type,
                 "name": operator.name,
                 "surname": operator.surname,
                 "id": operator.pk
             },
            'id': message.pk,
            'timestamp': message.timestamp.strftime("%d.%m.%Y %H:%M")
        }

        async_to_sync(closing_send)(json_data["chat_id"], data)
        return HttpResponse("sending with socket")
    else:
        if client.mobile_token:
            #Посылаем запрос на пуш
            r=requests.post(
                url="https://app.spiritfit.ru/fitness-test1/hs/website/chats",
                headers={
                    "Authorization": client.mobile_token
                }
            )

            response=r.json()
            if response["result"]:
                return HttpResponse("sending with push")
            else:
                return HttpResponse("fail on send with push")

        else:
            return HttpResponse("can't find client token")





