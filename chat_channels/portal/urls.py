from django.urls import path, re_path
from .views import install, handler

urlpatterns = [
    path('install/', install.install),
    path('<str:line_id>/handler/', handler.handler),
    path('<str:line_id>/message/', handler.message),
    re_path(r'^access/?(?P<line_id>.*)?$', handler.get_access)
]