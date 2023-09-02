from rest_framework import serializers
from chat.models import ConsultResult

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultResult
        fields = ('chat_id', 'keyword', 'emotion_temp', 'result_time', 'summary', 'emotion_list', 'category', 'is_read')

