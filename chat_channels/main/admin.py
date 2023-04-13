from django.contrib import admin

# Register your models here.
from .models import User, Chat, Access, Message

class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "surname")
    readonly_fields = ('id', "connections", "chats")
admin.site.register(User, UserAdmin)


class ChatAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Chat, ChatAdmin)

class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ('id', "chat", "owner", "text")
    list_display = ("id", "chat", "owner")
admin.site.register(Message, MessageAdmin)

class AccessAdmin(admin.ModelAdmin):
    readonly_fields = ('id', "member", "line")
admin.site.register(Access, AccessAdmin)
