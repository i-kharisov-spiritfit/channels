from portal.crest import CRest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def install(request):
    result = CRest().installApp(request)
    if result.get('rest_only') and result.get('rest_only')==False:
        page = '<head><script src="//api.bitrix24.com/api/v1/"></script>'
        if result.get('install') == True:
            page+= '<script>BX24.init(function(){BX24.installFinish();});</script>'

        page+='</head>'

        if result.get('install') == True:
            str = 'installation has been finished'
        else:
            str = 'installation error'

        page+=f'<body>{str}<pre>{json.dumps(result, indent=4)}</pre></body>'
        return HttpResponse(content=page)

    return JsonResponse(result)