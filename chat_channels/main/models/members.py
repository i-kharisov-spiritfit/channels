from django.db import models
from . import InheritanceCastModel

class Member(InheritanceCastModel):
    name = models.CharField('Имя', max_length=255, null=True, blank=True)
    surname = models.CharField('Фамилия', max_length=255, null=True, blank=True)
    picture = models.CharField('URL на аватарку', max_length=255, null=True, blank=True)
    chats = models.ManyToManyField("main.Chat")

    def __str__(self):
        return f"{self.name} {self.surname}"

class User(Member):
    connections = models.IntegerField("Кол-во соединений по сокету", default=0, null=False)
    phone = models.CharField('Номер телефона', max_length=10, unique=True, null=False)
    email = models.EmailField('Email', null=True, blank=True)
    mobile_token = models.CharField('Токен мобильного приложения', max_length=255, unique=True, blank=True)

    last_update_time = models.DateTimeField('Последнее обновление из CRM', auto_now_add=True)



class Access(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    line = models.ForeignKey("main.Line", on_delete=models.CASCADE)
    access = models.BooleanField("Есть доступ к линии", default=False, null=False)

    def __str__(self):
        return f"Пользователь {self.member}. Доступ к линии \"{self.line}\""