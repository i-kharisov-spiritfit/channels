
from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Client, Chat, Message
from django.core.exceptions import ObjectDoesNotExist


class ChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def setClient(self, online=True):
        self.client.online=online
        self.client.save()

    @database_sync_to_async
    def getMessages(self, offset=0, limit=1):
        try:
            messages = Message.objects.filter(chat_id=self.chat.id).order_by('-timestamp')[offset:limit]

            message_list=[]
            for m in messages:
                message_item={
                    "id": m.id,
                    "text": m.text,
                    "timestamp": m.timestamp.strftime("%d.%m.%Y %H:%M"),
                    # "owner": m.owner.owner_type
                    "owner": {
                        "type":m.owner.owner_type,
                        "name":m.owner.name,
                        "surname":m.owner.surname,
                        "id":m.owner.pk
                    },
                }

                message_list.append(message_item)

            return message_list

        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def setChat(self, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
        except ObjectDoesNotExist:
            chat = Chat(id=chat_id)
            chat.save()

        self.client.chats.add(chat)
        return chat

    @database_sync_to_async
    def setMessage(self, text):
        message = Message(text=text, chat=self.chat, owner=self.client)
        message.save()

        return message.pk, message.timestamp


    async def connect(self):
        self.client = self.scope['client']

        if not self.client or not self.client.access:
            await self.close(code=4004)
            return

        self.chat=await self.setChat(self.scope['url_route']['kwargs']['chat_id'])

        await self.accept()
        await self.channel_layer.group_add(self.chat.id, self.channel_name)


        messages = await self.getMessages(0, 25)

        await self.send(text_data=json.dumps({
            'event': "history",
            'messages': messages,
        }, indent=4, sort_keys=True, default=str))




        count = getattr(self.channel_layer, f'count_{self.chat.id}', 0)
        if not count:
            print(f"{self.client.phone} ON_LINE")
            setattr(self.channel_layer, f'count_{self.chat.id}', 1)
        else:
            setattr(self.channel_layer, f'count_{self.chat.id}', count + 1)

        print(f"{self.client.phone} CONNECTED, ROOM: {self.chat.id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat.id, self.channel_name)

        print(f"{self.client.phone} DISCONNECTED, ROOM: {self.chat.id}, CLOSE CODE: {close_code}")

        count = getattr(self.channel_layer, f'count_{self.chat.id}', 0)
        setattr(self.channel_layer, f'count_{self.chat.id}', count - 1)
        if count == 1:
            delattr(self.channel_layer, f'count_{self.chat.id}')
            await self.setClient(False)

            print(f"{self.client.phone} OFF_LINE")


    async def receive(self, text_data=None, bytes_data=None):
        data_json = json.loads(text_data)
        action = data_json.get("action")

        if action == "send":
            text = data_json.get("text")

            if text:
                owner_type = "client"
                message_id, message_timestamp=await self.setMessage(text)

                # Send message to room group
                await self.channel_layer.group_send(
                    self.chat.id, {
                        'type': 'chat_message',
                        'text': text,
                        'owner': {
                            "type":owner_type,
                            "name":self.client.name,
                            "surname":self.client.surname,
                            "id":self.client.pk
                        },
                        'id': message_id,
                        'timestamp': message_timestamp.strftime("%d.%m.%Y %H:%M")
                    }
                )

        elif action == "history":
            offset=data_json.get("offset")
            limit = data_json.get("limit")

            if not offset:
                offset=0

            if not limit:
                limit=50

            messages = await self.getMessages(offset, limit)

            await self.send(text_data=json.dumps({
                'event': "history",
                'messages': messages,
            }, indent=4, sort_keys=True, default=str))


    async def chat_message(self, event):
        text = event["text"]
        owner = event["owner"]
        message_id = event["id"]
        timestamp = event["timestamp"]

        await self.send(text_data=json.dumps({
            'event': "send",
            'id': message_id,
            'text': text,
            'owner': owner,
            'timestamp': timestamp
        }, indent=4, sort_keys=True, default=str))