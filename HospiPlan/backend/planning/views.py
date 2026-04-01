"""
views.py — Vues API Django REST Framework
==========================================
Endpoints principaux :
  /api/staff/           GET (list), POST
  /api/staff/<id>/      GET (detail), PUT, PATCH, DELETE
  /api/shifts/          GET, POST
  /api/shifts/<id>/     GET, PUT, PATCH, DELETE
  /api/assignments/     GET, POST  ← appelle les validateurs de contraintes
  /api/assignments/<id>/DELETE
  /api/absences/        GET, POST
  /api/absences/<id>/   GET, DELETE
  /api/certifications/  GET
  /api/contract-types/  GET
  /api/shift-types/     GET
  /api/absence-types/   GET
  /api/services/        GET
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django.db import IntegrityError

from .models import (
    Staff, Shift, ShiftAssignment, Absence, AbsenceType,
    Certification, ContractType, ShiftType, Service,
)
from .serializers import (
    StaffListSerializer, StaffDetailSerializer, StaffWriteSerializer,
    ShiftListSerializer, ShiftWriteSerializer,
    ShiftAssignmentSerializer, ShiftAssignmentCreateSerializer,
    AbsenceSerializer, AbsenceTypeSerializer,
    CertificationSerializer, ContractTypeSerializer, ShiftTypeSerializer,
    ServiceSerializer,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def error(detail, code=None, http_status=status.HTTP_400_BAD_REQUEST):
    payload = {"detail": detail}
    if code:
        payload["code"] = code
    return Response(payload, status=http_status)


# ─── Staff ────────────────────────────────────────────────────────────────────

class StaffListView(APIView):
    """GET /api/staff/  — liste tous les soignants
       POST /api/staff/ — crée un soignant"""

    def get(self, request):
        qs = Staff.objects.prefetch_related(
            "staff_roles__role", "staff_specialties__specialty"
        ).order_by("last_name", "first_name")
        return Response(StaffListSerializer(qs, many=True).data)

    def post(self, request):
        ser = StaffWriteSerializer(data=request.data)
        if ser.is_valid():
            staff = ser.save()
            return Response(StaffDetailSerializer(staff).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetailView(APIView):
    """GET / PUT / PATCH / DELETE /api/staff/<pk>/"""

    def _get(self, pk):
        return get_object_or_404(
            Staff.objects.prefetch_related(
                "staff_roles__role", "staff_specialties__specialty",
                "certifications__certification", "contracts__contract_type",
            ),
            pk=pk,
        )

    def get(self, request, pk):
        return Response(StaffDetailSerializer(self._get(pk)).data)

    def put(self, request, pk):
        staff = self._get(pk)
        ser = StaffWriteSerializer(staff, data=request.data)
        if ser.is_valid():
            return Response(StaffDetailSerializer(ser.save()).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        staff = self._get(pk)
        ser = StaffWriteSerializer(staff, data=request.data, partial=True)
        if ser.is_valid():
            return Response(StaffDetailSerializer(ser.save()).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        staff = self._get(pk)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Shifts (postes de garde) ─────────────────────────────────────────────────

class ShiftListView(APIView):
    def get(self, request):
        qs = Shift.objects.select_related(
            "care_unit__service", "shift_type"
        ).prefetch_related("required_certifications", "assignments").order_by("start_datetime")
        return Response(ShiftListSerializer(qs, many=True).data)

    def post(self, request):
        ser = ShiftWriteSerializer(data=request.data)
        if ser.is_valid():
            shift = ser.save()
            return Response(ShiftListSerializer(shift).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftDetailView(APIView):
    def _get(self, pk):
        return get_object_or_404(
            Shift.objects.select_related("care_unit__service", "shift_type")
                         .prefetch_related("required_certifications", "assignments"),
            pk=pk,
        )

    def get(self, request, pk):
        return Response(ShiftListSerializer(self._get(pk)).data)

    def put(self, request, pk):
        ser = ShiftWriteSerializer(self._get(pk), data=request.data)
        if ser.is_valid():
            return Response(ShiftListSerializer(ser.save()).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        ser = ShiftWriteSerializer(self._get(pk), data=request.data, partial=True)
        if ser.is_valid():
            return Response(ShiftListSerializer(ser.save()).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self._get(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Assignments (affectations) ───────────────────────────────────────────────

class AssignmentListView(APIView):
    """
    GET  /api/assignments/        — liste toutes les affectations
    POST /api/assignments/        — crée une affectation APRÈS validation des contraintes

    En cas de violation de contrainte dure :
      HTTP 409 Conflict  { "code": "C3", "detail": "..." }
    """

    def get(self, request):
        qs = ShiftAssignment.objects.select_related(
            "staff", "shift__care_unit"
        ).order_by("-assigned_at")
        return Response(ShiftAssignmentSerializer(qs, many=True).data)

    def post(self, request):
        ser = ShiftAssignmentCreateSerializer(data=request.data)
        if not ser.is_valid():
            errors = ser.errors
            # Constraint violations → 409
            if "non_field_errors" in errors:
                for e in errors["non_field_errors"]:
                    if isinstance(e, dict) and "constraint" in e:
                        return Response(
                            {"code": e["constraint"], "detail": e["detail"]},
                            status=status.HTTP_409_CONFLICT,
                        )
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment = ser.save()
        except IntegrityError:
            return error("Ce soignant est déjà affecté à ce poste.", http_status=status.HTTP_409_CONFLICT)

        return Response(
            ShiftAssignmentSerializer(
                ShiftAssignment.objects.select_related("staff", "shift__care_unit").get(pk=assignment.pk)
            ).data,
            status=status.HTTP_201_CREATED,
        )


class AssignmentDetailView(APIView):
    """DELETE /api/assignments/<pk>/"""

    def delete(self, request, pk):
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Absences ─────────────────────────────────────────────────────────────────

class AbsenceListView(APIView):
    def get(self, request):
        staff_id = request.query_params.get("staff_id")
        qs = Absence.objects.select_related("staff", "absence_type").order_by("-start_date")
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return Response(AbsenceSerializer(qs, many=True).data)

    def post(self, request):
        ser = AbsenceSerializer(data=request.data)
        if ser.is_valid():
            return Response(AbsenceSerializer(ser.save()).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class AbsenceDetailView(APIView):
    def get(self, request, pk):
        return Response(AbsenceSerializer(get_object_or_404(Absence, pk=pk)).data)

    def delete(self, request, pk):
        get_object_or_404(Absence, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Référentiels (lecture seule) ────────────────────────────────────────────

class CertificationListView(APIView):
    def get(self, request):
        return Response(CertificationSerializer(Certification.objects.all(), many=True).data)


class ContractTypeListView(APIView):
    def get(self, request):
        return Response(ContractTypeSerializer(ContractType.objects.all(), many=True).data)


class ShiftTypeListView(APIView):
    def get(self, request):
        return Response(ShiftTypeSerializer(ShiftType.objects.all(), many=True).data)


class AbsenceTypeListView(APIView):
    def get(self, request):
        return Response(AbsenceTypeSerializer(AbsenceType.objects.all(), many=True).data)


class ServiceListView(APIView):
    def get(self, request):
        qs = Service.objects.prefetch_related("care_units")
        return Response(ServiceSerializer(qs, many=True).data)
