import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from main.models.members import User
from portal.crest import CRest
from portal.models.members import prtl_Operator
from portal.models.chat import prtl_Line
from main.models.chat import Message
from django.db.models import F
from datetime import datetime
from portal.tools import convertBB
import calendar


class Consumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def update_client_incr(self):
        User.objects.filter(pk=self.user.pk).update(connections=F('connections') + 1)

    @database_sync_to_async
    def update_client_decr(self):
        User.objects.filter(pk=self.user.pk).update(connections=F('connections') - 1)

    @database_sync_to_async
    def get_chat(self):
        chat_exist = self.user.chats.exists()
        if not chat_exist:
            chat = self.user.chats.create(line=self.line)
        else:
            chat = self.user.chats.first()

        return chat

    @database_sync_to_async
    def get_group_name(self):
        return f"{self.line.real_type._meta.app_label}.chat.{self.chat.id}"

    @database_sync_to_async
    def get_messages(self, offset=0, limit=1, timestamp=None):
        try:
            if timestamp:
                messages = Message.objects.filter(chat_id=self.chat.id,
                                                  timestamp__lte=datetime.fromtimestamp(timestamp)).order_by(
                    '-timestamp')[0:limit]
            else:
                messages = Message.objects.filter(chat_id=self.chat.id).order_by('-timestamp')[offset:limit]

            message_list = []
            for m in messages:
                message_item = {
                    "id": m.id,
                    "text": convertBB(m.text),
                    "timestamp": calendar.timegm(m.timestamp.utctimetuple()),
                    "owner": {
                        "name": m.owner.name,
                        "surname": m.owner.surname,
                        "picture": m.owner.picture,
                        "id": m.owner.pk,
                    },
                }

                if m.owner.real_type.name == User._meta.verbose_name:
                    message_item["owner"]["type"] = "client"
                elif m.owner.real_type.name == prtl_Operator._meta.verbose_name:
                    message_item["owner"]["type"] = "operator"
                else:
                    message_item["owner"]["type"] = "system"

                message_list.append(message_item)

            return message_list
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def set_message(self, text):
        message = Message(text=text, chat=self.chat, owner=self.user)
        message.save()

        return message.pk, message.timestamp

    async def connect(self):
        self.line: prtl_Line = self.scope.get('line')


        self.user: User = self.scope.get('user')
        self.chat = await self.get_chat()

        await self.accept()

        self.group_name = await self.get_group_name()

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.update_client_incr()

        messages = await self.get_messages(0, 25)

        await self.send(text_data=json.dumps({
            'event': "history",
            'messages': messages,
        }, indent=4, sort_keys=True, default=str))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(await self.get_group_name(), self.channel_name)
        await self.update_client_decr()

    async def receive(self, text_data=None, bytes_data=None):
        data_json = json.loads(text_data)
        action = data_json.get("action")

        if not action:
            await self.send(text_data=json.dumps({
                "event": "error",
                "message": "Не задан параметр action"
            }, indent=4, sort_keys=True, default=str))
            return

        if action == "send":
            text = data_json.get("text")
            if not text:
                await self.send(text_data=json.dumps({
                    "event": "error",
                    "message": "Пустой текст сообщения"
                }, indent=4, sort_keys=True, default=str))
                return

            if not self.line.portal_line_id:
                await self.send(text_data=json.dumps({
                    "event": "error",
                    "message": "Линия не активирована на портале"
                }, indent=4, sort_keys=True, default=str))
                return

            owner_type = "client"
            message_id, message_timestamp = await self.set_message(text)

            arMessage = {
                "user":{
                    'id': self.user.pk,
                    'name': self.user.name,
                    'picture': self.user.picture,
                    'phone': self.user.phone,
                    'skip_phone_validate': 'N'
                },
                'message':{
                    'id':message_id,
                    'date':message_timestamp.strftime('%s'),
                    'disable_crm':'N',
                    'text':text,
                    # 'files':None
                },
                'chat':{
                    'id':self.chat.id,
                }
            }


            _result = CRest().call('imconnector.send.messages', {
                'CONNECTOR': self.line.id,
                'LINE': self.line.portal_line_id,
                'MESSAGES': [arMessage]
            })

            await self.channel_layer.group_send(
                self.group_name, {
                    'type': 'message',
                    'text': text,
                    'owner': {
                        "type": owner_type,
                        "name": self.user.name,
                        "surname": self.user.surname,
                        "picture": self.user.picture,
                        "id": self.user.pk
                    },
                    'id': message_id,
                    'timestamp': calendar.timegm(message_timestamp.utctimetuple()),
                }
            )
        elif action == "history":
            offset = data_json.get("offset")
            limit = data_json.get("limit")
            timestamp = data_json.get("timestamp")

            if not offset:
                offset=0

            if not limit:
                limit=25

            messages = await self.get_messages(offset, limit, timestamp)
            await self.send(text_data=json.dumps({
                'event': "history",
                'messages': messages,
            }, indent=4, sort_keys=True, default=str))

    async def message(self, event):
        text = event["text"]
        owner = event["owner"]
        message_id = event["id"]
        timestamp = event["timestamp"]

        await self.send(text_data=json.dumps({
            'event': "send",
            'id': message_id,
            'text': convertBB(text),
            'owner': owner,
            'timestamp': timestamp
        }, indent=4, sort_keys=True, default=str))



