import time
import logging

logger = logging.getLogger(__name__)

class ResponseTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        logger.info(f"Path: {request.path} | Method: {request.method} | Duration: {duration:.2f}s | Status: {response.status_code}")
        
        # Also add it to the header for debugging
        response['X-Response-Time'] = str(duration)
        
        return response
