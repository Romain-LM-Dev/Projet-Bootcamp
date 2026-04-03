"""Optimization app views"""
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
import random

from core.models import Service, CareUnit, ShiftType, Rule
from staff.models import Staff, Contract, StaffRole
from shifts.models import Shift
from planning.models import Absence, ShiftAssignment
from .models import OptimizationRun, OptimizationConfig, OptimizationAlgorithm, OptimizationResult
from .serializers import (
    OptimizationAlgorithmSerializer, OptimizationConfigSerializer,
    OptimizationRunSerializer, OptimizationResultSerializer,
    OptimizationGenerateSerializer
)


class OptimizationAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = OptimizationAlgorithm.objects.filter(is_active=True)
    serializer_class = OptimizationAlgorithmSerializer
    search_fields = ['name']


class OptimizationConfigViewSet(viewsets.ModelViewSet):
    queryset = OptimizationConfig.objects.filter(is_active=True)
    serializer_class = OptimizationConfigSerializer
    search_fields = ['name']


class OptimizationRunViewSet(viewsets.ModelViewSet):
    queryset = OptimizationRun.objects.select_related('config', 'service').all()
    serializer_class = OptimizationRunSerializer
    search_fields = ['name', 'service__name']


class OptimizationResultViewSet(viewsets.ModelViewSet):
    queryset = OptimizationResult.objects.select_related('run', 'staff').all()
    serializer_class = OptimizationResultSerializer
    search_fields = ['staff__first_name', 'staff__last_name']


