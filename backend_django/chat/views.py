# chat/views.py
from rest_framework import status
from django.shortcuts import render
from django.http import HttpResponse
import json, os
from .kogpt2_chatbot import kogpt2_answer
from .kobert import kobert_result
from .kobart import generate_summary
from .wordcloud import get_wordcloud_data
from django.contrib.auth.decorators import login_required   # 함수형 뷰에만 적용 가능
from .models import ChatRoom, ChatMessage, AllDialogue, ConsultResult   # 모델 임포트

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
            # combined_text = '\n'.join([message.message_text for message in all_messages])
            combined_text = ''

            for message in all_messages:
                 combined_text = combined_text + message.sender + ":" + message.message_text + "\n"

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

# chat/result/<str:user_id>/<int:chatroom_id>/
@login_required               
def chat_result(request, user_id, chatroom_id):
        user = request.user        
        alldialogue = AllDialogue.objects.filter(chat_id=chatroom_id)
        chat_room = ChatRoom.objects.get(chat_id=chatroom_id)
        student_dialogs = []
        combined_text = ''

        if request.method == 'GET':
            lines = alldialogue[0].dialogue_text.strip().split('\n')
            for line in lines:
                role, content = line.split(':', 1)
                role = role.strip()
                combined_text = combined_text + '\n' + content
                content = content.strip()
                if role == 'student':
                     student_dialogs.append(content)

            # KoBERT 이용하여 감정, 우울도 json 가져오기
            category_count, emotion_count, depression_count = kobert_result(student_dialogs)
            wordcloud = get_wordcloud_data(student_dialogs)

            # KeyWord로 WordCloud 이미지 저장하기
            media_path = os.path.join('media', 'wordcloud')
            os.makedirs(media_path, exist_ok=True)
            image_path = os.path.join(media_path, f'{chatroom_id}.png')
            wordcloud.to_file(image_path)
            
            # 요약문 생성하기
            summary = generate_summary(combined_text)

            # JSON으로 만들어서 클라이언트에게 전송
            context_data = {
                'category_count': category_count,
                'emotion_count': emotion_count,
                'depression_count': depression_count,
                'wordcloud':image_path,
                'summary':summary,
            }
            data_json = json.dumps(context_data, ensure_ascii=False)
            return HttpResponse(data_json)
        
        if request.method == 'POST':
            # Payload 받아오기
            data = json.loads(request.body)
            depression_count = data.get('depression_count')
            emotion_count = data.get('emotion_count')
            summary = data.get('summary')
            wordcloud = data.get('wordcloud')
            img_url = wordcloud.split('\\')[-2] + '/' + wordcloud.split('\\')[-1]

            # 결과문 생성하기
            ConsultResult.objects.create(     
                member_id=user,
                keyword = img_url,
                emotion_temp = depression_count,
                summary = summary,
                emotion_list = emotion_count,
                want_consult = True,
                chat_id = chat_room,     
            )

            return HttpResponse(status=status.HTTP_200_OK)

        
