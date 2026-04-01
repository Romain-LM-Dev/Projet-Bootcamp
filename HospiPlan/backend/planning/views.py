"""
views.py — Vues API Django REST Framework
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django.db import IntegrityError
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

from .models import (
    Staff, Shift, ShiftAssignment, Absence, AbsenceType,
    Certification, ContractType, ShiftType, Service,
    Role, Specialty, StaffCertification, Contract,
)
from .optimizer import generate_planning, SoftConstraintPenalty
from .serializers import (
    StaffListSerializer, StaffDetailSerializer, StaffWriteSerializer,
    ShiftListSerializer, ShiftWriteSerializer,
    ShiftAssignmentSerializer, ShiftAssignmentCreateSerializer,
    AbsenceSerializer, AbsenceTypeSerializer,
    CertificationSerializer, ContractTypeSerializer, ShiftTypeSerializer,
    ServiceSerializer,
    RoleSerializer, SpecialtySerializer,
    StaffCertificationWriteSerializer, ContractWriteSerializer,
)


# ─── CSRF cookie ────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def csrf_view(request):
    return JsonResponse({"detail": "CSRF cookie set"})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def error(detail, code=None, http_status=status.HTTP_400_BAD_REQUEST):
    payload = {"detail": detail}
    if code:
        payload["code"] = code
    return Response(payload, status=http_status)


# ─── Staff ───────────────────────────────────────────────────────────────────

class StaffListView(APIView):
    def get(self, request):
        qs = Staff.objects.prefetch_related(
            "staff_roles__role", "staff_specialties__specialty"
        ).order_by("last_name", "first_name")
        return Response(StaffListSerializer(qs, many=True).data)

    def post(self, request):
        ser = StaffWriteSerializer(data=request.data)
        if ser.is_valid():
            staff = ser.save()
            # Recharger avec les prefetch pour le serializer de lecture
            staff = Staff.objects.prefetch_related(
                "staff_roles__role", "staff_specialties__specialty",
                "certifications__certification", "contracts__contract_type",
            ).get(pk=staff.pk)
            return Response(StaffDetailSerializer(staff).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetailView(APIView):
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
            updated = ser.save()
            updated = Staff.objects.prefetch_related(
                "staff_roles__role", "staff_specialties__specialty",
                "certifications__certification", "contracts__contract_type",
            ).get(pk=updated.pk)
            return Response(StaffDetailSerializer(updated).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        staff = self._get(pk)
        ser = StaffWriteSerializer(staff, data=request.data, partial=True)
        if ser.is_valid():
            updated = ser.save()
            updated = Staff.objects.prefetch_related(
                "staff_roles__role", "staff_specialties__specialty",
                "certifications__certification", "contracts__contract_type",
            ).get(pk=updated.pk)
            return Response(StaffDetailSerializer(updated).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self._get(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Rôles ───────────────────────────────────────────────────────────────────

class RoleListView(APIView):
    def get(self, request):
        return Response(RoleSerializer(Role.objects.all(), many=True).data)


# ─── Spécialités ─────────────────────────────────────────────────────────────

class SpecialtyListView(APIView):
    def get(self, request):
        return Response(SpecialtySerializer(Specialty.objects.all(), many=True).data)


# ─── Certifications soignant ────────────────────────────────────────────────

class StaffCertificationListCreateView(APIView):
    def get(self, request):
        qs = StaffCertification.objects.select_related("certification").all()
        staff_id = request.query_params.get("staff")
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return Response(StaffCertificationWriteSerializer(qs, many=True).data)

    def post(self, request):
        ser = StaffCertificationWriteSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            obj = StaffCertification.objects.select_related("certification").get(pk=obj.pk)
            return Response(StaffCertificationWriteSerializer(obj).data,
                            status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffCertificationDetailView(APIView):
    def delete(self, request, pk):
        get_object_or_404(StaffCertification, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Contrats ────────────────────────────────────────────────────────────────

class ContractListCreateView(APIView):
    def get(self, request):
        qs = Contract.objects.select_related("contract_type").all()
        staff_id = request.query_params.get("staff")
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return Response(ContractWriteSerializer(qs, many=True).data)

    def post(self, request):
        ser = ContractWriteSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            obj = Contract.objects.select_related("contract_type").get(pk=obj.pk)
            return Response(ContractWriteSerializer(obj).data,
                            status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractDetailView(APIView):
    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        ser = ContractWriteSerializer(contract, data=request.data, partial=True)
        if ser.is_valid():
            return Response(ContractWriteSerializer(ser.save()).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        get_object_or_404(Contract, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Shifts ──────────────────────────────────────────────────────────────────

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


# ─── Assignments ─────────────────────────────────────────────────────────────

class AssignmentListView(APIView):
    def get(self, request):
        qs = ShiftAssignment.objects.select_related(
            "staff", "shift__care_unit"
        ).order_by("-assigned_at")
        return Response(ShiftAssignmentSerializer(qs, many=True).data)

    def post(self, request):
        ser = ShiftAssignmentCreateSerializer(data=request.data)
        if not ser.is_valid():
            errors = ser.errors
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
            return error("Ce soignant est déjà affecté à ce poste.",
                         http_status=status.HTTP_409_CONFLICT)
        return Response(
            ShiftAssignmentSerializer(
                ShiftAssignment.objects.select_related("staff", "shift__care_unit")
                    .get(pk=assignment.pk)
            ).data,
            status=status.HTTP_201_CREATED,
        )


class AssignmentDetailView(APIView):
    def delete(self, request, pk):
        get_object_or_404(ShiftAssignment, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Absences ────────────────────────────────────────────────────────────────

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


# ─── Génération automatique de planning ───────────────────────────────────────

class PlanningGenerateView(APIView):
    """
    Génère automatiquement un planning pour une période donnée.
    POST /api/plannings/generate/
    
    Body:
    {
        "start_date": "2024-01-15",
        "end_date": "2024-01-21",
        "service_id": 1,          // optionnel
        "care_unit_id": 2,        // optionnel
        "save": true              // par défaut true
    }
    """
    def post(self, request):
        from datetime import date as dt_date
        
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        service_id = request.data.get("service_id")
        care_unit_id = request.data.get("care_unit_id")
        save = request.data.get("save", True)
        
        if not start_date_str or not end_date_str:
            return error("Les dates de début et de fin sont requises.",
                         http_status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return error("Format de date invalide. Utilisez YYYY-MM-DD.",
                         http_status=status.HTTP_400_BAD_REQUEST)
        
        if start_date > end_date:
            return error("La date de début doit être antérieure à la date de fin.",
                         http_status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que service_id ou care_unit_id existe si fourni
        if service_id and not Service.objects.filter(id=service_id).exists():
            return error(f"Service introuvable avec l'id {service_id}.",
                         http_status=status.HTTP_404_NOT_FOUND)
        
        # Lancer la génération
        try:
            result = generate_planning(
                start_date=start_date,
                end_date=end_date,
                service_id=service_id,
                care_unit_id=care_unit_id,
                save=save,
            )
        except Exception as e:
            return error(f"Erreur lors de la génération : {str(e)}",
                         http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Formater la réponse
        assignments_data = []
        for assignment in result["assignments"]:
            assignments_data.append({
                "id": assignment.id if assignment.id else None,
                "staff_id": assignment.staff_id,
                "staff_name": f"{assignment.staff.first_name} {assignment.staff.last_name}",
                "shift_id": assignment.shift_id,
                "shift_label": assignment.shift.label,
                "care_unit": assignment.shift.care_unit.name,
                "service": assignment.shift.care_unit.service.name,
                "start_datetime": assignment.shift.start_datetime.isoformat(),
                "end_datetime": assignment.shift.end_datetime.isoformat(),
            })
        
        uncovered_data = []
        for item in result["uncovered"]:
            shift = item["shift"]
            uncovered_data.append({
                "shift_id": shift.id,
                "shift_label": shift.label,
                "care_unit": shift.care_unit.name,
                "needed": item["needed"],
                "assigned": item["assigned"],
                "reason": item["reason"],
            })
        
        return Response({
            "success": True,
            "period": {
                "start_date": start_date_str,
                "end_date": end_date_str,
            },
            "saved_count": result["saved_count"],
            "total_assignments": len(assignments_data),
            "uncovered_shifts": len(uncovered_data),
            "uncovered": uncovered_data,
            "score": result["score"],
            "score_details": result["score_details"],
            "assignments": assignments_data,
        })


class PlanningScoreView(APIView):
    """
    Calcule le score (pénalités) d'un planning existant.
    GET /api/plannings/score/?start_date=2024-01-15&end_date=2024-01-21&service_id=1
    """
    def get(self, request):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        service_id = request.query_params.get("service_id")
        
        if not start_date_str or not end_date_str:
            return error("Les dates de début et de fin sont requises.",
                         http_status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return error("Format de date invalide. Utilisez YYYY-MM-DD.",
                         http_status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer les données
        shifts = Shift.objects.filter(
            start_datetime__date__gte=start_date,
            start_datetime__date__lte=end_date,
        ).select_related("care_unit__service", "shift_type")
        
        if service_id:
            shifts = shifts.filter(care_unit__service_id=service_id)
        
        shifts = list(shifts)
        
        assignments = ShiftAssignment.objects.filter(
            shift__in=shifts,
        ).select_related("staff", "shift")
        assignments = list(assignments)
        
        staff_list = list(Staff.objects.filter(is_active=True))
        
        # Calculer le score
        penalty_calc = SoftConstraintPenalty(
            shifts=shifts,
            assignments=assignments,
            staff_list=staff_list,
            start_date=start_date,
            end_date=end_date,
        )
        
        score = penalty_calc.total_penalty()
        details = penalty_calc.penalty_details()
        
        return Response({
            "period": {
                "start_date": start_date_str,
                "end_date": end_date_str,
            },
            "total_shifts": len(shifts),
            "total_assignments": len(assignments),
            "score": score,
            "score_details": details,
            "coverage_rate": len(assignments) / len(shifts) * 100 if shifts else 0,
        })
