from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import User
from chat.models import ConsultResult
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from account.serializers import StudentListSerializer, UserSerializer
from teacher.serializers import ResultSerializer
import json

@login_required           
# 선생님의 학생 리스트
def studentList(request):  
    user = request.user
    student_list = User.objects.filter(school=user.school, job=1)
    if request.method == 'GET':
        print(student_list)
        serializer = StudentListSerializer(student_list, many=True)

        data = {
            'student_data':serializer.data
        }
        return JsonResponse(data)
    
@login_required
# student_id로 해당 학생의 세부 정보를 반환           
def studentDetail(request, student_id):  
    # 현재 로그인한 사용자
    user = request.user
    if request.method == 'GET':
        student = User.objects.get(email=student_id)
        student_chatResult = ConsultResult.objects.filter(member_id=student) 
        serializer = ResultSerializer(student_chatResult, many=True) #접근한 학생의 상담 결과를 직렬화
        

        # 유저 정보와 상담 결과를 Json으로 만들어 반환
        data = {
            'student_id':student.email,
            'nickname':student.username,
            'profile':student.profile_photo.url,
            'consult_result':serializer.data
        }

        return JsonResponse(data)
    
@login_required           
def resultDetail(request, chat_id):  
    user = request.user
    if request.method == 'GET': # 특정 chat_id로 접근시, 해당 채팅방의 결과 세부정보 반환
        student_chatResult = ConsultResult.objects.get(chat_id=chat_id)
        student_chatResult.is_read = True
        student_chatResult.save()
        Result_serializer = ResultSerializer(student_chatResult)
        User_serializer = UserSerializer(user)

        data = {
            'user_data' : User_serializer.data,
            'result_data' : Result_serializer.data
        }

        return JsonResponse(data)