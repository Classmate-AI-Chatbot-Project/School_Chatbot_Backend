from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import User
from chat.models import ConsultResult
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from account.serializers import StudentListSerializer, UserSerializer
from teacher.serializers import ResultSerializer, ResultListSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import json
from django.db.models import Count

from .drawingtest import visualize_detection_results, get_prediction

from django.http import JsonResponse
from PIL import Image
from io import BytesIO
import base64

@login_required           
# 선생님의 학생 리스트
def studentList(request):  
    user = request.user
    from django.db.models import F, Max

    from django.db.models import Max

    student_list = User.objects.filter(
        school=user.school, job=1, consultresult__isnull=False
    ).annotate(
        latest_consult_date=Max('consultresult__result_time')
    ).order_by('-latest_consult_date')


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
        student_id = student_chatResult.member_id
        User_serializer = UserSerializer(student_id)

        data = {
            'user_data' : User_serializer.data,
            'result_data' : Result_serializer.data
        }

        return JsonResponse(data)

@csrf_exempt
def test(request):  
    if request.method == 'POST': # 특정 chat_id로 접근시, 해당 채팅방의 결과 세부정보 반환
        data = json.loads(request.body.decode('utf-8'))
        image_data_url = data.get("image_data")
        print(image_data_url)

        _, data = image_data_url.split(',', 1)
        image_data = base64.b64decode(data)

        # 이미지를 Pillow Image 객체로 변환
        image = Image.open(BytesIO(image_data))

        # 이미지 처리 및 저장 (예: 미디어 디렉토리에 저장)
        image.save('media/drawings/drawing.png', 'PNG')

        return HttpResponse(status=status.HTTP_200_OK)

@csrf_exempt
def test_result(request):  
    if request.method == 'GET': # 특정 chat_id로 접근시, 해당 채팅방의 결과 세부정보 반환
        # 이미지 파일 경로
        image_path = 'media/drawings/drawing.png'

        # 이미지 읽기
        with open(image_path, 'rb') as ff:
            content = ff.read()


        # 객체 탐지 결과 얻기
        project_id = 'tree-392720'
        model_id = 'IOD139546717262446592'
        prediction = get_prediction(content, project_id, model_id)
        
        # 결과 시각화 및 문구 출력
        result_text = visualize_detection_results(prediction, image_path)

        data = {
            'img':'/media/drawings/drawing.png',
            'result':result_text
        }

        return JsonResponse(data)
    
def resultList(request):  
    user = request.user
    student_list = User.objects.filter(school=user.school, job=1)
    result_list = ConsultResult.objects.filter(member_id__in=student_list)
    if request.method == 'GET':
        print(result_list)

        serializer = ResultListSerializer(result_list, many=True) #접근한 학생의 상담 결과를 직렬화

        print(serializer.data)

        data = {
            'consult_result':serializer.data
        }

        return JsonResponse(data)
