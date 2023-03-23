from django.db import models
import redis
import chat_channels.settings as settings

# Create your models here.


class Chat(models.Model):
    id=models.CharField('ID', max_length=255, primary_key=True)

class ChatMember(models.Model):
    name = models.CharField('Имя', max_length=255, null=True, blank=True)
    surname = models.CharField('Фамилия', max_length=255, null=True, blank=True)
    picture = models.CharField('URL на аватарку', max_length=255, null=True, blank=True)

    chats = models.ManyToManyField(Chat)

    owner_type = models.CharField(max_length=10, default="unknown")

class Client(ChatMember):
    phone = models.CharField('Номер телефона', max_length=10, unique=True, null=False)
    email = models.EmailField('Email', null=True, blank=True)
    access = models.BooleanField('Доступен чат', default=True)
    mobile_token = models.CharField('Токен мобильного приложения', max_length=255, unique=True, blank=True)

    @property
    def online(self):
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT, db=0)
        online = redis_instance.get(f"{self.phone}_online")
        redis_instance.close()

        if not online == None:
            online = bool(online.decode())
            return online
        else:
            return False

    @online.setter
    def online(self, online):
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT, db=0)
        redis_instance.set(f"{self.phone}_online", str(online), ex=60)
        redis_instance.close()


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.owner_type="client"
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return str((self.name, self.phone, self.online))

class Operator(ChatMember):
    out_id=models.IntegerField('ID на портале', unique=True, null=False, blank=False)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.owner_type="operator"
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return str((self.out_id, self.name))

class Message(models.Model):
    text = models.TextField('Текст сообщения')
    timestamp = models.DateTimeField('Дата и время сообщения', auto_now_add=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    owner = models.ForeignKey(ChatMember, on_delete=models.CASCADE)

class Settings(models.Model):
    line = models.IntegerField('ID линии на портале')