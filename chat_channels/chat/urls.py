from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat.send/', views.send_to_chat),
]