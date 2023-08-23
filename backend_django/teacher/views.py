from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import User
from django.http import HttpResponse
from rest_framework import status
from account.serializers import StudentListSerializer

@login_required           
def studentList(request):  
    # 현재 로그인한 사용자
    user = request.user
    student_list = User.objects.filter(school=user.school, job=1)
    if request.method == 'GET':
        print(student_list)
        serializer = StudentListSerializer(student_list, many=True)
        return HttpResponse(serializer.data)