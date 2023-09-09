# chat/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    path('create/', views.create_chatroom_and_redirect, name='chat'),
    path('<str:user_id>/<int:chatroom_id>/', views.chat_service, name='chatbot'),
    path('result/<str:user_id>/<int:chatroom_id>/', views.chat_result, name='chatResult'),
    path('history/<str:user_id>/<int:chatroom_id>/', views.chat_history, name='chatHistory'),
    path('end/<str:user_id>/<int:chatroom_id>/', views.chat_end, name='chatEnd'),
]
