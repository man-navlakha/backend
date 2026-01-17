from django.urls import path
from .views import chatbot_reply, submit_hiring_request, submit_contact_request

urlpatterns = [
    path('chat/', chatbot_reply),
    path('hire/', submit_hiring_request),
    path('contact/', submit_contact_request),
]