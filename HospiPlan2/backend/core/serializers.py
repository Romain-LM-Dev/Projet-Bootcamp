"""Core app serializers"""
from rest_framework import serializers
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class CareUnitSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = CareUnit
        fields = '__all__'


class ShiftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftType
        fields = '__all__'


class AbsenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceType
        fields = '__all__'