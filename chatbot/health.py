from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

def health_check(request):
    health = {"status": "healthy", "database": "connected"}
    try:
        connections['default'].cursor()
    except OperationalError:
        health["status"] = "unhealthy"
        health["database"] = "disconnected"
    
    return JsonResponse(health, status=200 if health["status"] == "healthy" else 500)
