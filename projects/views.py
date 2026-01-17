from rest_framework import viewsets
from django.db.models import F
from .models import Project
from .serializers import ProjectSerializer
import logging

logger = logging.getLogger(__name__)
from rest_framework.decorators import action
from rest_framework.response import Response
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increments the view count for a specific project atomically."""
        Project.objects.filter(pk=pk).update(views=F('views') + 1)
        project = self.get_object()
        return Response({"message": f"Views for {project.title} incremented to {project.views}."})
