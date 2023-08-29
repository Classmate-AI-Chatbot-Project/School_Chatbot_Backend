from django.urls import path
from . import views

urlpatterns = [
    path("studentlist", views.studentList),
    path("detail/<str:student_id>", views.studentDetail),
    path("chat/result/<int:chat_id>", views.resultDetail), 
]