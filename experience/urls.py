from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExperienceViewSet

router = DefaultRouter()
router.register(r'', ExperienceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
