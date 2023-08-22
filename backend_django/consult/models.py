# consult/models.py

from django.db import models
from account.models import User

class ConsultRoom(models.Model):
    consult_id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_student', null=True, blank=True)
    teacher_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_teacher')
    consult_date = models.DateField(auto_now=True)      # 마지막 수정 일시 (자동 업데이트)

    def __str__(self):
        return f'ConsultRoom[{self.consult_id}] {self.teacher_id.username}'
    
class ConsultMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    # consult_id = models.ForeignKey(ConsultRoom, on_delete=models.CASCADE)
    sender = models.CharField(max_length=30, choices=(('student', '학생'), ('teacher', '선생님')))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_messages', null=True)  # 나중에 null 지우기
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)     # 처음 생성 일시만 자동 기록 

    def __str__(self):
        return f'ConsultMessage[{self.message_id}] {self.author.username} ({self.sender})'
    
    def last_all_massages():
        return ConsultMessage.objects.order_by('-timestamp').all()  # .all()[:20] 지난 20개 메시지 preload
