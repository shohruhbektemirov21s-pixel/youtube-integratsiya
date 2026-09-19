from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


class HealthCheckView(APIView):
    """
    Health check endpoint to verify API and Database status.
    """
    def get(self, request):
        db_status = "ok"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        except Exception as exc:
            db_status = f"unhealthy: {str(exc)}"

        return Response(
            {
                "status": "online",
                "service": "youtube-integratsiya-backend",
                "database": db_status,
                "version": "1.0.0",
            },
            status=status.HTTP_200_OK if db_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
        )
