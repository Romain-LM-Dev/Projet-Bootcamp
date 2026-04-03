"""Shifts app admin configuration"""
from django.contrib import admin
from .models import Shift, ShiftTemplate, ShiftSwapRequest


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    readonly_fields = ('label',)
    fields = ('label', 'shift_type', 'start_datetime', 'end_datetime', 'min_staff', 'max_staff', 'is_active')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('label', 'care_unit', 'shift_type', 'start_datetime', 'end_datetime', 'min_staff', 'max_staff', 'assigned_count', 'is_active')
    list_filter = ('shift_type', 'care_unit__service', 'is_active')
    search_fields = ('care_unit__name', 'shift_type__name')
    date_hierarchy = 'start_datetime'
    readonly_fields = ('label',)
    raw_id_fields = ('care_unit', 'shift_type')

    def assigned_count(self, obj):
        return obj.assignments.count()
    assigned_count.short_description = 'Effectif assigné'


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'care_unit', 'shift_type', 'days_of_week', 'start_time', 'end_time', 'min_staff', 'max_staff', 'is_active')
    list_filter = ('shift_type', 'care_unit__service', 'is_active')
    search_fields = ('name', 'care_unit__name')
    raw_id_fields = ('care_unit', 'shift_type')


@admin.register(ShiftSwapRequest)
class ShiftSwapRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'shift', 'status', 'created_at')
    list_filter = ('status', 'shift__shift_type')
    search_fields = ('requester__first_name', 'requester__last_name', 'shift__care_unit__name')
    raw_id_fields = ('requester', 'shift')
    date_hierarchy = 'created_at'