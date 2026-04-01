"""
serializers.py — Django REST Framework
"""
from rest_framework import serializers
from .models import (
    Staff, Role, StaffRole, Specialty, Contract, ContractType,
    Certification, StaffCertification,
    Service, CareUnit, Shift, ShiftType, ShiftAssignment,
    Absence, AbsenceType, Preference,
)


# ── Références légères (pour les listes imbriquées) ──────────────────────────

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "parent"]


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ["id", "name"]


class ContractTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractType
        fields = ["id", "name", "max_hours_per_week", "leave_days_per_year", "night_shift_allowed"]


class ShiftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftType
        fields = ["id", "name", "duration_hours", "requires_rest_after"]


class AbsenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceType
        fields = ["id", "name", "impacts_quota"]


# ── Staff ─────────────────────────────────────────────────────────────────────

class StaffCertificationSerializer(serializers.ModelSerializer):
    certification_name = serializers.CharField(source="certification.name", read_only=True)

    class Meta:
        model = StaffCertification
        fields = ["id", "certification", "certification_name", "obtained_date", "expiration_date"]


class ContractSerializer(serializers.ModelSerializer):
    contract_type_name = serializers.CharField(source="contract_type.name", read_only=True)
    night_shift_allowed = serializers.BooleanField(
        source="contract_type.night_shift_allowed", read_only=True
    )
    max_hours_per_week = serializers.IntegerField(
        source="contract_type.max_hours_per_week", read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id", "contract_type", "contract_type_name",
            "start_date", "end_date", "workload_percent",
            "night_shift_allowed", "max_hours_per_week",
        ]


class StaffListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes."""
    roles = serializers.SerializerMethodField()
    specialties = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            "id", "first_name", "last_name", "email", "phone",
            "is_active", "created_at", "roles", "specialties",
        ]

    def get_roles(self, obj):
        return [sr.role.name for sr in obj.staff_roles.select_related("role").all()]

    def get_specialties(self, obj):
        return [ss.specialty.name for ss in obj.staff_specialties.select_related("specialty").all()]


class StaffDetailSerializer(StaffListSerializer):
    """Serializer détaillé avec contrats et certifications."""
    certifications = StaffCertificationSerializer(many=True, read_only=True)
    active_contract = serializers.SerializerMethodField()

    class Meta(StaffListSerializer.Meta):
        fields = StaffListSerializer.Meta.fields + ["certifications", "active_contract"]

    def get_active_contract(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        contract = obj.contracts.filter(
            start_date__lte=today
        ).order_by("-start_date").first()
        if contract:
            return ContractSerializer(contract).data
        return None


class StaffWriteSerializer(serializers.ModelSerializer):
    """Pour la création / mise à jour."""
    class Meta:
        model = Staff
        fields = ["id", "first_name", "last_name", "email", "phone", "is_active"]


# ── Service / CareUnit ────────────────────────────────────────────────────────

class CareUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareUnit
        fields = ["id", "name", "service"]


class ServiceSerializer(serializers.ModelSerializer):
    care_units = CareUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ["id", "name", "manager", "bed_capacity", "criticality_level", "care_units"]


# ── Shift ─────────────────────────────────────────────────────────────────────

class ShiftListSerializer(serializers.ModelSerializer):
    care_unit_name = serializers.CharField(source="care_unit.name", read_only=True)
    service_name = serializers.CharField(source="care_unit.service.name", read_only=True)
    shift_type_name = serializers.CharField(source="shift_type.name", read_only=True)
    required_certifications = CertificationSerializer(many=True, read_only=True)
    assigned_count = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = [
            "id", "label", "care_unit", "care_unit_name", "service_name",
            "shift_type", "shift_type_name", "start_datetime", "end_datetime",
            "min_staff", "max_staff", "required_certifications", "assigned_count",
        ]

    def get_assigned_count(self, obj):
        return obj.assignments.count()

    def get_label(self, obj):
        return obj.label


class ShiftWriteSerializer(serializers.ModelSerializer):
    required_certification_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Certification.objects.all(),
        write_only=True,
        source="required_certifications",
        required=False,
    )

    class Meta:
        model = Shift
        fields = [
            "id", "care_unit", "shift_type", "start_datetime", "end_datetime",
            "min_staff", "max_staff", "required_certification_ids",
        ]

    def create(self, validated_data):
        certs = validated_data.pop("required_certifications", [])
        shift = super().create(validated_data)
        shift.required_certifications.set(certs)
        return shift

    def update(self, instance, validated_data):
        certs = validated_data.pop("required_certifications", None)
        shift = super().update(instance, validated_data)
        if certs is not None:
            shift.required_certifications.set(certs)
        return shift


# ── ShiftAssignment ───────────────────────────────────────────────────────────

class ShiftAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    shift_label = serializers.SerializerMethodField()

    class Meta:
        model = ShiftAssignment
        fields = ["id", "shift", "staff", "staff_name", "shift_label", "assigned_at"]
        read_only_fields = ["assigned_at"]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"

    def get_shift_label(self, obj):
        return obj.shift.label


class ShiftAssignmentCreateSerializer(serializers.Serializer):
    """Serializer dédié à la création avec validation des contraintes dures."""
    staff_id = serializers.IntegerField()
    shift_id = serializers.IntegerField()

    def validate(self, attrs):
        from .validators import validate_assignment
        try:
            staff = Staff.objects.get(pk=attrs["staff_id"])
            shift = Shift.objects.get(pk=attrs["shift_id"])
        except Staff.DoesNotExist:
            raise serializers.ValidationError({"staff_id": "Soignant introuvable."})
        except Shift.DoesNotExist:
            raise serializers.ValidationError({"shift_id": "Poste introuvable."})

        result = validate_assignment(staff, shift)
        if not result["ok"]:
            raise serializers.ValidationError({
                "constraint": result.get("code", "??"),
                "detail": result.get("detail", "Contrainte violée."),
            })

        attrs["staff"] = staff
        attrs["shift"] = shift
        return attrs

    def create(self, validated_data):
        return ShiftAssignment.objects.create(
            staff=validated_data["staff"],
            shift=validated_data["shift"],
        )


# ── Absence ───────────────────────────────────────────────────────────────────

class AbsenceSerializer(serializers.ModelSerializer):
    absence_type_name = serializers.CharField(source="absence_type.name", read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = Absence
        fields = [
            "id", "staff", "staff_name",
            "absence_type", "absence_type_name",
            "start_date", "expected_end_date", "actual_end_date", "is_planned",
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


# ── Preference ────────────────────────────────────────────────────────────────

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["id", "staff", "type", "description", "is_hard_constraint", "start_date", "end_date"]
