# consult/urls.py

from django.urls import path, re_path
from . import views

app_name = 'consult'

urlpatterns = [
    path("", views.index, name="index"),
    # path('start/', views.start_consult, name='start_consult'), 
    re_path(r'^(?P<room_name>[^/]+)/$', views.room, name="room"),  # /consult/1 (1번째 상담방)
]