from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from main.models.members import User



class Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
