"""Planning app admin configuration"""
from django.contrib import admin
from .models import Absence, Preference, ShiftAssignment, PlanningSnapshot


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'absence_type', 'start_date', 'expected_end_date', 'is_planned')
    list_filter = ('absence_type', 'is_planned')
    search_fields = ('staff__first_name', 'staff__last_name', 'absence_type__name')
    raw_id_fields = ('staff', 'absence_type')
    date_hierarchy = 'start_date'


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'type', 'description', 'is_hard_constraint', 'priority')
    list_filter = ('type', 'is_hard_constraint')
    search_fields = ('staff__first_name', 'staff__last_name', 'description')
    raw_id_fields = ('staff',)


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('staff', 'shift_label', 'care_unit', 'service', 'start_datetime', 'status', 'source')
    list_filter = ('status', 'source', 'shift__shift_type', 'shift__care_unit__service')
    search_fields = ('staff__first_name', 'staff__last_name', 'shift__care_unit__name')
    raw_id_fields = ('staff', 'shift')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    def shift_label(self, obj):
        return obj.shift.label
    shift_label.short_description = 'Poste'

    def care_unit(self, obj):
        return obj.shift.care_unit.name if obj.shift else '-'
    care_unit.short_description = 'Unité'

    def service(self, obj):
        return obj.shift.care_unit.service.name if obj.shift and obj.shift.care_unit else '-'
    service.short_description = 'Service'

    def start_datetime(self, obj):
        return obj.shift.start_datetime if obj.shift else '-'
    start_datetime.short_description = 'Début'


@admin.register(PlanningSnapshot)
class PlanningSnapshotAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'start_date', 'end_date', 'status', 'total_assignments', 'coverage_rate', 'created_at')
    list_filter = ('status', 'service')
    search_fields = ('name', 'service__name')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')