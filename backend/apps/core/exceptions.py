"""
Consistent error handling and response formatting for DRF.
Harden against sensitive information disclosure in production environments.
"""
from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Returns consistent JSON structure for any API exception:
    {
        "success": False,
        "error": {
            "code": "...",
            "message": "...",
            "details": {...}
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "success": False,
            "error": {
                "code": exc.__class__.__name__,
                "message": getattr(exc, 'default_detail', str(exc)),
                "details": response.data,
            }
        }
        response.data = error_payload
        return response

    # Unhandled exceptions (500)
    view = context.get('view', None)
    logger.error(f"Unhandled exception in {view}: {str(exc)}", exc_info=True)

    # Prevent information disclosure: only show details in DEBUG mode
    details = str(exc) if getattr(settings, 'DEBUG', False) else None

    return Response(
        {
            "success": False,
            "error": {
                "code": "InternalServerError",
                "message": "Kutilmagan server xatosi yuz berdi. Iltimos qayta urinib ko'ring.",
                "details": details,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
