"""Optimization app serializers"""
from rest_framework import serializers
from .models import OptimizationAlgorithm, OptimizationConfig, OptimizationRun, OptimizationResult


class OptimizationAlgorithmSerializer(serializers.ModelSerializer):
    algo_type_display = serializers.CharField(source='get_algo_type_display', read_only=True)

    class Meta:
        model = OptimizationAlgorithm
        fields = '__all__'


class OptimizationConfigSerializer(serializers.ModelSerializer):
    algorithm_name = serializers.CharField(source='algorithm.name', read_only=True)

    class Meta:
        model = OptimizationConfig
        fields = '__all__'


class OptimizationRunSerializer(serializers.ModelSerializer):
    config_name = serializers.CharField(source='config.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OptimizationRun
        fields = '__all__'


class OptimizationResultSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    run_name = serializers.CharField(source='run.name', read_only=True)

    class Meta:
        model = OptimizationResult
        fields = '__all__'


class OptimizationGenerateSerializer(serializers.Serializer):
    """Serializer for the generate endpoint."""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    service_id = serializers.IntegerField(required=False, allow_null=True)
    config_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être postérieure à la date de début'
            })
        return attrs