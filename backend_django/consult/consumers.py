# consult/consumers.py
# 소비자를 비동기(AsyncWebsocketConsumer)로 다시 작성함
# Websocket으로 채팅방 그룹 출입, 메시지 수신, 발신

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import ConsultMessage, ConsultRoom
from account.models import User

class ChatConsumer(WebsocketConsumer):
    # Preload last all messages
    def fetch_messages(self, data):
        messages = ConsultMessage.last_all_massages()
        content = {
            'command': 'messages',
            'messages': self.messages_to_json(messages)
        }
        self.send_message(content)

    # Send New Message + User info
    def new_message(self, data):
        # room.html에서 전달받은 데이터
        # consult_id = data['consult_id']  
        author = data['from']
        author_user = User.objects.filter(username=author)[0]   # username
        # 새 메시지 객체 생성
        message = ConsultMessage.objects.create(
            author = author_user,
            content = data['message'],
            # consult_id=consult_id
        )
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message)    # one message
        }
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        # loop & serialize a list of messages to json objects
        for message in messages:
            result.append(self.message_to_json(message))
        return result
    
    def message_to_json(self, message):
        # serialize each message
        return {
            'author': message.author.username,
            'content': message.content,
            'timestamp': str(message.timestamp)
        }

    # commands에 따라 다른 함수 실행
    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = 'chat_%s' % self.room_name
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, 
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, 
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        # command 딕셔너리 수신해서 메시지 종류별 처리를 관리
        self.commands[data['command']](self, data)

    # Send message to room group
    def send_chat_message(self, message):       
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, 
            {
                "type": "chat_message", 
                "message": message
            }
        )

    # Send LAST MESSAGES to WebSocket
    def send_message(self, message):
        self.send(text_data=json.dumps(message))
    
    # Send NEW MESSAGE to WebSocket
    def chat_message(self, event):
        # Receive message from room group
        message = event["message"]
        self.send(text_data=json.dumps(message))