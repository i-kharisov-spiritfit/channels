import json
import requests
from django.utils.html import escape
import os
from datetime import datetime
import random
from django.core.handlers.wsgi import WSGIRequest
import re

C_REST_CLIENT_ID = 'local.642f0986c35e94.01569628'                              #Application ID
C_REST_CLIENT_SECRET = 'QRr5yDqMuMDaTkfJVUMad3FH6R9HuzEqM93tTiajfIsAA6IIdv'     #Application key

C_REST_BLOCK_LOG = False
C_REST_LOGS_DIR = os.path.dirname(os.path.realpath(__file__)) + '/logs/'

class Utils:
    @staticmethod
    def empty(value):
        if isinstance(value, (list, dict, str)) and len(value)==0:
            return True

        if not bool(value):
            return True

        return False

class CRest:
    VERSION = 1.36
    BATCH_COUNT = 50
    TYPE_TRANSPORT = 'json'

    def setLog(self, data, type = ''):
        result = False
        if C_REST_BLOCK_LOG != True:
            if C_REST_LOGS_DIR!=None:
                path = C_REST_LOGS_DIR
            else:
                path = os.path.dirname(os.path.realpath(__file__)) + '/logs/'

            path+=datetime.now().strftime('%Y-%m-%d/%H')+'/'

            if not os.path.exists(path):
                os.makedirs(path, mode=0o775)

            path += datetime.now().strftime('%H:%M') + '_' + type + str(random.randint(1, 999)) + '.log'

            with open(path, 'a', encoding='utf-8') as file:
                file.write(json.dumps(data))

        return result

    def getRequestParams(self, request: WSGIRequest):
        def _request_dict_val(result, keys, val):
            current_key = keys[0]
            if len(keys) < 2:
                result[current_key] = val
            else:
                if current_key not in result:
                    result[current_key] = dict()
                _request_dict_val(result[current_key], keys[1:], val)

        def get_request_dict(query_dict):
            result = dict()
            all_params = query_dict.dict()
            for str_name in all_params.keys():
                if str_name.find('[')!=-1 and str_name.endswith(']'):
                    param = str_name.split('[')[0]
                    if param not in result:
                        result[param] = dict()

                    _request_dict_val(result[param], re.findall(r'\[(\w+)\]', str_name), all_params.get(str_name))
                else:
                    result[str_name] = all_params.get(str_name)
            return result

        params = request.GET.dict()
        if request.method == "POST":
            post_params = get_request_dict(request.POST)
            params.update(post_params)


        return params

    def installApp(self, request: WSGIRequest):
        result = {
            'rest_only': True,
            'install': False
        }
        params = self.getRequestParams(request)
        if params['event'] == 'ONAPPINSTALL' and not Utils.empty(params['auth']):
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
            'result':result
        }, 'installApp')

        return result

    def setAppSettings(self, settings, isInstall = False):
        _return = False
        if isinstance(settings, (list, dict)):
            oldData = self.getAppSettings()
            if isInstall != True and not Utils.empty(oldData) and isinstance(oldData, (list, dict)):
                oldData.update(settings)
                settings=oldData

            _return = self.setSettingData(settings)

        return _return

    def getAppSettings(self):
        data = self.getSettingData()
        isCurrData = False

        if not Utils.empty(data.get('access_token')) and \
                not Utils.empty(data['domain']) and \
                not Utils.empty(data['refresh_token']) and \
                not Utils.empty(data['application_token']) and \
                not Utils.empty(data['client_endpoint']):
            isCurrData = True

        if isCurrData:
            return data
        else:
            return False

    def getSettingData(self):
        _return = {}
        file_path = os.path.dirname(os.path.realpath(__file__)) + '/settings.json'

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                _return = json.loads(file.read())

            if not Utils.empty(C_REST_CLIENT_ID):
                _return['C_REST_CLIENT_ID'] = C_REST_CLIENT_ID

            if not Utils.empty(C_REST_CLIENT_SECRET):
                _return['C_REST_CLIENT_SECRET'] = C_REST_CLIENT_SECRET

        return _return

    def setSettingData(self, settings):
        try:
            os.umask(0)
            descriptor = os.open(
                path=os.path.dirname(os.path.realpath(__file__)) + '/settings.json',
                flags=(
                        os.O_WRONLY  # access mode: write only
                        | os.O_CREAT  # create if not exists
                        | os.O_TRUNC  # truncate the file to zero
                ),
                mode=0o774
            )



            with open(descriptor, 'w', encoding='utf-8') as file:
                file.write(json.dumps(settings))

            return True

        except:
            return False

    def call(self, method, params = {}):
        arPost = {
            'method':method,
            'params':params
        }

        result  = self.callRequest(arPost)
        return result

    def callRequest(self, params):
        settings = self.getAppSettings()
        if settings != False:
            if params.get('this_auth') and params.get('this_auth') == 'Y':
                url = 'https://oauth.bitrix.info/oauth/token/'
                transport_type = "data"
            else:
                transport_type = "json"
                url = settings['client_endpoint'] + params['method'] + '.' + self.TYPE_TRANSPORT
                if not settings.get('is_web_hook') or settings.get('is_web_hook') != 'Y':
                    params['params']['auth'] = settings['access_token']

            try:
                if not Utils.empty(params.get('params')):
                    method = "POST"
                else:
                    method = "GET"

                headers = {
                    'User-Agent': 'Bitrix24 CRest Utils ' + str(self.VERSION),
                }

                if transport_type == "data":
                    r = requests.request(method, url=url, headers=headers, data=params.get('params'), allow_redirects=params.get('followlocation') if params.get('followlocation') else True)
                else:
                    r = requests.request(method, url=url, headers=headers, json=params.get('params'),
                                         allow_redirects=params.get('followlocation') if params.get(
                                             'followlocation') else True)
                result = r.json()


                if not Utils.empty(result.get('error')):
                    if result.get('error') == 'expired_token' and Utils.empty(params.get('this_auth')):
                        result = self.GetNewAuth(params)
                    else:
                        arErrorInform={
                            'expired_token' : 'expired token, cant get new auth? Check access oauth server.',
                            'invalid_token' : 'invalid token, need reinstall application',
                            'invalid_grant' : 'invalid grant, check out define C_REST_CLIENT_SECRET or C_REST_CLIENT_ID',
                            'invalid_client' : 'invalid client, check out define C_REST_CLIENT_SECRET or C_REST_CLIENT_ID',
                            'QUERY_LIMIT_EXCEEDED' : 'Too many requests, maximum 2 query by second',
                            'ERROR_METHOD_NOT_FOUND' : 'Method not found! You can see the permissions of the application: CRest::call(\'scope\')',
                            'NO_AUTH_FOUND' : 'Some setup error b24, check in table "b_module_to_module" event "OnRestCheckAuth"',
                            'INTERNAL_SERVER_ERROR' : 'Server down, try later'
                        }

                        if not Utils.empty(arErrorInform.get(result['error'])):
                            result['error_information'] = arErrorInform[result['error']]

                self.setLog({
                    'url': url,
                    'params':params,
                    'result':result
                }, 'callCurl')

                return result


            except Exception as err:
                self.setLog({
                    'message': str(err)
                }, 'exceptRequest')

                return {
                    'error':'exception',
                    'message': str(err)
                }
        else:
            self.setLog({
                'params':params
            }, 'emptySettings')

        return {
            'error':'emptySettings'
        }

    def GetNewAuth(self, params):
        result = {}
        settings = self.getAppSettings()

        if settings:
            params_auth = {
                'this_auth': 'Y',
                'params':{
                    'client_id': settings["C_REST_CLIENT_ID"],
                    'grant_type': 'refresh_token',
                    'client_secret': settings['C_REST_CLIENT_SECRET'],
                    'refresh_token': settings['refresh_token']
                }
            }

            new_data = self.callRequest(params_auth)

            if new_data.get('C_REST_CLIENT_ID'):
                new_data.pop('C_REST_CLIENT_ID')

            if new_data.get('C_REST_CLIENT_SECRET'):
                new_data.pop('C_REST_CLIENT_SECRET')

            if self.setAppSettings(new_data):
                params['this_auth'] = 'N'
                result = self.callRequest(params)



        return result