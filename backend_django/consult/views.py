# consult/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json
from django.http import JsonResponse
from .models import ConsultRoom

def index(request):
    return render(request, "consult/index.html")
'''
@login_required
def start_consult(request):
    consult_room = ConsultRoom.objects.create(
        student_id=None,        # 초기에는 학생 정보 없이 생성
        teacher_id=request.user   # 선생님이 먼저 상담 시작
    )
    return JsonResponse({'consult_id': consult_room.consult_id})
'''
@login_required
def room(request, room_name):
    # 생성된 ConsultRoom 객체 가져오기
    # consult_room = ConsultRoom.objects.get(consult_id=room_id)

    # consult_id와 username을 딕셔너리 형태로 room.html로 전달
    return render(request, "consult/room.html", {
        'room_name_json': mark_safe(json.dumps(room_name)),
        'username': mark_safe(json.dumps(request.user.username)),
    })
