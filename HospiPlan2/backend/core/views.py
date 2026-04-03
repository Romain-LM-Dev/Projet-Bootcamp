"""Core app views"""
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType
from .serializers import (
    RuleSerializer, ServiceSerializer,
    CareUnitSerializer, ShiftTypeSerializer, AbsenceTypeSerializer
)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    search_fields = ['name', 'code']


class CareUnitViewSet(viewsets.ModelViewSet):
    queryset = CareUnit.objects.select_related('service').all()
    serializer_class = CareUnitSerializer
    search_fields = ['name', 'code', 'service__name']


class ShiftTypeViewSet(viewsets.ModelViewSet):
    queryset = ShiftType.objects.all()
    serializer_class = ShiftTypeSerializer


class AbsenceTypeViewSet(viewsets.ModelViewSet):
    queryset = AbsenceType.objects.all()
    serializer_class = AbsenceTypeSerializer


class AuthLoginView(APIView):
    """
    Custom login view for API authentication.
    Accepts JSON payload: {"username": "...", "password": "..."}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return Response(
                    {'detail': 'Nom d\'utilisateur et mot de passe requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return Response({
                    'detail': 'Connexion réussie',
                    'user': {
                        'pk': user.pk,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'detail': 'Identifiants invalides'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            return Response(
                {'detail': f'Erreur de connexion: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuthLogoutView(APIView):
    """
    Custom logout view for API authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


class AuthUserView(APIView):
    """
    Get current user information.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'pk': request.user.pk,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            })
        else:
            return Response({'detail': 'Non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)