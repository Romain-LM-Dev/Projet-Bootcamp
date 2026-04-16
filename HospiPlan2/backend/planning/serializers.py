"""Planning app serializers"""
from rest_framework import serializers
from .models import Absence, Preference, ShiftAssignment, PlanningSnapshot


class AbsenceSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    absence_type_name = serializers.CharField(source='absence_type.name', read_only=True)

    class Meta:
        model = Absence
        fields = '__all__'


class PreferenceSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Preference
        fields = '__all__'


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    shift_label = serializers.CharField(source='shift.label', read_only=True)
    care_unit_name = serializers.CharField(source='shift.care_unit.name', read_only=True)
    service_name = serializers.CharField(source='shift.care_unit.service.name', read_only=True)
    shift_type_name = serializers.CharField(source='shift.shift_type.name', read_only=True)
    start_datetime = serializers.DateTimeField(source='shift.start_datetime', read_only=True)
    end_datetime = serializers.DateTimeField(source='shift.end_datetime', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    assigned_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = '__all__'


class ShiftAssignmentCreateSerializer(serializers.Serializer):
    staff = serializers.IntegerField()
    shift = serializers.IntegerField()

    def validate(self, attrs):
        from staff.models import Staff
        from shifts.models import Shift

        try:
            staff = Staff.objects.get(pk=attrs['staff'])
            shift = Shift.objects.get(pk=attrs['shift'])
        except Staff.DoesNotExist:
            raise serializers.ValidationError({'staff': 'Membre du personnel introuvable.'})
        except Shift.DoesNotExist:
            raise serializers.ValidationError({'shift': 'Poste introuvable.'})

        if ShiftAssignment.objects.filter(staff=staff, shift=shift).exists():
            raise serializers.ValidationError(
                f'{staff.full_name} est déjà affecté(e) à ce poste.'
            )

        attrs['staff_obj'] = staff
        attrs['shift_obj'] = shift
        return attrs

    def create(self, validated_data):
        return ShiftAssignment.objects.create(
            staff=validated_data['staff_obj'],
            shift=validated_data['shift_obj'],
        )


class PlanningSnapshotSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PlanningSnapshot
        fields = '__all__'