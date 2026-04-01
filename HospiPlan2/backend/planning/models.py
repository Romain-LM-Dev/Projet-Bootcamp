"""
Planning app - Gestion des affectations et du planning
"""
from django.db import models
from core.models import TimeStampedModel


class Absence(TimeStampedModel):
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='absences')
    absence_type = models.ForeignKey('core.AbsenceType', on_delete=models.PROTECT)
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    is_planned = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff} - {self.absence_type} ({self.start_date})"


class Preference(TimeStampedModel):
    PREF_TYPES = [('wish', 'Souhait'), ('constraint', 'Contrainte impérative')]

    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='preferences')
    type = models.CharField(max_length=20, choices=PREF_TYPES, default='wish')
    description = models.TextField()
    is_hard_constraint = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    priority = models.IntegerField(default=5)

    class Meta:
        ordering = ['-priority']

    def __str__(self):
        return f"{self.staff} - {self.description[:50]}"


class ShiftAssignment(TimeStampedModel):
    STATUS_CHOICES = [('confirmed', 'Confirmé'), ('pending', 'En attente'), ('cancelled', 'Annulé')]
    SOURCE_CHOICES = [('manual', 'Manuel'), ('auto', 'Automatique'), ('swap', 'Échange')]

    shift = models.ForeignKey('shifts.Shift', on_delete=models.CASCADE, related_name='assignments')
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='shift_assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['shift', 'staff']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.staff} → {self.shift}"


class PlanningSnapshot(TimeStampedModel):
    STATUS_CHOICES = [('draft', 'Brouillon'), ('published', 'Publié'), ('archived', 'Archivé')]

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    service = models.ForeignKey('core.Service', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_assignments = models.IntegerField(default=0)
    coverage_rate = models.FloatField(default=0.0)
    soft_constraint_score = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"