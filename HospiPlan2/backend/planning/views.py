"""Planning app views"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Absence, Preference, ShiftAssignment, PlanningSnapshot
from .serializers import (
    AbsenceSerializer, PreferenceSerializer,
    ShiftAssignmentSerializer, ShiftAssignmentCreateSerializer,
    PlanningSnapshotSerializer
)


class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.select_related('staff', 'absence_type').all()
    serializer_class = AbsenceSerializer
    search_fields = ['staff__first_name', 'staff__last_name', 'absence_type__name']
    ordering_fields = ['start_date', 'staff']

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(expected_end_date__gte=start_date)
        if end_date:
            qs = qs.filter(start_date__lte=end_date)
        return qs


class PreferenceViewSet(viewsets.ModelViewSet):
    queryset = Preference.objects.select_related('staff').all()
    serializer_class = PreferenceSerializer
    search_fields = ['staff__first_name', 'staff__last_name', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs


class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ShiftAssignment.objects.select_related('staff', 'shift__care_unit__service', 'shift__shift_type').all()
    search_fields = ['staff__first_name', 'staff__last_name', 'shift__care_unit__name']
    ordering_fields = ['assigned_at', 'staff', 'shift']

    def get_serializer_class(self):
        if self.action == 'create':
            return ShiftAssignmentCreateSerializer
        return ShiftAssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        shift_id = self.request.query_params.get('shift')
        if shift_id:
            qs = qs.filter(shift_id=shift_id)
        start_date = self.request.query_params.get('start_date')
        if start_date:
            qs = qs.filter(shift__start_datetime__date__gte=start_date)
        end_date = self.request.query_params.get('end_date')
        if end_date:
            qs = qs.filter(shift__start_datetime__date__lte=end_date)
        return qs


class PlanningSnapshotViewSet(viewsets.ModelViewSet):
    queryset = PlanningSnapshot.objects.select_related('service').all()
    serializer_class = PlanningSnapshotSerializer
    search_fields = ['name', 'service__name']
    ordering_fields = ['start_date', 'end_date', 'created_at']