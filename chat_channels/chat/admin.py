from django.contrib import admin

# Register your models here.
from .models import Client, Chat, Message, Operator


class ClientAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Client, ClientAdmin)

class ChatAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Chat, ChatAdmin)

class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Message, MessageAdmin)

class OperatorAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Operator, OperatorAdmin)