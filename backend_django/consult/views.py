# consult/views.py

from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
import json
from django.http import Http404, HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from .models import ConsultRoom, ConsultMessage, Notification
from account.models import User
from chat.models import ConsultResult

# topbar, sidebar에 새 메시지 알림 전달
@login_required
def check_unread_messages(request):
    # 현재 로그인한 사용자(수신자)의 미확인 메시지 있는지 확인
    user = request.user
    is_student = user.job == 1

    if request.method == 'GET':
        is_unread = False  # 초기값 설정
        has_new_consult_result = False

        if is_student:  # 학생인 경우
            consult_rooms = ConsultRoom.objects.filter(student=user)
        else:  # 선생님인 경우
            consult_rooms = ConsultRoom.objects.filter(teacher=user)

        for consult_room in consult_rooms:
            # 하나 이상의 consult_room에 새 상담 메시지가 있으면 True
            if consult_room.has_unread_notification(user):
                is_unread = True

            # 상담방에 참가한 학생의 최신 ConsultResult가 안 읽은 상태면 True (새 상담 결과 있음)
            student_id = consult_room.student
            try:
                consult_result = ConsultResult.objects.filter(member_id=student_id).latest('result_time') 
                if consult_result and not consult_result.is_read:
                    has_new_consult_result = True
            except ConsultResult.DoesNotExist:
                has_new_consult_result = False
            
        return JsonResponse({'is_unread': is_unread, 'has_new_result': has_new_consult_result})   # is_unread=True 면 안 읽은 메시지 있음
        
# 상담 대화방 목록 페이지 : 학생은 선생님과의 채팅방 1개, 선생님은 여러 학생들과의 채팅방 n개 표시
def index(request):         # /consult/list (장고 테스트 페이지: /consult)
    user = request.user
    consult_room_items = []     # 채팅방 list items
    is_student = user.job == 1
    
    if request.method == 'GET':
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
                    is_read = False
                else:
                    is_read = True 

                # 각 채팅방의 최신 메시지 내용 가져오기
                latest_message = ConsultMessage.objects.filter(room_id=consult_room).latest('timestamp')
                latest_message_content = latest_message.content
                latest_message_time = latest_message.timestamp
            
                # 상담 채팅방 목록 item에 표시할 json 데이터 전달
                consult_room_items.append({
                    'username': other_user.username,
                    'user_profile': other_user.profile_photo.url,
                    'emotion_temp': recent_consult_result.emotion_temp,
                    'latest_message_content': latest_message_content,
                    'latest_message_time': latest_message_time,
                    'room_id': consult_room.room_id,
                    'student_id': user.id if is_student else other_user.id,
                    'is_read': is_read,  # 알림 확인 상태 전달
                })
        return JsonResponse({'consult_rooms': consult_room_items})
    
        # 장고 테스트 페이지(/consult)로 이동하려면 위 문장 주석처리 & 아래 주석 풀기 & consult/urls.py 1번째 주석 풀고 2번째 주석 추가하기
        # context = {'consult_room_items': consult_room_items}
        # return render(request, 'consult/index.html', context)

