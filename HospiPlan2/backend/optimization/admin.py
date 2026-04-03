"""Optimization app admin configuration"""
from django.contrib import admin
from .models import OptimizationAlgorithm, OptimizationConfig, OptimizationRun, OptimizationResult


@admin.register(OptimizationAlgorithm)
class OptimizationAlgorithmAdmin(admin.ModelAdmin):
    list_display = ('name', 'algo_type', 'is_active', 'description')
    list_filter = ('algo_type', 'is_active')
    search_fields = ('name', 'description')


@admin.register(OptimizationConfig)
class OptimizationConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'algorithm', 'is_active', 'max_iterations', 'time_limit_seconds', 'created_at')
    list_filter = ('algorithm', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'algorithm', 'is_active')
        }),
        ('Poids des contraintes molles', {
            'fields': (
                'weight_consecutive_nights',
                'weight_preferences',
                'weight_workload_balance',
                'weight_service_changes',
                'weight_weekend_equity',
                'weight_adaptation_period',
                'weight_continuity'
            )
        }),
        ('Paramètres d\'exécution', {
            'fields': ('max_iterations', 'time_limit_seconds')
        }),
    )


@admin.register(OptimizationRun)
class OptimizationRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'config', 'service', 'start_date', 'end_date', 'status', 'coverage_rate', 'total_score', 'created_at')
    list_filter = ('status', 'config', 'service')
    search_fields = ('name', 'service__name')
    date_hierarchy = 'start_date'
    readonly_fields = ('started_at', 'completed_at', 'total_assignments', 'total_shifts', 'coverage_rate', 'total_score', 'log', 'error_message')

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'config', 'service', 'start_date', 'end_date')
        }),
        ('Statut et résultats', {
            'fields': ('status', 'started_at', 'completed_at', 'total_assignments', 'total_shifts', 'coverage_rate', 'total_score')
        }),
        ('Logs', {
            'fields': ('log', 'error_message'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OptimizationResult)
class OptimizationResultAdmin(admin.ModelAdmin):
    list_display = ('run', 'staff', 'total_score', 'total_shifts_assigned')
    list_filter = ('run',)
    search_fields = ('staff__first_name', 'staff__last_name', 'run__name')
    raw_id_fields = ('run', 'staff')