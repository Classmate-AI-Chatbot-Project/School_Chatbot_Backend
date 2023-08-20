# consult/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("studentlist/<str:teacher_id>/", views.studentList, name="room"),
]