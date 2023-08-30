# consult/urls.py

from django.urls import path, re_path
from . import views

app_name = 'consult'

urlpatterns = [
    path("", views.index, name="index"), 
    # re_path(r'^(?P<room_name>[^/]+)/$', views.room, name="room"),  # /consult/1 (1번째 상담방)
    path('create/', views.create_or_redirect_room, name='create_or_redirect_room'),
    path('room/<int:room_name>/student/<int:student_id>/', views.room, name='room'),   
]