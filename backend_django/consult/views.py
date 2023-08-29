# consult/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
import json
from django.http import Http404
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ConsultRoom, ConsultMessage, Notification
from account.models import User
from chat.models import ConsultResult

# /consult : [상담 신청하기/상담하기] 버튼 + 상담 채팅방 목록 페이지
# 상담 목록 페이지 : 학생은 선생님과의 채팅방 1개, 선생님은 여러 학생들과의 채팅방 n개 표시하기 위해 json 데이터 전달
def index(request):
    user = request.user
    consult_room_items = []     # 채팅방 list items
    is_student = user.job == 1
    
    if is_student:  # 학생인 경우
        consult_rooms = ConsultRoom.objects.filter(student=user)
    else:  # 선생님인 경우
        consult_rooms = ConsultRoom.objects.filter(teacher=user)

    for consult_room in consult_rooms:
        # 학생이면 상담 선생님, 선생님이면 상담 학생들 정보 가져오기
        other_user = consult_room.teacher if is_student else consult_room.student
        
        # 학생(들)의 최신 ConsultResult 가져오기
        if is_student:
            consult_results = ConsultResult.objects.filter(member_id=user).order_by('-result_time')[:1]
        else:
            consult_results = ConsultResult.objects.filter(member_id=other_user).order_by('-result_time')[:1]
        
        # 학생의 챗봇 상담 결과가 존재하면 
        if consult_results.exists():
            recent_consult_result = consult_results[0]

            # Check if there are unread notifications for this user in the room
            if consult_room.has_unread_notification(user):
                is_unread = True
            else:
                is_unread = False 
            
            # 상담 채팅방 목록 item에 표시할 json 데이터 전달
            consult_room_items.append({
                'user_profile': other_user.profile_photo.url,
                'username': other_user.username,
                'emotion_temp': recent_consult_result.emotion_temp,
                'category': recent_consult_result.category,
                'result_time': recent_consult_result.result_time.strftime('%Y년 %m월 %d일'),
                'room_id': consult_room.room_id,
                'student_id': user.id if is_student else other_user.id,
                'is_unread': is_unread,  # 알림 확인 상태 전달
            })

    context = {'consult_room_items': consult_room_items}
    return render(request, 'consult/index.html', context)
        # 테스트: index.html로 이동 ([상담 신청하기/상담하기] 버튼 + 상담 채팅방 리스트 페이지)
        # Frontend에 적용할 때는 상담 채팅방 목록 페이지 url로 이동하도록 수정하기


@login_required     
def create_or_redirect_room(request):   # [상담 신청하기] 버튼을 누르면 새 채팅방 생성/기존 채팅방 이동
    user = request.user
    is_student = user.job == 1      # Check if the user is a student or a teacher

    if is_student:  # 학생이면
        # find a teacher with the same school
        teacher = User.objects.filter(job=0, school=user.school).first()
        if not teacher:
            raise Http404("No teacher available for this student's school.")
        
        # 최근 ConsultResult 데이터 가져와 상담 신청 메시지 구성: string 데이터
        consult_result = ConsultResult.objects.filter(member_id=user).latest('result_time')
        message_content = "상담을 신청해요.\n"
        message_content += f"키워드: {consult_result.category}\n"
        message_content += f"감정 온도: {consult_result.emotion_temp}도\n"
        message_content += f"챗봇 상담 시간: {consult_result.result_time.strftime('%Y년 %m월 %d일')}\n"
        
        # Frontend에 보낼 상담 신청 메시지 json 데이터
        # message_content = {
        #     'consult_request': '상담을 신청해요.',
        #     'category': consult_result.category,
        #     'emotion_temp': consult_result.emotion_temp,
        #     'result_time': consult_result.result_time.strftime('%Y년 %m월 %d일'),
        # }
        # message_content_json = json.dumps(message_content)
        
        # Check if a ConsultRoom already exists between this student and teacher
        existing_room = ConsultRoom.objects.filter(
            Q(student = user, teacher = teacher) | Q(student = teacher, teacher = user)
        ).first()
        
        if existing_room:   # 기존 채팅방에 상담 신청 메시지 생성, 전송
            create_or_update_consult_request_message(existing_room, user, message_content)  # or message_content_json
            return redirect('consult:room', room_name = existing_room.room_id, student_id = user.id)
        
        # If room not exists, 새 채팅방 생성 & 상담 신청 메시지 생성, 전송
        new_room = ConsultRoom.objects.create(student = user, teacher = teacher)
        create_or_update_consult_request_message(new_room, user, message_content)   # or message_content_json
        return redirect('consult:room', room_name = new_room.room_id, student_id=user.id) 
            # room/<int:room_name>/student/<int:student_id> 이동 => room 뷰 함수 실행   
    
    else:   # 선생님이면
        # 학생 프로필 페이지(/teacher/detail/<str:student_id>)의 [상담하기] 버튼을 누르면 해당 학생과의 기존 채팅방으로 이동
        # student = User.objects.get(email=student_id)
        student = User.objects.filter(job=1, school=user.school).first()    # 임시 학생
        if not student:
            raise Http404("Invalid student id or student not found.")
        
        # Check if a ConsultRoom already exists between this teacher and student
        existing_room = ConsultRoom.objects.filter(
            Q(student = student, teacher = user) | Q(student = user, teacher = student)
        ).first()

        if existing_room:
            return redirect('consult:room', room_name = existing_room.room_id, student_id = student.id)


