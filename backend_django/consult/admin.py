# consult/admin.py

from django.contrib import admin
from .models import ConsultMessage, ConsultRoom, Notification

admin.site.register(ConsultRoom)
admin.site.register(ConsultMessage)
admin.site.register(Notification)
