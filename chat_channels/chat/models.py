from django.db import models

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
    online = models.BooleanField('Онлайн')

    access = models.BooleanField('Доступен чат', default=True)
    mobile_token = models.CharField('Токен мобильного приложения', max_length=255, unique=True, blank=True)

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