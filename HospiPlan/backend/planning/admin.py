from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Staff, Role, StaffRole, Specialty, StaffSpecialty,
    ContractType, Contract, Certification, CertificationDependency,
    StaffCertification,
    Service, CareUnit, ServiceStatus, StaffServiceAssignment,
    ShiftType, Shift, ShiftRequiredCertification, ShiftAssignment,
    AbsenceType, Absence, Preference, PatientLoad, StaffLoan, Rule,
)


# ══════════════════════════════════════════════════════════════════════════════
# INLINES
# ══════════════════════════════════════════════════════════════════════════════

class StaffRoleInline(admin.TabularInline):
    model = StaffRole
    extra = 1
    autocomplete_fields = ["role"]


class StaffSpecialtyInline(admin.TabularInline):
    model = StaffSpecialty
    extra = 1
    autocomplete_fields = ["specialty"]


class StaffCertificationInline(admin.TabularInline):
    model = StaffCertification
    extra = 1
    autocomplete_fields = ["certification"]
    fields = ["certification", "obtained_date", "expiration_date", "is_valid_display"]
    readonly_fields = ["is_valid_display"]

    def is_valid_display(self, obj):
        if not obj.pk:
            return "—"
        if obj.expiration_date is None:
            return mark_safe('<span style="color:green;">✅ Permanente</span>')
        if obj.expiration_date >= timezone.now().date():
            return format_html(
                '<span style="color:green;">��� Valide jusqu\'au {}</span>',
                obj.expiration_date.strftime("%d/%m/%Y")
            )
        return format_html(
            '<span style="color:red;">❌ Expirée le {}</span>',
            obj.expiration_date.strftime("%d/%m/%Y")
        )
    is_valid_display.short_description = "Statut"


class ContractInline(admin.StackedInline):
    model = Contract
    extra = 0
    autocomplete_fields = ["contract_type"]
    fields = [
        ("contract_type", "workload_percent"),
        ("start_date", "end_date"),
    ]


class PreferenceInline(admin.TabularInline):
    model = Preference
    extra = 0
    fields = ["type", "description", "is_hard_constraint", "start_date", "end_date"]


class AbsenceInline(admin.TabularInline):
    model = Absence
    extra = 0
    autocomplete_fields = ["absence_type"]
    fields = ["absence_type", "start_date", "expected_end_date", "actual_end_date", "is_planned"]


class CareUnitInline(admin.TabularInline):
    model = CareUnit
    extra = 1


class ShiftRequiredCertificationInline(admin.TabularInline):
    model = ShiftRequiredCertification
    extra = 1
    autocomplete_fields = ["certification"]


# ──────────────────────────────────────────────────────────────────────────────
# Inline des affectations sur un Shift
# ──────────────────────────────────────────────────────────────────────────────

class ShiftAssignmentInlineForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ["staff"]

    def clean(self):
        cleaned = super().clean()
        staff = cleaned.get("staff")
        shift = self.instance.shift if self.instance.pk else None

        if staff and shift:
            self._validate_constraints(staff, shift)

        return cleaned

    def _validate_constraints(self, staff, shift):
        try:
            from .validators import validate_assignment
            result = validate_assignment(staff, shift)
            if not result["ok"]:
                raise ValidationError(
                    "Contrainte %(code)s : %(detail)s",
                    params={
                        "code": result.get("code", "??"),
                        "detail": result.get("detail", "Contrainte violée."),
                    },
                )
        except ImportError:
            pass


class ShiftAssignmentInline(admin.TabularInline):
    model = ShiftAssignment
    form = ShiftAssignmentInlineForm
    extra = 1
    autocomplete_fields = ["staff"]
    readonly_fields = ["assigned_at"]


class StaffShiftAssignmentInline(admin.TabularInline):
    model = ShiftAssignment
    extra = 0
    autocomplete_fields = ["shift"]
    readonly_fields = ["assigned_at", "shift_info"]
    fields = ["shift", "shift_info", "assigned_at"]

    def shift_info(self, obj):
        if not obj.pk:
            return "—"
        sh = obj.shift
        return format_html(
            "{} — {} → {}",
            sh.care_unit.name,
            sh.start_datetime.strftime("%d/%m %H:%M"),
            sh.end_datetime.strftime("%H:%M"),
        )
    shift_info.short_description = "Détail poste"


