# chat/admin.py

from django.contrib import admin
from .models import ChatRoom, ChatMessage, AllDialogue

admin.site.register(ChatRoom)
admin.site.register(ChatMessage)
admin.site.register(AllDialogue)
