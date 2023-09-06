from rest_framework import serializers
from chat.models import ConsultResult
from django.contrib.auth import get_user_model


User = get_user_model()

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultResult
        fields = ('chat_id', 'keyword', 'emotion_temp', 'result_time', 'summary', 'emotion_list', 'category', 'is_read')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'profile_photo')

class ResultListSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="member_id.username")
    profile_photo = serializers.ImageField(source="member_id.profile_photo")

    class Meta:
        model = ConsultResult
        fields = ('chat_id', 'emotion_temp', 'result_time', 'category', 'is_read', 'username', 'profile_photo')