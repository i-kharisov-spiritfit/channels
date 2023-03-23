from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer, channel_layers, DEFAULT_CHANNEL_LAYER
from asgiref.sync import async_to_sync
from ..models import Client, Message, Operator, Chat, Settings
from django.core.exceptions import ObjectDoesNotExist
import requests
from ..import CRest, PHP
from django.http import HttpResponse, JsonResponse
from .. import functions
import calendar
from django.core.handlers.wsgi import WSGIRequest
from chat_channels.settings import CONNECTORS

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
def install(request):
    result = CRest().installApp(request)
    if result.get('rest_only') and result.get('rest_only')==False:
        page = '<head><script src="//api.bitrix24.com/api/v1/"></script>'
        if result.get('install') == True:
            page+= '<script>BX24.init(function(){BX24.installFinish();});</script>'

        page+='</head>'

        if result.get('install') == True:
            str = 'installation has been finished'
        else:
            str = 'installation error'

        page+=f'<body>{str}<pre>{json.dumps(result, indent=4)}</pre></body>'
        return HttpResponse(content=page)

    return HttpResponse(content=json.dumps(result, indent=4), content_type="application/json")

@csrf_exempt
def handler(request):
    widgetUri = CONNECTORS["mobile_app"]["widgetUri"]
    widgetName = CONNECTORS["mobile_app"]["name"]


    crest = CRest()
    _request = crest.getRequestParams(request)

    if not PHP.empty(_request.get('PLACEMENT_OPTIONS')) and _request.get('PLACEMENT') == 'SETTING_CONNECTOR':
        #activate connector
        options = json.loads(_request.get('PLACEMENT_OPTIONS'))
        result = crest.call('imconnector.activate', {
            'CONNECTOR':CONNECTORS["mobile_app"]["id"],
            'LINE': int(options['LINE']),
            'ACTIVE': int(options['ACTIVE_STATUS']),
        })

        if not PHP.empty(result):
            #add data widget
            if not PHP.empty(widgetUri) and not PHP.empty(widgetName):
                resultWidgetData = crest.call('imconnector.connector.data.set', {
                    'CONNECTOR':CONNECTORS["mobile_app"]["id"],
                    'LINE':int(options['LINE']),
                    'DATA':{
                        'id':CONNECTORS["mobile_app"]["id"]+'line'+str(options['LINE']),
                        'url_im': widgetUri,
                        'name': widgetName
                    }
                })

                if not PHP.empty(resultWidgetData):
                    try:
                        settings = Settings.objects.get(pk=1)
                        settings.line = options['LINE']
                    except ObjectDoesNotExist:
                        settings = Settings(pk=1, line=options['LINE'])
                    settings.save()

            else:
                try:
                    settings = Settings.objects.get(pk=1)
                    settings.line = options['LINE']
                except ObjectDoesNotExist:
                    settings = Settings(pk=1, line=options['LINE'])
                settings.save()

            return HttpResponse("successfully")

    if _request.get('event') == 'ONIMCONNECTORMESSAGEADD' and \
            not PHP.empty(_request.get('data')) and not PHP.empty(_request['data'].get('CONNECTOR')) and _request.get('data').get('CONNECTOR') == CONNECTORS["mobile_app"]["id"] and \
            not PHP.empty(_request.get('data').get('MESSAGES')):

        messages = _request.get('data').get('MESSAGES')

        deliveryMessages = []
        for m in messages.values():
            chat_id = m['chat']['id']
            try:
                Chat.objects.get(pk=chat_id)
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps({"result": False, "error": "can't find chat"}), status=502)


            operator_id = m['message']['user_id']
            try:
                operator = Operator.objects.get(out_id=operator_id)
                operator.chats.add(chat_id)
            except Operator.DoesNotExist:
                # TODO: вызвать рест на битрикс для получения информации о пользователе by json_data["user_id"]
                # https://dev.1c-bitrix.ru/rest_help/users/user_get.php

                _response = CRest().call('user.get', {'ID' : operator_id})
                if _response.get('result'):
                    user = _response.get('result')[0]
                    operator = Operator(name=user.get("NAME") if user.get("NAME") else "unname", surname=user.get("LAST_NAME") if user.get("LAST_NAME") else "unsurname", picture=user.get("PERSONAL_PHOTO"), out_id=operator_id)
                else:
                    operator = Operator(name="unname", surname="unname", out_id=operator_id)
                    operator.chats.add(chat_id)

                operator.save()
                operator.chats.add(chat_id)

            message = Message(text=m['message']['text'], chat_id=chat_id, owner=operator)
            message.save()

            clients = Client.objects.filter(chats__id=chat_id)
            for client in clients:
                if client.online:
                    data = {
                        'type': 'chat_message',
                        'text': functions.convertBB(m['message']['text']),
                        'owner': {
                            "type": operator.owner_type,
                            "name": operator.name,
                            "surname": operator.surname,
                            "picture":operator.picture,
                            "id": operator.pk
                        },
                        'id': message.pk,
                        'timestamp': calendar.timegm(message.timestamp.utctimetuple()),
                    }

                    async_to_sync(closing_send)(chat_id, data)

                    deliveryMessages.append(
                        {
                            'im':m['im'],
                            'message':{
                                'id':message.pk
                            },
                            'chat':{
                                'id':chat_id
                            }
                        }
                    )
                else:
                    if client.mobile_token:
                        # Посылаем запрос на пуш
                        r = requests.post(
                            url="https://app.spiritfit.ru/fitness-test1/hs/website/chats",
                            headers={
                                "Authorization": client.mobile_token
                            }
                        )

                        response = r.json()
                        if response.get("result"):
                            deliveryMessages.append(
                                {
                                    'im': m['im'],
                                    'message': {
                                        'id': message.pk
                                    },
                                    'chat': {
                                        'id': chat_id
                                    }
                                }
                            )
                        else:
                            return JsonResponse({"result":False, "errorCode":1, "message": "Не удалось отправить PUSH"}, status=502)

                    else:
                        return JsonResponse({"result":False, "errorCode":1, "message": "Не удалось найти токен клиента"}, status=400)

        if not PHP.empty(deliveryMessages):
            CRest().call('imconnector.send.status.delivery', {
                'CONNECTOR': _request['data'].get('CONNECTOR'),
                'LINE': functions.get_line(),
                'MESSAGES': deliveryMessages
            })

            return HttpResponse("ok", status=200)

