import json
from django.utils.html import escape
import os
from datetime import datetime

C_REST_CLIENT_ID = 'local.63da805125bcf4.68832546'                              #Application ID
C_REST_CLIENT_SECRET = '73AtBwpgkH0rl5xUbXEj5EZIkCJbddd15rZIkeplazTEmZlV7x'     #Application key

C_REST_BLOCK_LOG = True
C_REST_LOGS_DIR = os.path.dirname(os.path.realpath(__file__)) + '/logs/'


from django.core.handlers.wsgi import WSGIRequest
import urllib.parse


class CRest:
    VERSION = 1.36
    BATCH_COUNT = 50
    TYPE_TRANSPORT = 'json'

    def getRequestParams(self, request: WSGIRequest):
        if request.method == "GET":
            params = request.GET
        else:
            params = json.loads(request.body)

        return params


    def DoResust(self, params):
        settings = self.getAppSettings()
        if settings:
            if params.get('this_auth') == 'Y':
                url = 'https://oauth.bitrix.info/oauth/token/'
            else:
                url = settings['client_endpoint'] + params['method'] + '.' + self.TYPE_TRANSPORT
                if not settings.get('is_web_hook') or settings.get('is_web_hook')!='Y':
                    params['params']['auth'] = settings['access_token']

            s_post_fields = urllib.parse.urlencode(params['params'])





    def installApp(self, request: WSGIRequest):
        result={
            'rest_only': True,
            'install': False
        }

        params = self.getRequestParams(request)
        if params['event'] == 'ONAPPINSTALL' and params['auth']:
            result['install'] = self.setAppSettings(params['auth'], True)
        elif params['PLACEMENT'] == 'DEFAULT':
            result['rest_only'] = False
            result['install'] = self.setAppSettings({
                'access_token': escape(params["AUTH_ID"]),
                'expires_in': escape(params["AUTH_EXPIRES"]),
                'application_token': escape(params["APP_SID"]),
                'refresh_token': escape(params["REFRESH_ID"]),
                'domain': escape(params["DOMAIN"]),
                'client_endpoint': f'https://{escape(params["DOMAIN"])}/rest/'
            }, True)

        self.setLog({
            'request': params,
            'result': result
        }, 'installApp')

        return result

    def setAppSettings(self, settings, is_install=False):
        result = False
        if isinstance(settings, (list, dict)):
            old_data = self.getAppSettings()
            if not is_install and old_data and isinstance(old_data, (list, dict)):
                settings = old_data + settings

            result = self.setSettingData(settings)

        return result

    def getAppSettings(self):
        data = self.getSettingData()

        if data['access_token'] and data['domain'] and data['refresh_token'] and data['application_token'] and data['client_endpoint']:
            return data

        return False

    def getSettingData(self):
        result={}
        if os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '/settings.json'):
            with open(os.path.dirname(os.path.realpath(__file__)) + '/settings.json', 'r') as file:
                result = json.loads(file.read())

        return result

    def setSettingData(self, settings):
        with open(os.path.dirname(os.path.realpath(__file__)) + '/settings.json', 'w') as file:
            file.write(json.dumps(settings))

        return True

    def GetNewAuth(self, params):
        result = {}
        settings = self.getAppSettings()
        if settings:
            params_auth = {
                'this_auth': 'Y',
                'params':{
                    'client_id': C_REST_CLIENT_ID,
                    'grant_type': 'refresh_token',
                    'client_secret': C_REST_CLIENT_SECRET,
                    'refresh_token': settings['refresh_token']
                }
            }

            new_data = self.DoResust(params_auth)

            if self.setAppSettings(new_data):
                params['this_auth'] = 'N'
                result = self.DoResust(params)

        return result




    def setLog(self, data, type=''):
        result = False
        if C_REST_BLOCK_LOG:
            if C_REST_LOGS_DIR:
                path = C_REST_LOGS_DIR
            else:
                path = os.path.dirname(os.path.realpath(__file__)) + '/logs/'

            if not os.path.exists(path):
                os.makedirs(path)

            path += datetime.now().strftime('d.m.Y H')+f'_{type}.txt'
            with open(path, 'a') as file:
                file.write(json.dumps(data))

            result = True

        return result
