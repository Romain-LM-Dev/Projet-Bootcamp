"""Core app views"""
from rest_framework import viewsets
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType
from .serializers import RuleSerializer, ServiceSerializer, CareUnitSerializer, ShiftTypeSerializer, AbsenceTypeSerializer


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.filter(is_active=True)
    serializer_class = RuleSerializer
    search_fields = ['name', 'category']
    ordering_fields = ['category', 'name']


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class CareUnitViewSet(viewsets.ModelViewSet):
    queryset = CareUnit.objects.all()
    serializer_class = CareUnitSerializer
    search_fields = ['name', 'service__name']
    ordering_fields = ['service', 'name']


class ShiftTypeViewSet(viewsets.ModelViewSet):
    queryset = ShiftType.objects.all()
    serializer_class = ShiftTypeSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['start_time']


class AbsenceTypeViewSet(viewsets.ModelViewSet):
    queryset = AbsenceType.objects.all()
    serializer_class = AbsenceTypeSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['name']