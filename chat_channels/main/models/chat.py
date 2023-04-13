from django.db import models
from . import InheritanceCastModel

class Line(InheritanceCastModel):
    id = models.CharField("ID линии ", primary_key=True, max_length=255)
    name = models.CharField("Название линии", default="Открытая линия Spirit. Fitness!", max_length=255)
    open = models.BooleanField("Открытый чат", default=True, null=False)

    def __str__(self):
        return self.name

class Chat(models.Model):
    id = models.AutoField('ID', primary_key=True)
    line = models.ForeignKey(Line, on_delete=models.CASCADE)

    def __str__(self):
        return f"Чат №{self.id}"


class Message(models.Model):
    text = models.TextField('Текст сообщения')
    timestamp = models.DateTimeField('Дата и время сообщения', auto_now_add=True)
    chat = models.ForeignKey("main.Chat", on_delete=models.CASCADE)
    owner = models.ForeignKey("main.Member", on_delete=models.CASCADE)

    def __str__(self):
        return f"Сообщение №{self.pk}"

class BlackList(models.Model):
    member = models.ForeignKey("main.Member", on_delete=models.CASCADE)
    chat = models.ForeignKey("main.Chat", on_delete=models.CASCADE)
    status = models.BooleanField(default=False)