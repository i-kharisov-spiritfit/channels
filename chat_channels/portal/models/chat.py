from main.models.chat import Line
import json

from django.db import models
from portal.crest import CRest, Utils
from django.http import HttpResponse, JsonResponse
import base64
from PIL import Image
from io import BytesIO
from django.conf import settings as project_settings



class prtl_Line(Line):
    portal_line_id = models.IntegerField("ID привязанной линии на портале", null=True, blank=True)
    icon = models.ImageField("Иконка для портала", upload_to='uploads/lines/icons/')

    def install_connector(self):
        self.icon.save(self.icon.name, self.icon.file)

        crest = CRest()

        binary_fc = open(self.icon.name, 'rb').read()
        base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')
        ext = self.icon.name.split('.')[-1]
        dataurl_active = f'data:image/{ext};base64,{base64_utf8_str}'

        with Image.open(self.icon.name) as img:
            img.load()

        img.convert("L")

        buffered = BytesIO()
        img.save(buffered, format=img.format)
        img_str = base64.b64encode(buffered.getvalue())
        dataurl_inactive = f'data:image/{ext};base64,{img_str.decode("utf-8")}'

        result = crest.call('imconnector.register', {
            'ID': self.id,
            'NAME': self.name,
            'ICON': {
                'DATA_IMAGE': dataurl_active,
                'COLOR': '#a6ffa3',
                'SIZE': '100%',
                'POSITION': 'center',
            },
            'ICON_DISABLED': {
                'DATA_IMAGE': dataurl_inactive,
                'SIZE': '100%',
                'POSITION': 'center',
                'COLOR': '#ffb3a3',
            },
            'PLACEMENT_HANDLER': f"https://"+project_settings.SITE_DOMAIN_NAME+"/portal/{self.id}/handler/"
        })

        if not Utils.empty(result.get('result')):
            resultEvent = crest.call(
                'event.bind',
                {
                    'event': 'OnImConnectorMessageAdd',
                    'handler': f"https://"+project_settings.SITE_DOMAIN_NAME+"/portal/{self.id}/message/"
                }
            )
            if not Utils.empty(resultEvent.get('result')):
                return HttpResponse("successfully")
            else:
                raise Exception(f"Не удалось установить коннектор на портале. Can't bind \"OnImConnectorMessageAdd\" event: {json.dumps(resultEvent)}")
        else:
            raise Exception(f"Не удалось установить коннектор на портале: {json.dumps(result)}")

    def uninstall_connector(self):
        crest = CRest()
        result = crest.call("imconnector.unregister", {
            "ID": self.id,
        })

        if not Utils.empty(result.get('result')):
            resultEvent = crest.call("event.unbind", {"event": "OnImConnectorMessageAdd",
                                                      "handler": f"https://"+project_settings.SITE_DOMAIN_NAME+"/portal/{self.id}/message/"})
            if not Utils.empty(resultEvent.get('result')):
                return HttpResponse("successfully")
            else:
                raise Exception(
                    f"Не удалось удалить коннектор на портале. Can't unbind \"OnImConnectorMessageAdd\" event: {json.dumps(resultEvent)}")
        else:
            raise Exception(f"Не удалось удалить коннектор на портале: {json.dumps(result)}")