@csrf_exempt
def install_connector(request):
    crest = CRest()
    _request = crest.getRequestParams(request)

    with open('log.log', 'a', encoding='utf-8') as file:
        file.write(json.dumps(_request))

    if not PHP.empty(_request.get("UNINSTALL")):
        result = crest.call("imconnector.unregister", {
            "ID":CONNECTORS["mobile_app"]["id"],
        })

        resultEvent = crest.call("event.unbind", {"event":"OnImConnectorMessageAdd", "handler": CONNECTORS["mobile_app"]["handler_url"]})

        return HttpResponse(content=json.dumps(resultEvent), content_type='application/json')

    result = crest.call('imconnector.register', {
        'ID':CONNECTORS["mobile_app"]["id"],
        'NAME':CONNECTORS["mobile_app"]["name"],
        'ICON':{
            'DATA_IMAGE':'data:image/svg+xml;charset=US-ASCII,%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20x%3D%220px%22%20y%3D%220px%22%0A%09%20viewBox%3D%220%200%2070%2071%22%20style%3D%22enable-background%3Anew%200%200%2070%2071%3B%22%20xml%3Aspace%3D%22preserve%22%3E%0A%3Cpath%20fill%3D%22%230C99BA%22%20class%3D%22st0%22%20d%3D%22M34.7%2C64c-11.6%2C0-22-7.1-26.3-17.8C4%2C35.4%2C6.4%2C23%2C14.5%2C14.7c8.1-8.2%2C20.4-10.7%2C31-6.2%0A%09c12.5%2C5.4%2C19.6%2C18.8%2C17%2C32.2C60%2C54%2C48.3%2C63.8%2C34.7%2C64L34.7%2C64z%20M27.8%2C29c0.8-0.9%2C0.8-2.3%2C0-3.2l-1-1.2h19.3c1-0.1%2C1.7-0.9%2C1.7-1.8%0A%09v-0.9c0-1-0.7-1.8-1.7-1.8H26.8l1.1-1.2c0.8-0.9%2C0.8-2.3%2C0-3.2c-0.4-0.4-0.9-0.7-1.5-0.7s-1.1%2C0.2-1.5%2C0.7l-4.6%2C5.1%0A%09c-0.8%2C0.9-0.8%2C2.3%2C0%2C3.2l4.6%2C5.1c0.4%2C0.4%2C0.9%2C0.7%2C1.5%2C0.7C26.9%2C29.6%2C27.4%2C29.4%2C27.8%2C29L27.8%2C29z%20M44%2C41c-0.5-0.6-1.3-0.8-2-0.6%0A%09c-0.7%2C0.2-1.3%2C0.9-1.5%2C1.6c-0.2%2C0.8%2C0%2C1.6%2C0.5%2C2.2l1%2C1.2H22.8c-1%2C0.1-1.7%2C0.9-1.7%2C1.8v0.9c0%2C1%2C0.7%2C1.8%2C1.7%2C1.8h19.3l-1%2C1.2%0A%09c-0.5%2C0.6-0.7%2C1.4-0.5%2C2.2c0.2%2C0.8%2C0.7%2C1.4%2C1.5%2C1.6c0.7%2C0.2%2C1.5%2C0%2C2-0.6l4.6-5.1c0.8-0.9%2C0.8-2.3%2C0-3.2L44%2C41z%20M23.5%2C32.8%0A%09c-1%2C0.1-1.7%2C0.9-1.7%2C1.8v0.9c0%2C1%2C0.7%2C1.8%2C1.7%2C1.8h23.4c1-0.1%2C1.7-0.9%2C1.7-1.8v-0.9c0-1-0.7-1.8-1.7-1.9L23.5%2C32.8L23.5%2C32.8z%22/%3E%0A%3C/svg%3E%0A',
            'COLOR' : '#a6ffa3',
            'SIZE' : '100%',
            'POSITION' : 'center',
        },
        'ICON_DISABLED':{
            'DATA_IMAGE':'data:image/svg+xml;charset=US-ASCII,%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20x%3D%220px%22%20y%3D%220px%22%0A%09%20viewBox%3D%220%200%2070%2071%22%20style%3D%22enable-background%3Anew%200%200%2070%2071%3B%22%20xml%3Aspace%3D%22preserve%22%3E%0A%3Cpath%20fill%3D%22%230C99BA%22%20class%3D%22st0%22%20d%3D%22M34.7%2C64c-11.6%2C0-22-7.1-26.3-17.8C4%2C35.4%2C6.4%2C23%2C14.5%2C14.7c8.1-8.2%2C20.4-10.7%2C31-6.2%0A%09c12.5%2C5.4%2C19.6%2C18.8%2C17%2C32.2C60%2C54%2C48.3%2C63.8%2C34.7%2C64L34.7%2C64z%20M27.8%2C29c0.8-0.9%2C0.8-2.3%2C0-3.2l-1-1.2h19.3c1-0.1%2C1.7-0.9%2C1.7-1.8%0A%09v-0.9c0-1-0.7-1.8-1.7-1.8H26.8l1.1-1.2c0.8-0.9%2C0.8-2.3%2C0-3.2c-0.4-0.4-0.9-0.7-1.5-0.7s-1.1%2C0.2-1.5%2C0.7l-4.6%2C5.1%0A%09c-0.8%2C0.9-0.8%2C2.3%2C0%2C3.2l4.6%2C5.1c0.4%2C0.4%2C0.9%2C0.7%2C1.5%2C0.7C26.9%2C29.6%2C27.4%2C29.4%2C27.8%2C29L27.8%2C29z%20M44%2C41c-0.5-0.6-1.3-0.8-2-0.6%0A%09c-0.7%2C0.2-1.3%2C0.9-1.5%2C1.6c-0.2%2C0.8%2C0%2C1.6%2C0.5%2C2.2l1%2C1.2H22.8c-1%2C0.1-1.7%2C0.9-1.7%2C1.8v0.9c0%2C1%2C0.7%2C1.8%2C1.7%2C1.8h19.3l-1%2C1.2%0A%09c-0.5%2C0.6-0.7%2C1.4-0.5%2C2.2c0.2%2C0.8%2C0.7%2C1.4%2C1.5%2C1.6c0.7%2C0.2%2C1.5%2C0%2C2-0.6l4.6-5.1c0.8-0.9%2C0.8-2.3%2C0-3.2L44%2C41z%20M23.5%2C32.8%0A%09c-1%2C0.1-1.7%2C0.9-1.7%2C1.8v0.9c0%2C1%2C0.7%2C1.8%2C1.7%2C1.8h23.4c1-0.1%2C1.7-0.9%2C1.7-1.8v-0.9c0-1-0.7-1.8-1.7-1.9L23.5%2C32.8L23.5%2C32.8z%22/%3E%0A%3C/svg%3E%0A',
            'SIZE':'100%',
            'POSITION':'center',
            'COLOR': '#ffb3a3',
        },
        'PLACEMENT_HANDLER':CONNECTORS["mobile_app"]["handler_url"]
    })

    if not PHP.empty(result.get('result')):
        resultEvent = crest.call(
            'event.bind',
            {
                'event':'OnImConnectorMessageAdd',
                'handler':CONNECTORS["mobile_app"]["handler_url"]
            }
        )
        if not PHP.empty(resultEvent.get('result')):
            return HttpResponse("successfully")
        else:
            HttpResponse(content=json.dumps(resultEvent), content_type='application/json')
    else:
        return JsonResponse(result)

@csrf_exempt
def check_user(request: WSGIRequest):
    try:
        print(request.body)
        params = json.loads(request.body.decode())
    except ValueError:
        return JsonResponse({"result": False, "error": "Не удалось распознать json, передан неправильный json"}, status=400)

    if not params.get("login"):
        return JsonResponse({"result": False, "error": "Отсутствует обязательный параметр login"}, status=400)

    if not params.get("id1c"):
        return JsonResponse({"result": False, "error": "Отсутствует обязательный параметр id1c"}, status=400)

    client = functions.check_client(params)


    if client:
        return JsonResponse({
            "result":client.access,
            "access_token": client.access_token
        })
    else:
        return JsonResponse({
            "result": False
        })