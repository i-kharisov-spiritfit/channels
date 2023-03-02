from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from . import CRest

# Create your views here.


@csrf_exempt
def test(request):
    print(request.body.decode())
    CRest.getRequestParams(request)