def create_or_update_consult_request_message(room, author, content):
    is_student = author.job == 1
    # 지난 같은 내용의 상담 신청 메시지 존재 체크
    existing_message = ConsultMessage.objects.filter(
        room_id=room,
        is_consult_request=True,
        content=content
    ).first()

    # 같은 내용이 없으면 새로운 상담 신청 메시지 생성
    if not existing_message:
        new_message = ConsultMessage.objects.create(
            author=author,
            room_id=room,
            is_consult_request=True,
            content=content             
        )
        # Create and send a new notification for the new consult request message
        receiver = room.teacher if is_student else room.student
        notification = Notification.create_notification(
            sender=author,
            receiver=receiver,
            consult_room=room
        )
        # Use channel layer to send a new message to the WebSocket consumer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room.room_id}',
            {
                'type': 'new_message',
                'message': {
                    'command': 'new_message',
                    'message': {
                        'author': author.username,
                        'content': new_message.content,
                        'timestamp': str(new_message.timestamp),
                    },
                    'notification_id': notification.id
                }
            }
        )


@login_required 
def room(request, room_name, student_id):
    room_id = int(room_name)
    consult_room = ConsultRoom.objects.get(room_id=room_id, student=student_id)
    user = request.user
    is_student = user.job == 1 
    consult_room.mark_notifications_as_read(user)
        # When the user enters the room, Mark the notifications as read
    consult_result = ConsultResult.objects.filter(member_id = student_id).latest('result_time')
        # 상담 신청 메시지에 표시할 학생의 최근 ConsultResult 가져오기
    has_consult_result = ConsultResult.objects.filter(member_id=student_id).exists()
        # If the student does not have consult result, chat with chatbot first
    consult_request_messages = ConsultMessage.objects.filter(room_id=consult_room, is_consult_request=True)
        # 해당 채팅방의 상담 신청 메시지들
    
    # 상대방의 프로필 사진 가져오기 Retrieve other user's profile photo
    if is_student:
        teacher_id = consult_room.teacher.id
        other_user = User.objects.get(id=teacher_id, job=0)
    else:
        student_id = consult_room.student.id
        other_user = User.objects.get(id=student_id, job=1) 
    user_profile = user.profile_photo.url
    other_user_profile = other_user.profile_photo.url

    # 상담 채팅방에 표시할 데이터를 json 형태로 consult/room.html에 전달
    return render(request, "consult/room.html", {
        'room_id_json': mark_safe(json.dumps(room_id)),
        'username': user.username,              # 현재 로그인한 사용자
        'other_username': other_user.username,  # 대화 상대방
        'user_profile': user_profile,
        'other_user_profile': other_user_profile,
        # 상담 신청 메시지 데이터
        'consult_request_messages': consult_request_messages,  # 상담 신청 메시지 목록
        'category': consult_result.category,    # 키워드
        'emotion_temp': consult_result.emotion_temp,
        'result_time': consult_result.result_time.strftime('%Y년 %m월 %d일'),
            # 1. 우선 DB에 저장된 상담 신청 메시지 내용(string)을 가져와서 Frontend의 상담 신청 메시지 양식에 표시하기 (is_consult_request=True인 consult_request_messages)
            # 2. 만약 string으로 가져오는 게 어려우면 메시지 내용을 주석 처리한 message_content_json 로 변경하고, content = message_content 주석처리하기
            # 3. 만약 2번도 어렵다면 해당 render 안의 json 데이터 이용하기
            # 새로운 상담 신청 메시지가 왔을 때 전 상담 신청 메시지도 감정 이모티콘이 표시되도록 하기.
            # 전 신청 매시지의 이모티콘이 표시되지 않으면, 시도해보다가 안 되면, 그냥 감정 온도 숫자 그대로 가져와서 표시하기 (ex: 70°C)
        'has_consult_result': has_consult_result,   # Boolean
            # Frontend 적용: 학생에게 ConsultResult가 아무것도 없으면, 
            # “챗봇과 먼저 이야기를 나눠보세요!” 문구 & [챗봇과 상담하기] 버튼 표시 & 메시지 input 창 비활성화
    })
