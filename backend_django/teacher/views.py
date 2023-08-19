from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import User
from django.http import HttpResponse
from rest_framework import status
from account.serializers import StudentListSerializer


# Create your views here.
@login_required           
def studentList(request, teacher_id):  # URL에 포함된 값을 전달받음 (ex: /chat/1/1/)
    # 현재 로그인한 사용자
    user = request.user
    student_list = User.objects.filter(school=user.school, job=1)
    if request.method == 'GET':
        print(student_list)
        serializer = StudentListSerializer(student_list, many=True)
        return HttpResponse(serializer.data)