# ══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE CUSTOM POUR SHIFTASSIGNMENT (standalone)
# ══════════════════════════════════════════════════════════════════════════════

class ShiftAssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ["staff", "shift"]

    def clean(self):
        cleaned = super().clean()
        staff = cleaned.get("staff")
        shift = cleaned.get("shift")

        if staff and shift:
            existing = ShiftAssignment.objects.filter(staff=staff, shift=shift)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("Ce soignant est déjà affecté à ce poste.")

            try:
                from .validators import validate_assignment
                result = validate_assignment(staff, shift)
                if not result["ok"]:
                    code = result.get("code", "??")
                    detail = result.get("detail", "Contrainte violée.")
                    raise ValidationError(
                        "Contrainte %(code)s violée : %(detail)s",
                        params={"code": code, "detail": detail},
                    )
            except ImportError:
                pass

        return cleaned


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — STAFF
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        "full_name", "email", "is_active", "roles_display",
        "specialties_display", "active_contract_display", "created_at",
    ]
    list_filter = ["is_active", "staff_roles__role", "staff_specialties__specialty"]
    search_fields = ["first_name", "last_name", "email"]
    list_per_page = 30
    ordering = ["last_name", "first_name"]

    fieldsets = (
        ("Informations personnelles", {
            "fields": (
                ("first_name", "last_name"),
                ("email", "phone"),
                "is_active",
            ),
        }),
    )

    inlines = [
        StaffRoleInline,
        StaffSpecialtyInline,
        StaffCertificationInline,
        ContractInline,
        AbsenceInline,
        PreferenceInline,
        StaffShiftAssignmentInline,
    ]

    def full_name(self, obj):
        icon = "🟢" if obj.is_active else "🔴"
        return format_html("{} {} {}", icon, obj.first_name, obj.last_name)
    full_name.short_description = "Soignant"
    full_name.admin_order_field = "last_name"

    def roles_display(self, obj):
        roles = obj.staff_roles.select_related("role").all()
        if not roles:
            return mark_safe('<span style="color:#999;">—</span>')
        return ", ".join(sr.role.name for sr in roles)
    roles_display.short_description = "Rôles"

    def specialties_display(self, obj):
        specs = obj.staff_specialties.select_related("specialty").all()
        if not specs:
            return mark_safe('<span style="color:#999;">—</span>')
        return ", ".join(ss.specialty.name for ss in specs)
    specialties_display.short_description = "Spécialités"

    def active_contract_display(self, obj):
        today = timezone.now().date()
        contract = obj.contracts.select_related("contract_type").filter(
            start_date__lte=today
        ).order_by("-start_date").first()
        if not contract:
            return mark_safe('<span style="color:#c00;">Aucun contrat</span>')
        ct = contract.contract_type
        return format_html("{} ({}%)", ct.name, contract.workload_percent)
    active_contract_display.short_description = "Contrat actif"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "staff_roles__role", "staff_specialties__specialty",
            "contracts__contract_type",
        )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SHIFT
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        "shift_label", "care_unit", "shift_type", "start_datetime",
        "end_datetime", "staffing_display", "certs_display",
    ]
    list_filter = ["shift_type", "care_unit__service", "care_unit"]
    search_fields = ["care_unit__name", "care_unit__service__name"]
    date_hierarchy = "start_datetime"
    list_per_page = 30
    ordering = ["-start_datetime"]
    autocomplete_fields = ["care_unit", "shift_type"]

    fieldsets = (
        ("Poste de garde", {
            "fields": (
                ("care_unit", "shift_type"),
                ("start_datetime", "end_datetime"),
                ("min_staff", "max_staff"),
            ),
        }),
    )

    inlines = [
        ShiftRequiredCertificationInline,
        ShiftAssignmentInline,
    ]

    def shift_label(self, obj):
        return obj.label
    shift_label.short_description = "Poste"

    def staffing_display(self, obj):
        count = obj.assignments.count()
        if count >= obj.min_staff:
            icon = "✅"
            color = "green"
        elif count > 0:
            icon = "⚠️"
            color = "orange"
        else:
            icon = "❌"
            color = "red"
        return format_html(
            '{} <span style="color:{};">{}/{} (min {})</span>',
            icon, color, count, obj.max_staff, obj.min_staff
        )
    staffing_display.short_description = "Effectif"

    def certs_display(self, obj):
        certs = obj.required_certifications.all()
        if not certs:
            return "—"
        return ", ".join(c.name for c in certs)
    certs_display.short_description = "Certifications requises"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "care_unit__service", "shift_type"
        ).prefetch_related("required_certifications", "assignments")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SHIFT ASSIGNMENT (avec validation des contraintes)
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    form = ShiftAssignmentAdminForm
    list_display = [
        "id", "staff_display", "shift_display", "shift_date",
        "shift_type_display", "assigned_at",
    ]
    list_filter = [
        "shift__shift_type",
        "shift__care_unit__service",
        "shift__care_unit",
    ]
    search_fields = [
        "staff__first_name", "staff__last_name",
        "shift__care_unit__name",
    ]
    autocomplete_fields = ["staff", "shift"]
    date_hierarchy = "assigned_at"
    list_per_page = 30
    ordering = ["-assigned_at"]

    fieldsets = (
        ("Affectation", {
            "description": (
                "⚠️ Les contraintes métier (C1→C8) sont vérifiées automatiquement. "
                "L'enregistrement sera refusé si une contrainte dure est violée."
            ),
            "fields": ("staff", "shift"),
        }),
    )

    def staff_display(self, obj):
        icon = "🟢" if obj.staff.is_active else "🔴"
        return format_html("{} {} {}", icon, obj.staff.first_name, obj.staff.last_name)
    staff_display.short_description = "Soignant"
    staff_display.admin_order_field = "staff__last_name"

    def shift_display(self, obj):
        return format_html(
            "{} — {} → {}",
            obj.shift.care_unit.name,
            obj.shift.start_datetime.strftime("%d/%m %H:%M"),
            obj.shift.end_datetime.strftime("%H:%M"),
        )
    shift_display.short_description = "Poste"

    def shift_date(self, obj):
        return obj.shift.start_datetime.strftime("%d/%m/%Y")
    shift_date.short_description = "Date"
    shift_date.admin_order_field = "shift__start_datetime"

    def shift_type_display(self, obj):
        name = obj.shift.shift_type.name
        if "nuit" in name.lower():
            return format_html("{} {}", "🌙", name)
        return format_html("{} {}", "☀️", name)
    shift_type_display.short_description = "Type"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "staff", "shift__care_unit__service", "shift__shift_type"
        )

    actions = ["check_constraints"]

    @admin.action(description="🔍 Vérifier les contraintes des affectations sélectionnées")
    def check_constraints(self, request, queryset):
        errors = []
        ok_count = 0
        try:
            from .validators import validate_assignment
        except ImportError:
            self.message_user(request, "⚠️ Module validators non trouvé.", level="warning")
            return

        for assignment in queryset.select_related("staff", "shift"):
            result = validate_assignment(assignment.staff, assignment.shift)
            if result["ok"]:
                ok_count += 1
            else:
                errors.append(
                    "❌ {} → {} : [{}] {}".format(
                        assignment.staff,
                        assignment.shift.label,
                        result.get("code", "??"),
                        result.get("detail", ""),
                    )
                )

        if errors:
            msg = "✅ {} OK — ❌ {} violations :\n{}".format(
                ok_count, len(errors), "\n".join(errors)
            )
            self.message_user(request, msg, level="warning")
        else:
            self.message_user(
                request,
                "✅ {} affectation(s) vérifiée(s) — Aucune violation.".format(ok_count),
            )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — ABSENCE
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = [
        "staff", "absence_type", "start_date", "expected_end_date",
        "is_planned", "status_display",
    ]
    list_filter = ["absence_type", "is_planned"]
    search_fields = ["staff__first_name", "staff__last_name"]
    autocomplete_fields = ["staff", "absence_type"]
    date_hierarchy = "start_date"

    fieldsets = (
        (None, {
            "fields": (
                "staff",
                "absence_type",
                ("start_date", "expected_end_date"),
                "actual_end_date",
                "is_planned",
            ),
        }),
    )

    def status_display(self, obj):
        today = timezone.now().date()
        end = obj.actual_end_date or obj.expected_end_date
        if today < obj.start_date:
            return mark_safe('<span style="color:blue;">📅 À venir</span>')
        if today <= end:
            return mark_safe('<span style="color:orange;">⚠️ En cours</span>')
        return mark_safe('<span style="color:green;">✅ Terminée</span>')
    status_display.short_description = "Statut"


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — RÉFÉRENTIELS
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "staff_count"]
    search_fields = ["name"]

    def staff_count(self, obj):
        return obj.staffrole_set.count()
    staff_count.short_description = "Soignants"


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "staff_count"]
    search_fields = ["name"]
    autocomplete_fields = ["parent"]

    def staff_count(self, obj):
        return obj.staffspecialty_set.count()
    staff_count.short_description = "Soignants"


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ["name", "holders_count"]
    search_fields = ["name"]

    def holders_count(self, obj):
        return obj.staffcertification_set.count()
    holders_count.short_description = "Titulaires"


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "max_hours_per_week", "leave_days_per_year", "night_shift_allowed"]
    search_fields = ["name"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["staff", "contract_type", "start_date", "end_date", "workload_percent"]
    list_filter = ["contract_type"]
    search_fields = ["staff__first_name", "staff__last_name"]
    autocomplete_fields = ["staff", "contract_type"]


@admin.register(StaffCertification)
class StaffCertificationAdmin(admin.ModelAdmin):
    list_display = ["staff", "certification", "obtained_date", "expiration_date"]
    list_filter = ["certification"]
    search_fields = ["staff__first_name", "staff__last_name", "certification__name"]
    autocomplete_fields = ["staff", "certification"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "manager", "bed_capacity", "criticality_level", "units_count"]
    search_fields = ["name"]
    autocomplete_fields = ["manager"]
    inlines = [CareUnitInline]

    def units_count(self, obj):
        return obj.care_units.count()
    units_count.short_description = "Unités"


@admin.register(CareUnit)
class CareUnitAdmin(admin.ModelAdmin):
    list_display = ["name", "service"]
    list_filter = ["service"]
    search_fields = ["name", "service__name"]
    autocomplete_fields = ["service"]


@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "duration_hours", "requires_rest_after"]
    search_fields = ["name"]


