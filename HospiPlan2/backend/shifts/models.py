"""
Shifts app - Gestion des postes de garde
"""
from django.db import models
from core.models import TimeStampedModel, CareUnit, ShiftType


class Shift(TimeStampedModel):
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE, related_name='shifts')
    shift_type = models.ForeignKey(ShiftType, on_delete=models.PROTECT)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    min_staff = models.IntegerField(default=1)
    max_staff = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.care_unit} - {self.start_datetime:%d/%m %H:%M}"

    @property
    def label(self):
        return f"{self.care_unit.name} — {self.start_datetime:%d/%m %H:%M}"


class ShiftTemplate(TimeStampedModel):
    name = models.CharField(max_length=100)
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE, related_name='shift_templates')
    shift_type = models.ForeignKey(ShiftType, on_delete=models.PROTECT)
    days_of_week = models.CharField(max_length=7)
    start_time = models.TimeField()
    end_time = models.TimeField()
    min_staff = models.IntegerField(default=1)
    max_staff = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['care_unit', 'name']

    def __str__(self):
        return self.name


class ShiftSwapRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
        ('cancelled', 'Annulé'),
    ]

    requester = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='swap_requests')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='swap_requests')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester} - {self.shift}"