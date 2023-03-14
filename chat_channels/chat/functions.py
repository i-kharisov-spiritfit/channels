from . import CRest
import re
from .models import Settings
from channels.db import database_sync_to_async

def get_connector_id():
    return 'mobile_chat_connector'

@database_sync_to_async
def get_line_async():
    try:
        s = Settings.objects.get(pk=1)
        return s.line
    except Exception as err:
        print(err)
        return False


def get_line():
    try:
        s = Settings.objects.get(pk=1)
        return s.line
    except Exception as err:
        print(err)
        return False

def convertBB(var):
    search = [
        r'\[b\](.+)\[/b\]',
        r'\[br\]',
        r'\[i\](.+)\[/i\]',
        r'\[u\](.+)\[/u\]',
        r'\[img\](.+)\[/img\]',
        r'\[url\](.+)\[/url\]',
        r'\[url\=(.+)\](.+)\[/url\]',
    ]

    replace = [
        r'<strong>\1</strong>',
        '<br>',
        r'<em>\1</em>',
        r'<u>\1</u>',
        r'<img src="\1" />',
        r'<a href="\1">\1</a>',
        r'<a href="\1">\2</a>',
    ]

    for i in range(len(search)):
        var = re.sub(search[i], replace[i], var)

    return var