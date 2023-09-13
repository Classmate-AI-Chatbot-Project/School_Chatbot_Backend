# consult/urls.py

from django.urls import path
from . import views

app_name = 'consult'

urlpatterns = [
    # path("", views.index, name="index"),        # 상담 대화방 목록 (장고 테스트 페이지)
    path("list", views.index, name="index"),    # 상담 대화방 목록 (프론트 연결)
    path('create/', views.student_create_or_redirect_room, name='student_create_or_redirect_room'),
    path('start_consult/<str:student_email>/', views.teacher_start_consult, name='teacher_start_consult'),
    path('room/<int:room_name>/student/<int:student_id>/', views.room, name='room'),
]