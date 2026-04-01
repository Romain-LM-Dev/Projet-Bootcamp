"""Staff app views"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Staff, Role, Specialty, Certification, ContractType, Contract, StaffRole, StaffSpecialty, StaffCertification
from .serializers import (
    StaffSerializer, StaffDetailSerializer, StaffWriteSerializer,
    RoleSerializer, SpecialtySerializer, CertificationSerializer,
    ContractTypeSerializer, ContractSerializer,
    StaffRoleSerializer, StaffSpecialtySerializer, StaffCertificationSerializer
)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return StaffSerializer
        elif self.action == 'retrieve':
            return StaffDetailSerializer
        return StaffWriteSerializer

    def get_queryset(self):
        qs = Staff.objects.prefetch_related('staff_roles__role', 'staff_specialties__specialty')
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs.order_by('last_name', 'first_name')


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    search_fields = ['name']
    ordering_fields = ['name']


class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class ContractTypeViewSet(viewsets.ModelViewSet):
    queryset = ContractType.objects.all()
    serializer_class = ContractTypeSerializer
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('staff', 'contract_type')
    serializer_class = ContractSerializer
    search_fields = ['staff__first_name', 'staff__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs


class StaffRoleViewSet(viewsets.ModelViewSet):
    queryset = StaffRole.objects.select_related('staff', 'role')
    serializer_class = StaffRoleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs


class StaffSpecialtyViewSet(viewsets.ModelViewSet):
    queryset = StaffSpecialty.objects.select_related('staff', 'specialty')
    serializer_class = StaffSpecialtySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs


class StaffCertificationViewSet(viewsets.ModelViewSet):
    queryset = StaffCertification.objects.select_related('staff', 'certification')
    serializer_class = StaffCertificationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs