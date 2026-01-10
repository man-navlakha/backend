from rest_framework import serializers
from .models import HiringRequest, ContactRequest

class HiringRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiringRequest
        fields = ['id', 'name', 'email', 'message', 'created_at']

class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']