# 학생이 [상담 신청하기] 버튼을 누르면 새 채팅방 생성/기존 채팅방 이동 => 상담 신청 메시지 전송
@login_required     
def student_request_consult(request):   # /consult/request_consult
    user = request.user
    is_student = user.job == 1      # Check if the user is a student or a teacher
    if is_student:
        if request.method == 'POST':    # 상담 신청 메시지 전송하기
            # find a teacher with the same school
            teacher = User.objects.filter(job=0, school_code=user.school_code).first()
            if not teacher:
                raise Http404("No teacher available for this student's school.")

            # 가장 최근 ConsultResult 데이터 가져와 상담 신청 메시지 구성
            consult_result = ConsultResult.objects.filter(member_id=user).latest('result_time')
            # message_content = {
            #     'category': consult_result.category,
            #     'emotion_temp': consult_result.emotion_temp,
            #     'result_time': consult_result.result_time.strftime('%Y년 %m월 %d일'),
            # }
            message_content = ""
            message_content += f"{consult_result.emotion_temp}/n"
            message_content += f"{consult_result.category}/n"
            message_content += f"{consult_result.result_time.strftime('%Y년 %m월 %d일')}/n"
            message_content += f"{consult_result.chat_id}/n"
        
            # 기존 상담방/새 상담방으로 이동 => 상담 신청 메시지 전송
            existing_room = ConsultRoom.objects.filter(
                Q(student=user, teacher=teacher) | Q(student=teacher, teacher=user)
            ).first()

            # room/<int:room_name>/student/<int:student_id> 이동 => room 뷰 함수 실행
            if existing_room:
                create_consult_request_message(existing_room, user, message_content)
                return HttpResponseRedirect(reverse('consult:room', args=[existing_room.room_id, user.id]))
            else:
                new_room = ConsultRoom.objects.create(student=user, teacher=teacher)
                create_consult_request_message(new_room, user, message_content)
                return HttpResponseRedirect(reverse('consult:room', args=[new_room.room_id, user.id]))

        # Return an HTTP response in case of GET request
        return HttpResponse(status=200)

def create_consult_request_message(room, author, content):
    # JSON 데이터를 문자열로 변환하여 content 필드에 저장
    message_content_str = json.dumps(content, ensure_ascii=False)

    # 새로운 상담 신청 메시지 생성
    ConsultMessage.objects.create(
        author=author,
        room_id=room,
        is_consult_request=True,
        content=message_content_str      # Frontend: JSON.parse해서 데이터 추출하기       
    )

    ConsultMessage.objects.create(
        author=author,
        room_id=room,
        is_consult_request=True,
        content="상담을 신청해요."    # Frontend: JSON.parse해서 데이터 추출하기       
    )
    # 알림 생성
    is_student = author.job == 1
    receiver = room.teacher if is_student else room.student
    Notification.create_notification(
        sender=author,
        receiver=receiver,
        consult_room=room
    )

# 학생이 사이드바에서 [선생님과 상담하기] 누르면 기존 채팅방으로 이동    
@login_required
def consult_with_teacher(request):  # /consult/redirect_room  
    user = request.user
    is_student = user.job == 1  # Check if the user is a student

    if is_student:
        if request.method == 'GET':
            # Find a teacher with the same school
            teacher = User.objects.filter(job=0, school_code=user.school_code).first()
            if not teacher:
                raise Http404("No teacher available for this student's school.")

            # Check if there is an existing consultation room between the student and teacher
            existing_room = ConsultRoom.objects.filter(
                Q(student=user, teacher=teacher) | Q(student=teacher, teacher=user)
            ).first()

            if existing_room:
                # If an existing room exists, redirect to the room
                consult_room_url =f'/consult/room/{existing_room.room_id}/student/{user.id}/'
                return JsonResponse({'consult_room_url': consult_room_url})
            else:
                # If no room exists, create a new consultation room and redirect to it
                new_room = ConsultRoom.objects.create(student=user, teacher=teacher)
                consult_room_url =f'/consult/room/{new_room.room_id}/student/{user.id}/'
                return JsonResponse({'consult_room_url': consult_room_url})

# 선생님이 학생 프로필 페이지(/teacher/detail/<str:student_email>)에서 [상담하기] 버튼을 누르면 기존 상담방으로 이동
@login_required
def teacher_start_consult(request, student_email):
    user = request.user
    is_teacher = user.job == 0

    if request.method == 'GET':
        if is_teacher:
            # 프로필 url에서 학생 정보 가져오기
            student = User.objects.get(email=student_email, job=1)

            # 상담 채팅방 찾기: 학생과 선생님이 이미 채팅한 방이 있는지 확인
            existing_room = ConsultRoom.objects.filter(
                Q(student=student, teacher=user) | Q(student=user, teacher=student)
            ).first()

            if existing_room:
                # 이미 채팅한 방이 있으면 해당 방으로 이동
                consult_room_url =f'/consult/room/{existing_room.room_id}/student/{student.id}/'
                return JsonResponse({'consult_room_url': consult_room_url})
            else:
                # 없으면 새로운 채팅방 생성 후 이동
                new_room = ConsultRoom.objects.create(student=student, teacher=user)
                consult_room_url =f'/consult/room/{new_room.room_id}/student/{student.id}/'
                return JsonResponse({'consult_room_url': consult_room_url})
        

