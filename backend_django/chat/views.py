# chat/views.py

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .kogpt2_chatbot import kogpt2_answer
from django.contrib.auth.decorators import login_required   # 함수형 뷰에만 적용 가능
from .models import User, ChatRoom, ChatMessage, AllDialogue   # 모델 임포트

'''
# 메인 페이지 [상담하러 가기] 버튼, 그림 심리 테스트 [챗봇과 상담하기] 버튼, 
# 선생님 상담 페이지 [챗봇과 상담하기] 버튼, 메뉴바 [챗봇과 상담하기] 버튼
# 위의 버튼을 누르면 아래 링크 연결
<a href="{% url 'chat_service' user.id chat_room.chat_id %}">채팅 서비스 입장</a>

# 로그인 안 한 상태 => '로그인이 필요합니다' 모달창 띄우기
# 로그인 한 상태 => 새로운 채팅방 생성하기 & 로그인한 user.id와 생성한 채팅방 id를 url에 전달하기
'''

@login_required           
def chat_service(request, user_id, chatroom_id):  # URL에 포함된 값을 전달받음 (ex: /chat/1/1/)
    # 현재 로그인한 사용자
    user = request.user                     # user = User.objects.get(user_id=1)
    # 가장 최근에 생성한 대화방 가져오기
    chat_room = ChatRoom.objects.filter(student_id=request.user.id).latest('chat_id')
    # chat_room = ChatRoom.objects.filter(student_id=request.user.id).order_by('-chat_date').first()

    context = { 'user': user.id, 'chat_room': chat_room.chat_id }

    if request.method == 'POST':
        user_input = request.POST['input1']     # 사용자 채팅

        # 사용자가 '종료하기'를 입력하지 않았을 때만 메시지 저장
        if user_input != '종료하기':
            # 사용자 메시지 저장
            ChatMessage.objects.create(     
                chat_id=chat_room,  
                sender='student',
                message_text=user_input,
                sender_user=user
            )
            # 챗봇 응답 생성 및 저장
            response = kogpt2_answer(user_input, user)    # 사용자 정보 & 발화 입력

            ChatMessage.objects.create(      
                chat_id=chat_room,  
                sender='chatbot',
                message_text=response
            )
            # POST 요청 => response에 output 챗봇 응답 메시지를 담아서 json 형태로 리턴
            output = dict()
            output['response'] = response
            return HttpResponse(json.dumps(output), status=200)
        
        else:   # '종료하기' 입력하면
            # 챗봇과 사용자의 저장된 발화들을 하나의 문자열로 연결하여 저장하기
            all_messages = ChatMessage.objects.filter(chat_id=chat_room).order_by('message_time')
            combined_text = ' '.join([message.message_text for message in all_messages])

            AllDialogue.objects.create(     
                chat_id=chat_room,  
                sender_user=user,
                dialogue_text=combined_text
            )
            # DB에 저장한 모든 대화 텍스트를 KoBERT 모델에 전달/입력하기

            # '상담 분석 중' 로딩 창으로 이동하기
            
            # 임시 챗봇 응답
            output = dict()
            output['response'] = "대화 종료"
            return HttpResponse(json.dumps(output), status=200)
    else:
        return render(request, 'chat/chat_test.html', context)