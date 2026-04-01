"""
Staff app - Gestion des soignants et de leurs compétences
"""
from django.db import models
from core.models import TimeStampedModel


class Role(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Specialty(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Specialties'
        ordering = ['name']

    def __str__(self):
        return self.name


class Certification(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    validity_period_months = models.IntegerField(null=True, blank=True)
    requires_renewal = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Staff(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class StaffRole(TimeStampedModel):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['staff', 'role']

    def __str__(self):
        return f"{self.staff} → {self.role}"


class StaffSpecialty(TimeStampedModel):
    LEVELS = [(1, 'Débutant'), (2, 'Intermédiaire'), (3, 'Confirmé'), (4, 'Expert')]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_specialties')
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    level = models.IntegerField(choices=LEVELS, default=2)

    class Meta:
        unique_together = ['staff', 'specialty']

    def __str__(self):
        return f"{self.staff} → {self.specialty}"


class StaffCertification(TimeStampedModel):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_certifications')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    obtained_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['staff', 'certification']

    def __str__(self):
        return f"{self.staff} - {self.certification}"


class ContractType(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    max_hours_per_week = models.IntegerField()
    leave_days_per_year = models.IntegerField()
    night_shift_allowed = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Contract(TimeStampedModel):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.ForeignKey(ContractType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    workload_percent = models.IntegerField(default=100)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff} - {self.contract_type}"