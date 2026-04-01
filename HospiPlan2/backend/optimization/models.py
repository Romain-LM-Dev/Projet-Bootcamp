"""
Optimization app - Moteur d'optimisation du planning
"""
from django.db import models
from core.models import TimeStampedModel


class OptimizationAlgorithm(models.Model):
    ALGO_TYPES = [
        ('greedy', 'Algorithme glouton'),
        ('local_search', 'Recherche locale'),
        ('simulated_annealing', 'Recuit simulé'),
        ('genetic', 'Algorithme génétique'),
    ]

    name = models.CharField(max_length=100, unique=True)
    algo_type = models.CharField(max_length=30, choices=ALGO_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_parameters = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class OptimizationConfig(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Poids des contraintes molles
    weight_consecutive_nights = models.FloatField(default=1.5)
    weight_preferences = models.FloatField(default=1.0)
    weight_workload_balance = models.FloatField(default=2.0)
    weight_service_changes = models.FloatField(default=1.0)
    weight_weekend_equity = models.FloatField(default=0.8)
    weight_adaptation_period = models.FloatField(default=1.2)
    weight_continuity = models.FloatField(default=1.5)

    max_iterations = models.IntegerField(default=100)
    time_limit_seconds = models.IntegerField(default=60)
    algorithm = models.ForeignKey(OptimizationAlgorithm, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class OptimizationRun(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]

    name = models.CharField(max_length=100)
    config = models.ForeignKey(OptimizationConfig, on_delete=models.PROTECT)
    service = models.ForeignKey('core.Service', on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_assignments = models.IntegerField(default=0)
    total_shifts = models.IntegerField(default=0)
    coverage_rate = models.FloatField(default=0.0)
    total_score = models.FloatField(default=0.0)
    log = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"


class OptimizationResult(TimeStampedModel):
    run = models.ForeignKey(OptimizationRun, on_delete=models.CASCADE, related_name='results')
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    total_score = models.FloatField(default=0.0)
    total_shifts_assigned = models.IntegerField(default=0)

    class Meta:
        unique_together = ['run', 'staff']
        ordering = ['-total_score']

    def __str__(self):
        return f"{self.staff} - Score: {self.total_score}"