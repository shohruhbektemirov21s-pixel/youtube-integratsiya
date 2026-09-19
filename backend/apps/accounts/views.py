"""
Views for user registration, authentication, and profile management.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "success": True,
                    "message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi.",
                    "data": {
                        "user": UserSerializer(user).data,
                        "token": token.key,
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Ma'lumotlarni tekshirishda xatolik yuz berdi.",
                    "details": serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "success": True,
                "message": "Tizimga muvaffaqiyatli kirildi.",
                "data": {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                }
            })
        return Response(
            {
                "success": False,
                "error": {
                    "code": "AuthenticationError",
                    "message": "Autentifikatsiyada xatolik yuz berdi.",
                    "details": serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            Token.objects.filter(user=request.user).delete()
        except Exception:
            pass
        return Response({
            "success": True,
            "message": "Tizimdan muvaffaqiyatli chiqildi."
        })


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "success": True,
            "data": UserSerializer(request.user).data
        })
