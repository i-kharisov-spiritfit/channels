import redis
import chat_channels.settings as settings
from main.models.members import User, Access
from main.models.chat import BlackList, Message
from django.core.exceptions import ObjectDoesNotExist
from uuid import uuid4
import requests
from datetime import datetime, timedelta
from django.utils import timezone

class UserAccess:
    def __init__(self, auth_params, line):
        self.line = line
        self.auth_params = auth_params
        self.access = False

        self.user = self.get_user()

    def get_user(self):
        if not isinstance(self.auth_params, dict):
            return None

        if self.auth_params.get("login"):
            login = self.auth_params.get("login")

            try:
                user = User.objects.get(phone=login)

                if (timezone.now() - timedelta(minutes=10)) < user.last_update_time:

                    try:
                        access_obj = Access.objects.get(member=user, line=self.line)
                        self.access = access_obj.access
                        return user

                    except ObjectDoesNotExist:
                        pass

            except ObjectDoesNotExist:
                pass

        if self.auth_params.get("login") and self.auth_params.get("id1c"):
            login = self.auth_params.get("login")
            id1c = self.auth_params.get("id1c")
            mobile_token = ""

            headers = {
                "login": login,
                "id1c": id1c,
                "line_id": self.line.id
            }
        elif self.auth_params.get("mobile_token"):
            mobile_token = self.auth_params.get("mobile_token")
            headers = {"Authorization": self.auth_params.get("mobile_token"), "line_id": self.line.id}

            try:
                user = User.objects.get(mobile_token=mobile_token)

                if (timezone.now() - timedelta(minutes=10)) < user.last_update_time:

                    try:
                        access_obj = Access.objects.get(member=user, line=self.line)
                        self.access = access_obj.access
                        return user

                    except ObjectDoesNotExist:
                        pass

            except ObjectDoesNotExist:
                pass

        else:
            return None


        r = requests.get(
            url="https://1c.spiritfit.ru/fitness-test1/hs/website/chats",
            headers=headers
        )
        json_data = r.json()
        response = json_data.get("result")
        if response and json_data.get("success"):
            phone = response['phone']
            name = response['name']
            surname = response['surname']
            photo = response['photo']

            self.access = response['access']

            values_for_update={
                'phone':phone,
                'name':name,
                'surname':surname,
                'picture':photo,
                'mobile_token':mobile_token,
                'last_update_time':timezone.now()
            }

            user, created = User.objects.update_or_create(phone=phone, defaults=values_for_update)

            Access.objects.update_or_create(
                line=self.line,
                member=user,
                defaults={'access':self.access}
            )

            return user
        else:
            return None

    def in_blacklist(self, chat):
        try:
            b = BlackList.objects.get(member=self.user, chat=chat)
            return b.status
        except ObjectDoesNotExist:
            return False

    def check_line_access_by_token(self):
        redis_instance = redis.Redis(host=settings.REDIS_HOST,
                                     port=settings.REDIS_PORT, db=0)

        if not isinstance(self.auth_params, dict):
            redis_instance.close()
            return False

        if self.auth_params.get("login") and self.auth_params.get("token"):
            access_token = redis_instance.get(self.user.phone + "_access_token")
            if not access_token or access_token.decode() != self.auth_params.get("token"):
                redis_instance.close()
                return False

            redis_instance.delete(self.user.phone + "_access_token")
            redis_instance.close()
            return True

    def get_access_token(self):
        redis_instance = redis.Redis(host=settings.REDIS_HOST,
                                     port=settings.REDIS_PORT, db=0)

        if not isinstance(self.auth_params, dict):
            redis_instance.close()
            return None

        if not self.user or not self.access:
            return None

        rand_token = uuid4()
        redis_instance.set(self.user.phone + "_access_token", str(rand_token), ex=60)
        redis_instance.close()
        return rand_token


def send_push(user, message:Message):
    if not user.mobile_token:
        return

    headers = {"Authorization": user.mobile_token}
    data = {
        "lineID":message.chat.line.id,
        "chatID":message.chat.id,
        "messageID":message.pk
    }

    r = requests.post(
        url="https://1c.spiritfit.ru/fitness-test1/hs/website/chats",
        headers=headers,
        json=data
    )




def crm_request__get_user(headers):
    with open("logs.log", 'a', encoding='utf-8') as file:
        file.write(f"++++++\n{datetime.now()}::Отправляюю запрос в 1С:\n {headers}\n++++++\n")

    r = requests.get(
        url="https://1c.spiritfit.ru/fitness-test1/hs/website/chats",
        headers=headers
    )

    json_data = r.json()

    response = json_data.get("result")
    if response and json_data.get("success"):
        return response
    else:
        return None


def check_client_access(auth_params, line):
    redis_instance = redis.Redis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT, db=0)

    if isinstance(auth_params, dict) and auth_params.get("login"):
        login = auth_params.get("login")
        access_key = login + "_access"
        type = "LOGIN"

        if not auth_params.get("id1c"):
            access_token = redis_instance.get(login + "_access_token")

            if not access_token or access_token.decode() != auth_params.get("token"):
                return None

            try:
                client = User.objects.get(phone=login)
                redis_instance.delete(login + "_access_token")
                return client
            except ObjectDoesNotExist:
                return None


    elif isinstance(auth_params, str):
        token = auth_params
        access_key = token + "_access"
        type = "TOKEN"

    else:
        redis_instance.close()
        return None

    access = redis_instance.get(access_key)


    if access != None:
        access = bool(access.decode())

    if type == "TOKEN":
        mobile_token = auth_params
        headers = {"Authorization": mobile_token}

        try:
            client = User.objects.get(mobile_token=mobile_token)
            if access:
                redis_instance.close()
                return client
        except ObjectDoesNotExist:
            client = None

    elif type == "LOGIN":
        mobile_token = ""
        headers = {
            "login": login,
            "id1c": auth_params.get("id1c")
        }

        try:
            client = User.objects.get(phone=login)
            if access:
                rand_token = uuid4()
                client.access_token = rand_token
                redis_instance.set(login + "_access_token", str(rand_token), ex=60)
                redis_instance.close()
                return client
        except ObjectDoesNotExist:
            client = None

    else:
        redis_instance.close()
        return None


    response = crm_request__get_user(headers)
    if not response:
        redis_instance.close()
        return None


    phone = response['phone']
    name = response['name']
    surname = response['surname']
    photo = response['photo']

    if bool(line.open):
        access = True
    else:
        access = response['access']


    if not client:
        client = User(phone=phone, name=name, surname=surname, picture=photo,
                      mobile_token=mobile_token)
        client.save()

    else:
        client.mobile_token = auth_params
        client.photo = photo
        client.save()

    access_obj, created = Access.objects.update_or_create(
        line=line,
        member=client,
        access=bool(access)
    )

    redis_instance.set(access_key, str(access), ex=600)

    if type=="LOGIN":
        rand_token = uuid4()
        client.access_token = rand_token
        redis_instance.set(login + "_access_token", str(rand_token), ex=60)

    redis_instance.close()

    return client