class GeneratePlanningView(views.APIView):
    """
    Endpoint pour générer un planning automatiquement.
    POST /api/generate/
    """
    def post(self, request):
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        service_id = request.data.get('service_id')

        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create a default config
        config = OptimizationConfig.objects.filter(is_active=True).first()
        if not config:
            algo, _ = OptimizationAlgorithm.objects.get_or_create(
                name='Algorithme Glouton (Défaut)',
                defaults={'algo_type': 'greedy', 'is_active': True}
            )
            config = OptimizationConfig.objects.create(
                name='Configuration par défaut',
                algorithm=algo,
                is_active=True
            )

        # Create optimization run
        run = OptimizationRun.objects.create(
            name=f"Génération auto {start_date} → {end_date}",
            config=config,
            service_id=service_id,
            start_date=start_date,
            end_date=end_date,
            status='running'
        )

        try:
            # Run optimization
            result = self.run_optimization(start_date, end_date, service_id, config, run)
            
            run.status = 'completed'
            run.total_assignments = result['total_assignments']
            run.total_shifts = result['total_shifts']
            run.coverage_rate = result['coverage_rate']
            run.total_score = result['total_score']
            run.completed_at = timezone.now()
            run.save()

            return Response({
                'status': 'success',
                'run_id': run.id,
                'message': f'Planning généré avec succès ! {result["total_assignments"]} affectations créées.',
                'coverage_rate': result['coverage_rate'],
                'total_score': result['total_score'],
                'total_assignments': result['total_assignments'],
                'total_shifts': result['total_shifts']
            }, status=status.HTTP_200_OK)

        except Exception as e:
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = timezone.now()
            run.save()

            return Response({
                'status': 'error',
                'run_id': run.id,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def run_optimization(self, start_date, end_date, service_id, config, run):
        """
        Algorithme glouton avec heuristiques pour générer un planning équitable.
        """
        total_assignments = 0
        total_shifts = 0
        total_required_slots = 0
        total_score = 0

        # Get shifts to fill
        shifts = Shift.objects.filter(
            start_datetime__date__gte=start_date,
            start_datetime__date__lte=end_date,
            is_active=True
        )
        
        if service_id:
            shifts = shifts.filter(care_unit__service_id=service_id)

        # Get active staff
        active_staff = Staff.objects.filter(is_active=True)
        
        # Get existing assignments for workload calculation
        existing_assignments = ShiftAssignment.objects.filter(
            staff__in=active_staff,
            shift__start_datetime__date__gte=start_date,
            shift__start_datetime__date__lte=end_date
        )

        # Calculate current workload per staff
        workload = {}
        for staff in active_staff:
            workload[staff.id] = existing_assignments.filter(staff=staff).count()

        # Get absences in the requested period
        absences = Absence.objects.filter(
            start_date__lte=end_date,
            expected_end_date__gte=start_date
        )

        # Get rules
        max_consecutive_nights = Rule.objects.filter(name='Nuits consécutives max').first()
        max_nights = int(max_consecutive_nights.value) if max_consecutive_nights else 5

        assignments_by_staff = {
            staff.id: list(existing_assignments.filter(staff=staff).select_related('shift', 'shift__shift_type'))
            for staff in active_staff
        }

        for shift in shifts:
            total_shifts += 1
            total_required_slots += max(shift.min_staff, 0)

            # Skip already sufficiently covered shifts
            current_shift_assignments = ShiftAssignment.objects.filter(shift=shift).count()
            remaining_needed = max(shift.min_staff - current_shift_assignments, 0)
            if remaining_needed == 0:
                continue

            # Get eligible staff for this shift
            eligible_staff = self.get_eligible_staff(
                shift, active_staff, workload, absences,
                max_nights, config, assignments_by_staff
            )

            if not eligible_staff:
                continue

            # Sort by workload (least loaded first for equity)
            eligible_staff.sort(key=lambda s: workload.get(s.id, 0))

            # Assign staff to shift
            num_needed = remaining_needed
            assigned = 0

            for staff in eligible_staff:
                if assigned >= num_needed:
                    break
                
                # Create assignment
                assignment = ShiftAssignment.objects.create(
                    staff=staff,
                    shift=shift,
                    status='confirmed',
                    source='auto'
                )
                
                workload[staff.id] = workload.get(staff.id, 0) + 1
                assignments_by_staff.setdefault(staff.id, []).append(assignment)
                total_assignments += 1
                assigned += 1

                # Calculate soft constraint penalties
                penalty = self.calculate_penalty(staff, shift, config, assignments_by_staff)
                total_score += penalty

        coverage_rate = (total_assignments / total_required_slots * 100) if total_required_slots > 0 else 0

        return {
            'total_assignments': total_assignments,
            'total_shifts': total_shifts,
            'coverage_rate': round(coverage_rate, 1),
            'total_score': round(total_score, 2)
        }

    def get_eligible_staff(self, shift, all_staff, workload, absences, max_nights, config, assignments_by_staff):
        """
        Retourne la liste du personnel éligible pour un poste donné.
        """
        eligible = []
        shift_date = shift.start_datetime.date()

        for staff in all_staff:
            staff_assignments = assignments_by_staff.get(staff.id, [])

            # Skip if on absence for the specific shift date
            if absences.filter(
                staff=staff,
                start_date__lte=shift_date,
                expected_end_date__gte=shift_date
            ).exists():
                continue

            # Skip duplicate or overlapping shifts
            if any(
                assignment.shift_id == shift.id or (
                    assignment.shift.start_datetime < shift.end_datetime and
                    assignment.shift.end_datetime > shift.start_datetime
                )
                for assignment in staff_assignments
            ):
                continue

            # Check contract constraints
            try:
                contract = Contract.objects.filter(staff=staff, is_current=True).first()
                if contract:
                    # Check if night shifts allowed
                    if shift.shift_type.requires_rest_after and not contract.contract_type.night_shift_allowed:
                        continue
                    
                    # Check weekly hours limit
                    weekly_assignments = [
                        assignment for assignment in staff_assignments
                        if shift_date - timedelta(days=shift_date.weekday())
                        <= assignment.shift.start_datetime.date()
                        < shift_date + timedelta(days=7 - shift_date.weekday())
                    ]
                    weekly_hours = len(weekly_assignments) * 8

                    if weekly_hours >= contract.contract_type.max_hours_per_week:
                        continue
            except:
                pass

            # Check consecutive night shifts
            if shift.shift_type.requires_rest_after:
                consecutive_nights = self.count_consecutive_nights(staff, shift_date, staff_assignments)
                if consecutive_nights >= max_nights:
                    continue

            eligible.append(staff)

        return eligible

    def count_consecutive_nights(self, staff, target_date, staff_assignments):
        """
        Compte le nombre de nuits consécutives avant une date.
        """
        count = 0
        check_date = target_date - timedelta(days=1)
        
        while check_date >= target_date - timedelta(days=10):
            has_night = any(
                assignment.shift.start_datetime.date() == check_date and assignment.shift.shift_type.requires_rest_after
                for assignment in staff_assignments
            )
            
            if has_night:
                count += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return count

    def calculate_penalty(self, staff, shift, config, assignments_by_staff):
        """
        Calcule la pénalité pour les contraintes molles.
        """
        penalty = 0
        shift_date = shift.start_datetime.date()

        # Pénalité pour nuits consécutives
        staff_assignments = assignments_by_staff.get(staff.id, [])

        if shift.shift_type.requires_rest_after:
            consecutive = self.count_consecutive_nights(staff, shift_date, staff_assignments)
            penalty += consecutive * config.weight_consecutive_nights

        # Pénalité pour déséquilibre de charge
        total_assignments = sum(len(assignments) for assignments in assignments_by_staff.values())
        avg_workload = total_assignments / max(len(assignments_by_staff), 1)
        staff_workload = len(staff_assignments)
        deviation = abs(staff_workload - avg_workload)
        penalty += deviation * config.weight_workload_balance

        return penalty