@login_required 
def room(request, room_name, student_id):   # room/<int:room_name>/student/<int:student_id>
    room_id = int(room_name)
    consult_room = ConsultRoom.objects.get(room_id=room_id, student=student_id)
    user = request.user
    is_student = user.job == 1

    if request.method == 'GET':
        # 상담방 입장하면 모든 알림을 읽음 표시하기
        consult_room.mark_notifications_as_read(user)

        # 상담 신청 메시지에 표시할 학생의 최근 ConsultResult 가져오기
        consult_result = ConsultResult.objects.filter(member_id=student_id).latest('result_time') 

        # 최신 ConsultResult가 안 읽은 상태인가? (새 상담 신청 메시지 전송 조건)
        if consult_result and not consult_result.is_read:
            has_new_consult_result = True
        else:
            has_new_consult_result = False
            
        # 상대방의 프로필 사진 & 선생님 학교 / 학생 이메일 가져오기
        if is_student:
            teacher_id = consult_room.teacher.id
            other_user = User.objects.get(id=teacher_id, job=0)
            student_profile_id = user.email
        else:
            student_id = consult_room.student.id
            other_user = User.objects.get(id=student_id, job=1) 
            student_profile_id = other_user.email
            
        user_profile = user.profile_photo.url
        other_user_profile = other_user.profile_photo.url
        teacher_school = other_user.school_code          # 학생, 선생님 모두 같은 학교임

        # 새로 받은 새 메시지 + 지난 모든 메시지들 가져오기
        messages = ConsultMessage.objects.filter(room_id=consult_room).order_by('timestamp').all()
        #last_messages = serializers.serialize("json", messages)  # QuerySet을 JSON으로 직렬화
        messages_data = []
        for message in messages:
            messages_data.append({
                'author': message.author.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'date': message.timestamp.strftime('%Y년 %m월 %d일'),
                'request': message.is_consult_request,
            })

        consultRoomData = {
            'room_id_json': mark_safe(json.dumps(room_id)),
            # Frontend: 프로필 사진 클릭 => 모달창 팝업
            'username': user.username,                  # 현재 로그인한 사용자
            'other_username': other_user.username,      # 대화 상대방
            'user_profile': user_profile,               # 사용자 프로필 사진
            'other_user_profile': other_user_profile,   # 상대방 프로필 사진
            'teacher_school': teacher_school,           # 선생님 학교
            'student_profile_id': student_profile_id,   # 학생 프로필 페이지 url 속 student_id(email)
            'last_messages': messages_data,               # 지난 모든 메시지들
            'has_new_consult_result': has_new_consult_result,   # 새 상담 신청 메시지가 있으면...
            # 최근 상담 신청 메시지 데이터
            'category': consult_result.category,                   # 키워드
            'emotion_temp': consult_result.emotion_temp,           # 우울도(depression_count)
            'result_time': consult_result.result_time.strftime('%Y년 %m월 %d일'),
        }
        return JsonResponse({'consult_room_data': consultRoomData})

    # 상담 대화방에서 메시지 전송
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message', '')    # 'message' 키로 데이터 가져옴

        # 현재 시간 가져오기
        current_time = timezone.now()
        # 사용자 메시지 저장
        message = ConsultMessage.objects.create(     
            room_id=consult_room, 
            author=user,  
            content=user_input,
            timestamp=current_time
        )
        # 알림 생성 & 저장 (발신자가 학생이면 수신자는 선생님)
        receiver = consult_room.teacher if user == consult_room.student else consult_room.student
        Notification.create_notification(
            sender=user,
            receiver=receiver,
            consult_room=consult_room
        )

        # 새 메시지 데이터를 Frontend 화면에 추가하기
        new_message_data = {
            'author': message.author.username,
            'content': message.content,
            'timestamp': message.timestamp,
        }
        return JsonResponse({'new_message': new_message_data}, status=200)
