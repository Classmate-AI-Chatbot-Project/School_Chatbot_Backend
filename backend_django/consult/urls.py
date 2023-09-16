# consult/urls.py

from django.urls import path
from . import views

app_name = 'consult'

urlpatterns = [
    # path("", views.index, name="index"),        # 상담 대화방 목록 (장고 테스트 페이지)
    path("list/", views.index, name="index"),    # 상담 대화방 목록 (프론트 연결)
    path('redirect_room/', views.consult_with_teacher, name='create_consult_with_teacher'),  # 사이드바 버튼
    path('request_consult/', views.student_request_consult, name='student_request_consult'),    # 챗봇 결과 페이지 버튼
    path('start_consult/<str:student_email>/', views.teacher_start_consult, name='teacher_start_consult'),  # 학생 프로필 페이지 버튼
    path('room/<int:room_name>/student/<int:student_id>/', views.room, name='room'),
]