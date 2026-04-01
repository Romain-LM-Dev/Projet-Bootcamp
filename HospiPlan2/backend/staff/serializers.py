"""Staff app serializers"""
from rest_framework import serializers
from .models import Staff, Role, Specialty, Certification, ContractType, Contract, StaffRole, StaffSpecialty, StaffCertification


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class SpecialtySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Specialty
        fields = '__all__'


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class StaffRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = StaffRole
        fields = '__all__'


class StaffSpecialtySerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = StaffSpecialty
        fields = '__all__'


class StaffCertificationSerializer(serializers.ModelSerializer):
    certification_name = serializers.CharField(source='certification.name', read_only=True)

    class Meta:
        model = StaffCertification
        fields = '__all__'


class ContractTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractType
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    contract_type_name = serializers.CharField(source='contract_type.name', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = '__all__'

    def get_is_active(self, obj):
        from datetime import date
        today = date.today()
        return obj.start_date <= today and (not obj.end_date or obj.end_date >= today)


class StaffSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    specialties = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'employee_id', 'is_active', 'hire_date', 'roles', 'specialties']

    def get_roles(self, obj):
        return [sr.role.name for sr in obj.staff_roles.all()]

    def get_specialties(self, obj):
        return [ss.specialty.name for ss in obj.staff_specialties.all()]


class StaffDetailSerializer(StaffSerializer):
    certifications = StaffCertificationSerializer(many=True, read_only=True)
    contracts = ContractSerializer(many=True, read_only=True)

    class Meta(StaffSerializer.Meta):
        fields = StaffSerializer.Meta.fields + ['certifications', 'contracts']


class StaffWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['first_name', 'last_name', 'email', 'phone', 'employee_id', 'is_active', 'hire_date']