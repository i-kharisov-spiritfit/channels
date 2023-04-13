from django.apps import AppConfig
import os


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        print(os.environ.get('SERVER_GATEWAY_INTERFACE'))

        if os.environ.get('SERVER_GATEWAY_INTERFACE') == "ASGI":
            from main.models.members import User

            User.objects.update(connections=0)