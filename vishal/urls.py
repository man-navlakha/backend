# your_app/urls.py

from django.urls import path
from .views import chatbot_reply, submit_hiring_request, generate_sticker_image 

urlpatterns = [
    path('chat/', chatbot_reply),
    path('hire/', submit_hiring_request),
    path('api/generate-sticker/', generate_sticker_image, name='generate_sticker_image'),
    
]