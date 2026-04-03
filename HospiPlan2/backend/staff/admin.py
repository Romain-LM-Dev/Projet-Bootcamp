"""Staff app admin configuration"""
from django.contrib import admin
from .models import (
    Role, Specialty, Certification,
    Staff, StaffRole, StaffSpecialty, StaffCertification,
    ContractType, Contract
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code')


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'requires_renewal', 'validity_period_months')
    list_filter = ('requires_renewal',)
    search_fields = ('name', 'code')




class StaffRoleInline(admin.TabularInline):
    model = StaffRole
    extra = 1
    raw_id_fields = ('role',)


class StaffSpecialtyInline(admin.TabularInline):
    model = StaffSpecialty
    extra = 1
    raw_id_fields = ('specialty',)


class StaffCertificationInline(admin.TabularInline):
    model = StaffCertification
    extra = 1
    raw_id_fields = ('certification',)


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 1
    raw_id_fields = ('contract_type',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'employee_id', 'is_active', 'hire_date')
    list_filter = ('is_active', 'hire_date')
    search_fields = ('first_name', 'last_name', 'email', 'employee_id')
    inlines = [StaffRoleInline, StaffSpecialtyInline, StaffCertificationInline, ContractInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ('staff', 'role')
    list_filter = ('role',)
    raw_id_fields = ('staff', 'role')


@admin.register(StaffSpecialty)
class StaffSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('staff', 'specialty', 'level')
    list_filter = ('specialty', 'level')
    raw_id_fields = ('staff', 'specialty')


@admin.register(StaffCertification)
class StaffCertificationAdmin(admin.ModelAdmin):
    list_display = ('staff', 'certification', 'obtained_date', 'expiration_date')
    list_filter = ('certification',)
    raw_id_fields = ('staff', 'certification')
    date_hierarchy = 'obtained_date'


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'max_hours_per_week', 'leave_days_per_year', 'night_shift_allowed')
    list_filter = ('night_shift_allowed',)
    search_fields = ('name', 'code')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('staff', 'contract_type', 'start_date', 'end_date', 'workload_percent', 'is_current')
    list_filter = ('contract_type', 'is_current')
    raw_id_fields = ('staff',)
    date_hierarchy = 'start_date'