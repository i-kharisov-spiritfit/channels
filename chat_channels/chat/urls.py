from django.urls import path

from . import views

urlpatterns = [
    path('install', views.install),
    path('handler', views.handler),
    path('install_connector', views.install_connector),
    path('check/', views.check_user)
    # path('', views.index, name='index'),
    # path('chat.send/', views.send_to_chat),
]