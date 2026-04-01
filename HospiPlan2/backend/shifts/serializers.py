"""Shifts app serializers"""
from rest_framework import serializers
from .models import Shift, ShiftTemplate, ShiftSwapRequest


class ShiftSerializer(serializers.ModelSerializer):
    care_unit_name = serializers.CharField(source='care_unit.name', read_only=True)
    service_name = serializers.CharField(source='care_unit.service.name', read_only=True)
    shift_type_name = serializers.CharField(source='shift_type.name', read_only=True)
    assigned_count = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ['id', 'label', 'care_unit', 'care_unit_name', 'service_name',
                  'shift_type', 'shift_type_name', 'start_datetime', 'end_datetime',
                  'min_staff', 'max_staff', 'assigned_count', 'is_active', 'notes']

    def get_assigned_count(self, obj):
        return obj.assignments.count()

    def get_label(self, obj):
        return obj.label


class ShiftTemplateSerializer(serializers.ModelSerializer):
    care_unit_name = serializers.CharField(source='care_unit.name', read_only=True)
    shift_type_name = serializers.CharField(source='shift_type.name', read_only=True)

    class Meta:
        model = ShiftTemplate
        fields = '__all__'


class ShiftSwapRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.full_name', read_only=True)
    shift_label = serializers.CharField(source='shift.label', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ShiftSwapRequest
        fields = '__all__'