from django.db import models
from account.models import User
from chat.models import ChatRoom

class ConsultMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    chat_id = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.CharField(max_length=30, choices=(('student', '학생'), ('teacher', '선생님')))
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # 나중에 null 지우기
    message_text = models.TextField()
    message_time = models.DateTimeField(auto_now_add=True)     # 처음 생성 일시만 자동 기록 

    def __str__(self):
        return f'Consult[{self.message_id}] {self.sender}'

class ConsultRoom(models.Model):
    consult_id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_student')
    teacher_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_teacher')
    consult_date = models.DateField(auto_now=True)      # 마지막 수정 일시 (자동 업데이트)

    def __str__(self):
        return f'ConsultRoom[{self.consult_id}] {self.student_id}'
