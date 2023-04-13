from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.handlers.wsgi import WSGIRequest
import json
from main.models.chat import Line
from django.core.exceptions import ObjectDoesNotExist
from main.tools.crm import UserAccess
from portal.crest import CRest, Utils
from portal.models.members import prtl_Operator
from main.models.chat import Message
from main.models.members import User
from main.tools.crm import send_push
from portal.tools import convertBB
import calendar

@csrf_exempt
def get_access(request: WSGIRequest, line_id=None):
    try:
        params = json.loads(request.body.decode())
    except ValueError:
        return JsonResponse({"result": False, "error": "Не удалось распознать json, передан неправильный json"}, status=400)


    if params.get("token"):
        params = params.get("token")
    else:
        if not params.get("login"):
            return JsonResponse({"result": False, "error": "Отсутствует обязательный параметр login"}, status=400)

        if not params.get("id1c"):
            return JsonResponse({"result": False, "error": "Отсутствует обязательный параметр id1c"}, status=400)

    if not line_id:
        line_id = "online_coach_connector"
    try:
        line = Line.objects.get(id=line_id)
    except ObjectDoesNotExist:
        return JsonResponse({"result": False, "error": f"Линия {line_id} не существует"}, status=400)

    a = UserAccess(params, line)


    if not a.access:
        return JsonResponse({
            "result": False
        }, status=403)

    return JsonResponse({
        "result": a.access,
        "access_token": a.get_access_token()
    })

@csrf_exempt
def handler(request:WSGIRequest, line_id = None):
    try:
        line = Line.objects.get(id=line_id)
    except ObjectDoesNotExist:
        line = None

    if not line:
        try:
            line = Line.objects.get(id="online_coach_connector")
        except ObjectDoesNotExist:
            return JsonResponse({"result": False, "error": "Линия не найдена"}, status=400)

    line = line.cast()

    crest = CRest()
    _request = crest.getRequestParams(request)
    if not Utils.empty(_request.get('PLACEMENT_OPTIONS')) and _request.get('PLACEMENT') == 'SETTING_CONNECTOR':
        options = json.loads(_request.get('PLACEMENT_OPTIONS'))
        result = crest.call('imconnector.activate', {
            'CONNECTOR': line.id,
            'LINE': int(options['LINE']),
            'ACTIVE': int(options['ACTIVE_STATUS']),
        })

        if not Utils.empty(result):
            crest.call('imconnector.connector.data.set', {
                'CONNECTOR': line.id,
                'LINE': int(options['LINE']),
                'DATA': {
                    'id': line.id + '_line' + str(options['LINE']),
                    'url_im': "",
                    'name': line.name
                }
            })

            line.portal_line_id = int(options['LINE'])
            line.save()

        return HttpResponse("Линия успешно активирована")

    return HttpResponse("Неизвестный запрос", status=400)

@csrf_exempt
def message(request, line_id):
    try:
        line = Line.objects.get(id=line_id)
    except ObjectDoesNotExist:
        line = None

    if not line:
        try:
            line = Line.objects.get(id="online_coach_connector")
        except ObjectDoesNotExist:
            return JsonResponse({"result": False, "error": "Линия не найдена"}, status=400)

    line = line.cast()
    crest = CRest()
    _request = crest.getRequestParams(request)

    with open("logs.log", "a") as file:
        file.write(str(_request)+"\n")

    if _request.get('event') == 'ONIMCONNECTORMESSAGEADD' and \
            not Utils.empty(_request.get('data')) and not Utils.empty(
        _request['data'].get('CONNECTOR')) and _request.get(
        'data').get('CONNECTOR') == line.id and \
            not Utils.empty(_request.get('data').get('MESSAGES')):
        messages = _request.get('data').get('MESSAGES')

        deliveryMessages = []

        for m in messages.values():
            chat_id = m['chat']['id']

            try:
                chat = line.chat_set.get(id=chat_id)
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps({"result": False, "error": "Чат не найден"}), status=400)

            operator_id = m['message']['user_id']

            operator, created = prtl_Operator.objects.get_or_create(portal_user_id=operator_id)
            operator.chats.add(chat_id)

            if created:
                _response = CRest().call('user.get', {'ID': operator_id})
                if _response.get('result'):
                    user = _response.get('result')[0]
                    name = user.get("NAME") if user.get("NAME") else "Без имени"
                    surname = user.get("LAST_NAME") if user.get("LAST_NAME") else "Без фамилии"
                    picture = user.get("PERSONAL_PHOTO")
                else:
                    name = "Без имени"
                    surname = "Без фамилии"
                    picture = None

                operator.name = name
                operator.surname = surname
                operator.picture = picture

            operator.save()
            message = Message(text=m['message']['text'], chat_id=chat_id, owner=operator)
            message.save()

            users = User.objects.filter(chats__id=chat_id)
            for u in users:
                if u.connections == 0:
                    send_push(u, message)

            data = {
                "type":"message",
                "text":convertBB(message.text),
                "id": message.pk,
                "timestamp": calendar.timegm(message.timestamp.utctimetuple()),
                "owner":{
                    "type": "operator",
                    "name": operator.name,
                    "surname": operator.surname,
                    "picture": operator.picture,
                    "id": operator.pk
                }
            }

            group_name = f"{line.real_type._meta.app_label}.chat.{chat_id}"
            async_to_sync(closing_send)(group_name, data)

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

        if not Utils.empty(deliveryMessages):
            CRest().call('imconnector.send.status.delivery', {
                'CONNECTOR': _request['data'].get('CONNECTOR'),
                'LINE': line.id,
                'MESSAGES': deliveryMessages
            })

            return HttpResponse("ok", status=200)



async def closing_send(group_name, data):
    channel_layer = get_channel_layer()
    # print(channel_layer.__dict__)

    await channel_layer.group_send(group_name, data)
    await channel_layer.close_pools()