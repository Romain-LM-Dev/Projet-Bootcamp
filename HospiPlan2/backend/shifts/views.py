"""Shifts app views"""
from rest_framework import viewsets
from .models import Shift, ShiftTemplate, ShiftSwapRequest
from .serializers import ShiftSerializer, ShiftTemplateSerializer, ShiftSwapRequestSerializer


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.select_related('care_unit__service', 'shift_type').all()
    serializer_class = ShiftSerializer
    search_fields = ['care_unit__name', 'shift_type__name']
    ordering_fields = ['start_datetime', 'care_unit']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(start_datetime__date__gte=start_date)
        if end_date:
            qs = qs.filter(start_datetime__date__lte=end_date)
        return qs


class ShiftTemplateViewSet(viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.select_related('care_unit__service', 'shift_type').all()
    serializer_class = ShiftTemplateSerializer
    search_fields = ['name', 'care_unit__name']
    ordering_fields = ['care_unit', 'name']


class ShiftSwapRequestViewSet(viewsets.ModelViewSet):
    queryset = ShiftSwapRequest.objects.select_related('requester', 'shift').all()
    serializer_class = ShiftSwapRequestSerializer
    search_fields = ['requester__first_name', 'requester__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(requester_id=staff_id)
        return qs