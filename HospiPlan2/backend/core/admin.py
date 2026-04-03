"""Core app admin configuration"""
from django.contrib import admin
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'value', 'unit', 'category', 'is_active')
    list_filter = ('rule_type', 'category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'bed_capacity', 'criticality_level', 'manager', 'is_active')
    list_filter = ('is_active', 'criticality_level')
    search_fields = ('name', 'code', 'description')


@admin.register(CareUnit)
class CareUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'service', 'bed_count')
    list_filter = ('service',)
    search_fields = ('name', 'code')
    ordering = ('service', 'name')


@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'duration_hours', 'start_time', 'end_time', 'requires_rest_after')
    list_filter = ('requires_rest_after',)
    search_fields = ('name', 'code')


@admin.register(AbsenceType)
class AbsenceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_paid', 'requires_justification')
    list_filter = ('is_paid', 'requires_justification')
    search_fields = ('name', 'code')