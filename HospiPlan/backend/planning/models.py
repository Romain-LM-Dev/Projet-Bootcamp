"""
Models Django — correspondance exacte avec database_hopital_corrige.sql
Toutes les tables sont mappées ; on ajoute managed=False pour éviter
les migrations sur un schéma existant. Retirez managed=False si vous
partez d'une base vierge et souhaitez que Django la crée.
"""
from django.db import models


class Staff(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "staff"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Role(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "role"

    def __str__(self):
        return self.name


class StaffRole(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="staff_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = "staff_role"
        unique_together = ("staff", "role")


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "specialty"

    def __str__(self):
        return self.name


class StaffSpecialty(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="staff_specialties")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)

    class Meta:
        db_table = "staff_specialty"
        unique_together = ("staff", "specialty")


class ContractType(models.Model):
    name = models.CharField(max_length=100)
    max_hours_per_week = models.IntegerField()
    leave_days_per_year = models.IntegerField()
    night_shift_allowed = models.BooleanField(default=True)

    class Meta:
        db_table = "contract_type"

    def __str__(self):
        return self.name


class Contract(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="contracts")
    contract_type = models.ForeignKey(ContractType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    workload_percent = models.IntegerField(default=100)

    class Meta:
        db_table = "contract"

    def __str__(self):
        return f"{self.staff} — {self.contract_type}"


class Certification(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "certification"

    def __str__(self):
        return self.name


class CertificationDependency(models.Model):
    parent_cert = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name="dependencies")
    required_cert = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name="required_by")

    class Meta:
        db_table = "certification_dependency"
        unique_together = ("parent_cert", "required_cert")


class StaffCertification(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="certifications")
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    obtained_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "staff_certification"

    def __str__(self):
        return f"{self.staff} — {self.certification}"


class Service(models.Model):
    name = models.CharField(max_length=200)
    manager = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_services")
    bed_capacity = models.IntegerField(default=0)
    criticality_level = models.IntegerField(default=1)

    class Meta:
        db_table = "service"

    def __str__(self):
        return self.name


class CareUnit(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="care_units")
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "care_unit"

    def __str__(self):
        return f"{self.service} — {self.name}"


class ServiceStatus(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "service_status"


class StaffServiceAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "staff_service_assignment"


class ShiftType(models.Model):
    name = models.CharField(max_length=100)
    duration_hours = models.IntegerField()
    requires_rest_after = models.BooleanField(default=False)

    class Meta:
        db_table = "shift_type"

    def __str__(self):
        return self.name


class Shift(models.Model):
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE, related_name="shifts")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.PROTECT)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    min_staff = models.IntegerField(default=1)
    max_staff = models.IntegerField(default=10)
    required_certifications = models.ManyToManyField(
        Certification,
        through="ShiftRequiredCertification",
        blank=True,
    )

    class Meta:
        db_table = "shift"

    def __str__(self):
        return f"{self.care_unit} — {self.start_datetime:%Y-%m-%d %H:%M}"

    @property
    def label(self):
        return f"{self.care_unit.name} — {self.start_datetime:%d/%m %H:%M}"


class ShiftRequiredCertification(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)

    class Meta:
        db_table = "shift_required_certification"
        unique_together = ("shift", "certification")


class ShiftAssignment(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="assignments")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="shift_assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shift_assignment"

    def __str__(self):
        return f"{self.staff} → {self.shift}"


class AbsenceType(models.Model):
    name = models.CharField(max_length=100)
    impacts_quota = models.BooleanField(default=True)

    class Meta:
        db_table = "absence_type"

    def __str__(self):
        return self.name


class Absence(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="absences")
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.PROTECT)
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    is_planned = models.BooleanField(default=True)

    class Meta:
        db_table = "absence"


class Preference(models.Model):
    PREF_TYPES = [("souhait", "Souhait"), ("contrainte", "Contrainte impérative")]
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="preferences")
    type = models.CharField(max_length=50, choices=PREF_TYPES)
    description = models.TextField()
    is_hard_constraint = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "preference"


class PatientLoad(models.Model):
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE)
    date = models.DateField()
    patient_count = models.IntegerField()
    occupancy_rate = models.FloatField()

    class Meta:
        db_table = "patient_load"


class StaffLoan(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    from_service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="loans_from")
    to_service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="loans_to")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = "staff_loan"


class Rule(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "rule"

    def __str__(self):
        return self.name
