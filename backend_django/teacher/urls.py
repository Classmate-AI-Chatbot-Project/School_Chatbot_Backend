from django.urls import path
from . import views

urlpatterns = [
    path("studentlist", views.studentList),
    path("detail/<str:student_id>", views.studentDetail),
    path("chat/result/<int:chat_id>", views.resultDetail), 
    path("chatresult_list", views.resultList), 
    path("test", views.test), 
    path("test/result", views.test_result),
]