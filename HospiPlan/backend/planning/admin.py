from django.contrib import admin
from .models import (
    Staff, Role, StaffRole, Specialty, StaffSpecialty,
    ContractType, Contract, Certification, StaffCertification,
    Service, CareUnit, ShiftType, Shift, ShiftAssignment,
    AbsenceType, Absence, Preference, Rule,
)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["first_name", "last_name", "email"]

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["care_unit", "shift_type", "start_datetime", "end_datetime", "min_staff", "max_staff"]
    list_filter = ["shift_type", "care_unit__service"]
    date_hierarchy = "start_datetime"

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ["staff", "shift", "assigned_at"]
    list_filter = ["shift__shift_type"]

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ["staff", "absence_type", "start_date", "expected_end_date", "is_planned"]
    list_filter = ["absence_type", "is_planned"]

admin.site.register(Role)
admin.site.register(Specialty)
admin.site.register(ContractType)
admin.site.register(Contract)
admin.site.register(Certification)
admin.site.register(StaffCertification)
admin.site.register(Service)
admin.site.register(CareUnit)
admin.site.register(ShiftType)
admin.site.register(AbsenceType)
admin.site.register(Preference)
admin.site.register(Rule)
