# chat/models.py
from django.db import models
from account.models import User

class ChatRoom(models.Model):
    chat_id = models.AutoField(primary_key=True, unique=True)
    student_id = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_date = models.DateField(auto_now_add=True)     # 처음 생성 일시만 자동 기록 

    def __str__(self):
        return f'ChatRoom[{self.chat_id}] {self.student_id}'

class ChatMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    chat_id = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.CharField(max_length=30, choices=(('student', '학생'), ('chatbot', '챗봇')))
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # 학생 정보 연결
    message_text = models.TextField()
    message_time = models.DateTimeField(auto_now_add=True)     # 처음 생성 일시만 자동 기록 

    def __str__(self):
        return f'ChatMessage[{self.message_id}] {self.sender}'

class AllDialogue(models.Model):    # 모든 메시지 합쳐서 하나로 관리 (KoBERT, KoBART에 전송)
    dialogue_id = models.AutoField(primary_key=True)
    chat_id = models.OneToOneField(ChatRoom, on_delete=models.CASCADE)
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # 나중에 null 없애기
    dialogue_text = models.TextField()
 
class ConsultResult(models.Model):    # 상담 결과
    member_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    result_time = models.DateTimeField(auto_now_add=True)
    keyword = models.ImageField(null=True)
    category = models.TextField(null=True)

    emotion_temp = models.FloatField()
    summary = models.TextField()
    emotion_list = models.JSONField()
    want_consult = models.BooleanField()
    chat_id = models.OneToOneField(ChatRoom, on_delete=models.CASCADE, primary_key=True)
 