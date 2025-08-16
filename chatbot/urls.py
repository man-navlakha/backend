# your_app/urls.py

from django.urls import path
from .views import chatbot_reply, submit_hiring_request, synthesize_speech

urlpatterns = [
    path('chat/', chatbot_reply),
    path('hire/', submit_hiring_request),
      path('synthesize-speech/', synthesize_speech), # Add this line
]