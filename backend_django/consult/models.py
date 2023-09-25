# consult/models.py

from django.db import models
from account.models import User

class ConsultRoom(models.Model):
    room_id = models.AutoField(primary_key=True)     # room id
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_student', null=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consult_teacher', null=True)      
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)        # 마지막 수정 일시 (자동 업데이트)

    def __str__(self):
        return f'ConsultRoom[{self.room_id}]'
    
    def has_unread_notification(self, user):    # 미확인 알림이 있는가?
        return Notification.objects.filter(receiver=user, consult_room=self, is_read=False).exists()
    
    def mark_notifications_as_read(self, user): # 채팅방에 들어가면 모든 알림을 읽음으로 표시하기
        # Mark all unread notifications in this room as read for the given user
        unread_notifications = Notification.objects.filter(
            consult_room=self,
            receiver=user,
            is_read=False
        )
        for notification in unread_notifications:
            notification.mark_as_read()
    
class ConsultMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    room_id = models.ForeignKey(ConsultRoom, on_delete=models.CASCADE, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_messages', null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)     # 처음 생성 일시만 자동 기록
    is_consult_request = models.BooleanField(default=False)   # 상담 신청 메시지인가?

    def __str__(self):
        return f'ConsultMessage[{self.message_id}] {self.content} by {self.author.username} in {self.room_id}'
    
    def last_all_messages(self, room_id):
        return ConsultMessage.objects.filter(room_id=room_id).order_by('timestamp').all()

# 새로운 메시지(상담 신청 포함) 전송 시 알림 모델 생성
class Notification(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications', null=True)
    consult_room = models.ForeignKey(ConsultRoom, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    # 새 메시지 전송 시 알림 생성
    @classmethod
    def create_notification(cls, sender, receiver, consult_room):
        notification = cls.objects.create(
            sender=sender,
            receiver=receiver,
            consult_room=consult_room,
            is_read=False  # Set is_read to False initially
        )
        return notification

    # 수신자가 메시지 읽으면 is_read 업데이트
    def mark_as_read(self): 
        self.is_read = True
        self.save()

    class Meta:
        ordering = ['-created_at']  # 최신 순으로 나열