@admin.register(AbsenceType)
class AbsenceTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "impacts_quota"]
    search_fields = ["name"]


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ["staff", "type", "is_hard_constraint", "start_date", "end_date"]
    list_filter = ["type", "is_hard_constraint"]
    search_fields = ["staff__first_name", "staff__last_name", "description"]
    autocomplete_fields = ["staff"]


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ["name", "rule_type", "value", "unit", "valid_from", "valid_to"]
    list_filter = ["rule_type"]
    search_fields = ["name"]


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — MODÈLES SECONDAIRES
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(CertificationDependency)
class CertificationDependencyAdmin(admin.ModelAdmin):
    list_display = ["parent_cert", "required_cert"]
    autocomplete_fields = ["parent_cert", "required_cert"]


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ["service", "status", "start_date", "end_date"]
    list_filter = ["status"]


@admin.register(StaffServiceAssignment)
class StaffServiceAssignmentAdmin(admin.ModelAdmin):
    list_display = ["staff", "service", "start_date", "end_date"]
    autocomplete_fields = ["staff", "service"]


@admin.register(PatientLoad)
class PatientLoadAdmin(admin.ModelAdmin):
    list_display = ["care_unit", "date", "patient_count", "occupancy_rate"]
    date_hierarchy = "date"


@admin.register(StaffLoan)
class StaffLoanAdmin(admin.ModelAdmin):
    list_display = ["staff", "from_service", "to_service", "start_date", "end_date"]
    autocomplete_fields = ["staff", "from_service", "to_service"]


# ══════════════════════════════════════════════════════════════════════════════
# PERSONNALISATION DU SITE ADMIN
# ══════════════════════════════════════════════════════════════════════════════

admin.site.site_header = "🏥 PlanningRH — Administration"
admin.site.site_title = "PlanningRH Admin"
admin.site.index_title = "Gestion hospitalière"