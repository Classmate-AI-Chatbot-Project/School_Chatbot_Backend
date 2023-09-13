# # consult/consumers.py
# # Websocket 요청을 처리하는 함수들 (채팅방 그룹 출입, 메시지 수신&발신)

# from asgiref.sync import async_to_sync
# from channels.generic.websocket import WebsocketConsumer
# import json
# from .models import ConsultMessage, ConsultRoom, Notification
# from account.models import User
# from chat.models import ConsultResult

# class ChatConsumer(WebsocketConsumer):
#     # Preload last all messages to room
#     def fetch_messages(self, data):
#         room_id = int(self.room_name)
#         messages = ConsultMessage.last_all_messages(self, room_id=room_id)
#         content = {
#             'command': 'messages',
#             'messages': self.messages_to_json(messages)
#         }
#         self.send_message(content)

#     # Make & Send New Message from User, Room info
#     def new_message(self, data):
#         author = data['from']   # data 안에 username 담김
#         room_id = int(self.room_name)   # room_id는 websocket 연결 시 room_name에 저장
#         author_user = User.objects.filter(username = author)[0]
#         room_contact = ConsultRoom.objects.filter(room_id=room_id).first()
#         # 새 메시지 객체 생성
#         message = ConsultMessage.objects.create(
#             author = author_user,
#             room_id = room_contact,
#             content = data['message'],
#         )
#         # 알림 생성 & 저장 (발신자가 학생이면 수신자는 선생님)
#         receiver = room_contact.teacher if author_user == room_contact.student else room_contact.student
#         notification = Notification.create_notification(
#             sender=author_user,
#             receiver=receiver,
#             consult_room=room_contact
#         )
#         # 새 메시지 & 알림 전송
#         content = {
#             'command': 'new_message',
#             'message': self.message_to_json(message),   # one message
#             'notification_id': notification.id      # Pass the notification ID to the client
#         }
#         return self.send_chat_message(content)
    

#     def messages_to_json(self, messages):
#         result = []
#         # loop & serialize a list of messages to json objects
#         for message in messages:
#             result.append(self.message_to_json(message))
#         return result
    
#     def message_to_json(self, message):
#         # serialize each message
#         return {
#             'author': message.author.username,
#             'content': message.content,
#             'timestamp': str(message.timestamp),
#         }

#     # commands에 따라 다른 함수 실행
#     commands = {
#         'fetch_messages': fetch_messages,
#         'new_message': new_message,
#     }
    
#     # Websocket 연결
#     def connect(self):
#         # room_name 파라미터를 consult/routing.py URL 에서 얻기
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = 'chat_%s' % self.room_name
#         # Join room group
#         async_to_sync(self.channel_layer.group_add)(
#             self.room_group_name, 
#             self.channel_name
#         )
#         self.accept()   # websocket 연결 수락
        
#     # Leave room group
#     def disconnect(self, close_code):
#         async_to_sync(self.channel_layer.group_discard)(
#             self.room_group_name, 
#             self.channel_name
#         )

#     # Receive message from WebSocket 서버
#     def receive(self, text_data):
#         data = json.loads(text_data)
#         # command 딕셔너리 수신해서 메시지 종류별 처리 (지난 메시지들 / 새 메시지 1개)
#         self.commands[data['command']](self, data)

#     # Send new message to room group in channel layer
#     def send_chat_message(self, message):       
#         async_to_sync(self.channel_layer.group_send)(
#             self.room_group_name, 
#             {
#                 "type": "chat_message", 
#                 "message": message
#             }
#         )

#     # Send LAST MESSAGES to WebSocket Client
#     def send_message(self, message):
#         self.send(text_data=json.dumps(message))    # 메시지들을 json 형태로 인코딩
    
#     # Send NEW MESSAGE to WebSocket Client
#     def chat_message(self, event):
#         # Receive new message from room group
#         message = event["message"]
#         self.send(text_data=json.dumps(message))
