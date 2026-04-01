"""
Core app - Modèles de base partagés
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Modèle abstrait pour les timestamps automatiques."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Rule(TimeStampedModel):
    """Règles métier configurables (F-10)."""
    RULE_TYPES = [
        ('constraint', 'Contrainte'),
        ('preference', 'Préférence'),
        ('threshold', 'Seuil'),
        ('ratio', 'Ratio'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} = {self.value} {self.unit}"


class Service(TimeStampedModel):
    """Service hospitalier."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managed_services'
    )
    bed_capacity = models.IntegerField(default=0)
    criticality_level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CareUnit(TimeStampedModel):
    """Unité de soin au sein d'un service."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='care_units')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    bed_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['service', 'code']
        ordering = ['service', 'name']

    def __str__(self):
        return f"{self.service.name} - {self.name}"


class ShiftType(TimeStampedModel):
    """Type de poste (Jour, Nuit, 12h, etc.)"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    duration_hours = models.IntegerField()
    requires_rest_after = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    color = models.CharField(max_length=7, default='#3B82F6')

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.duration_hours}h)"


class AbsenceType(TimeStampedModel):
    """Type d'absence."""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    is_paid = models.BooleanField(default=True)
    requires_justification = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#EF4444')

    def __str__(self):
        return self.name