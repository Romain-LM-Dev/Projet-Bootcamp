"""Optimization app views"""
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework import status
from .models import OptimizationAlgorithm, OptimizationConfig, OptimizationRun, OptimizationResult
from .serializers import (
    OptimizationAlgorithmSerializer, OptimizationConfigSerializer,
    OptimizationRunSerializer, OptimizationResultSerializer,
    OptimizationGenerateSerializer
)


class OptimizationAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = OptimizationAlgorithm.objects.filter(is_active=True)
    serializer_class = OptimizationAlgorithmSerializer
    search_fields = ['name']
    ordering_fields = ['name']


class OptimizationConfigViewSet(viewsets.ModelViewSet):
    queryset = OptimizationConfig.objects.filter(is_active=True)
    serializer_class = OptimizationConfigSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class OptimizationRunViewSet(viewsets.ModelViewSet):
    queryset = OptimizationRun.objects.select_related('config', 'service').all()
    serializer_class = OptimizationRunSerializer
    search_fields = ['name', 'service__name']
    ordering_fields = ['start_date', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        service_id = self.request.query_params.get('service')
        if service_id:
            qs = qs.filter(service_id=service_id)
        return qs


class OptimizationResultViewSet(viewsets.ModelViewSet):
    queryset = OptimizationResult.objects.select_related('run', 'staff').all()
    serializer_class = OptimizationResultSerializer
    search_fields = ['staff__first_name', 'staff__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        run_id = self.request.query_params.get('run')
        if run_id:
            qs = qs.filter(run_id=run_id)
        return qs


class GeneratePlanningView(views.APIView):
    """
    Endpoint pour générer un planning automatiquement.
    POST /api/generate/
    """
    def post(self, request):
        serializer = OptimizationGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        service_id = serializer.validated_data.get('service_id')
        config_id = serializer.validated_data.get('config_id')

        # Get or create default config
        if config_id:
            config = OptimizationConfig.objects.get(id=config_id)
        else:
            config = OptimizationConfig.objects.filter(is_active=True).first()
            if not config:
                return Response(
                    {'error': 'No active optimization config found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create optimization run
        run = OptimizationRun.objects.create(
            name=f"Génération {start_date} → {end_date}",
            config=config,
            service_id=service_id,
            start_date=start_date,
            end_date=end_date,
            status='pending'
        )

        # TODO: Implement actual optimization logic here
        # For now, return the run ID
        return Response({
            'status': 'Generation started',
            'run_id': run.id,
            'message': 'Planning generation initiated. Check back for results.'
        }, status=status.HTTP_202_ACCEPTED)