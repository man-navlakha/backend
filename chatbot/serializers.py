from rest_framework import serializers
from .models import HiringRequest

class HiringRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiringRequest
        fields = ['id', 'name', 'email', 'message', 'created_at']