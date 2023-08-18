# consult/admin.py

from django.contrib import admin
from .models import ConsultMessage, ConsultRoom

admin.site.register(ConsultRoom)
admin.site.register(ConsultMessage)
