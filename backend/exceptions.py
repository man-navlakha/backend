from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap the response in a standard format
        response.data = {
            'status': 'error',
            'status_code': response.status_code,
            'message': response.data.get('detail', str(exc)),
            'data': response.data
        }
    else:
        # Handling non-DRF (standard Python) exceptions
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        response = Response({
            'status': 'error',
            'status_code': 500,
            'message': 'An unexpected server error occurred.',
            'detail': str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
