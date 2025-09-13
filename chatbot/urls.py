# your_app/urls.py

from django.urls import path
from .views import chatbot_reply, submit_hiring_request, synthesize_speech, get_github_activity

urlpatterns = [
    path('chat/', chatbot_reply),
    path('hire/', submit_hiring_request),
      path('synthesize-speech/', synthesize_speech), # Add this line
      
      path('github-activity/', get_github_activity, name='get_github_activity'),
]