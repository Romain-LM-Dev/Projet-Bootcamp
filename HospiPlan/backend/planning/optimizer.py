"""
optimizer.py — Génération automatique de planning avec optimisation des contraintes molles
============================================================================================

Algorithmes :
  1. Heuristique gloutonne "moins chargé" (least-loaded) pour construire un premier planning
  2. Recherche locale (swap/échange) pour améliorer la solution
  3. Fonction objectif pondérée combinant toutes les contraintes molles

Contraintes molles minimisées :
  S1 : Éviter plus de N nuits consécutives
  S2 : Respecter les préférences de créneaux (pondérées)
  S3 : Équilibrer la charge entre soignants de même grade (écart-type)
  S4 : Minimiser les changements de service par semaine
  S5 : Équité week-end sur le trimestre
  S6 : Éviter affectation sans période d'adaptation
  S7 : Continuité des soins (mêmes soignants → mêmes patients)
"""

import math
from datetime import timedelta, date
from collections import defaultdict
from django.db.models import Q
from django.utils import timezone
from . import models as m


# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION & RÈGLES MÉTIER
# ──────────────────────────────────────────────────────────────────────────────

def get_rule_value(rule_name, default=None):
    """Récupère une règle F-10 depuis la base (avec cache implicite)."""
    rule = m.Rule.objects.filter(name=rule_name).order_by("-valid_from").first()
    if rule:
        return float(rule.value)
    return default


# Valeurs par défaut des règles
DEFAULT_MAX_CONSECUTIVE_NIGHTS = 3      # S1
DEFAULT_MAX_WEEKEND_SHIFTS_RATIO = 0.3  # S5 : max 30% des week-ends
DEFAULT_ADAPTATION_PERIOD_DAYS = 30     # S6
DEFAULT_CONTINUITY_DAYS = 3             # S7


# ──────────────────────────────────────────────────────────────────────────────
#  FONCTION OBJECTIF — calcul des pénalités
# ──────────────────────────────────────────────────────────────────────────────

class SoftConstraintPenalty:
    """Calcule les pénalités pour chaque contrainte molle."""

    def __init__(self, shifts, assignments, staff_list, start_date, end_date):
        self.shifts = shifts
        self.assignments = assignments
        self.staff_list = staff_list
        self.start_date = start_date
        self.end_date = end_date

        # Indexations pour accès rapide
        self._build_indexes()

    def _build_indexes(self):
        """Construit des index pour accélérer les calculs."""
        # assignment_by_staff[staff_id] = list of assignment
        self.assignment_by_staff = defaultdict(list)
        for a in self.assignments:
            self.assignment_by_staff[a.staff_id].append(a)

        # shift_by_id
        self.shift_by_id = {s.id: s for s in self.shifts}

        # assignments_by_shift[shift_id] = list of staff_ids
        self.assignments_by_shift = defaultdict(list)
        for a in self.assignments:
            self.assignments_by_shift[a.shift_id].append(a.staff_id)

    def penalty_consecutive_nights(self, staff_id):
        """
        S1 : Pénalité pour nuits consécutives excessives.
        """
        staff_assignments = self.assignment_by_staff.get(staff_id, [])
        if not staff_assignments:
            return 0.0

        # Trier par date
        night_shifts = []
        for a in staff_assignments:
            shift = self.shift_by_id[a.shift_id]
            if shift.shift_type.requires_rest_after:
                night_shifts.append(shift.start_datetime.date())

        if not night_shifts:
            return 0.0

        night_shifts.sort()
        max_nights = get_rule_value("max_consecutive_nights", DEFAULT_MAX_CONSECUTIVE_NIGHTS)

        penalty = 0.0
        consecutive = 1
        for i in range(1, len(night_shifts)):
            if (night_shifts[i] - night_shifts[i - 1]).days <= 1:
                consecutive += 1
                if consecutive > max_nights:
                    penalty += (consecutive - max_nights) * 10.0
            else:
                consecutive = 1

        return penalty

    def penalty_preferences(self, staff_id):
        """
        S2 : Pénalité pour non-respect des préférences.
        """
        staff_prefs = m.Preference.objects.filter(
            staff_id=staff_id,
            is_hard_constraint=False,
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=self.end_date),
            Q(end_date__isnull=True) | Q(end_date__gte=self.start_date),
        )

        staff_assignments = self.assignment_by_staff.get(staff_id, [])

        penalty = 0.0
        for pref in staff_prefs:
            desc = pref.description.lower()
            weight = 5.0

            if "[poids=" in desc:
                try:
                    weight = float(desc.split("[poids=")[1].split("]")[0])
                except (ValueError, IndexError):
                    pass

            if "matin" in desc or "jour" in desc:
                for a in staff_assignments:
                    shift = self.shift_by_id[a.shift_id]
                    shift_date = shift.start_datetime.date()
                    if pref.start_date and shift_date < pref.start_date:
                        continue
                    if pref.end_date and shift_date > pref.end_date:
                        continue
                    if shift.shift_type.requires_rest_after:
                        penalty += weight * 3.0
                    elif shift.start_datetime.hour >= 14:
                        penalty += weight * 1.5

            elif "soir" in desc or "nuit" in desc:
                for a in staff_assignments:
                    shift = self.shift_by_id[a.shift_id]
                    shift_date = shift.start_datetime.date()
                    if pref.start_date and shift_date < pref.start_date:
                        continue
                    if pref.end_date and shift_date > pref.end_date:
                        continue
                    if not shift.shift_type.requires_rest_after and shift.start_datetime.hour < 14:
                        penalty += weight * 2.0

            elif "week-end" in desc or "weekend" in desc:
                for a in staff_assignments:
                    shift = self.shift_by_id[a.shift_id]
                    shift_date = shift.start_datetime.date()
                    if shift_date.weekday() >= 5:
                        if "éviter" in desc or "pas" in desc:
                            penalty += weight * 4.0
                    else:
                        if "travailler" in desc or "préfère" in desc:
                            penalty += weight * 1.0

        return penalty

    def penalty_workload_balance(self, service_id=None):
        """
        S3 : Équilibrer la charge entre soignants de même grade/service.
        """
        staff_workload = defaultdict(list)

        for staff in self.staff_list:
            service = None
            if service_id:
                service = service_id
            else:
                ssa = m.StaffServiceAssignment.objects.filter(
                    staff=staff,
                ).filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=self.start_date)
                ).select_related("service").first()
                if ssa:
                    service = ssa.service_id

            if service is None:
                continue

            count = len(self.assignment_by_staff.get(staff.id, []))
            roles = [sr.role.name for sr in staff.staff_roles.all()]

            for role in roles:
                key = (service, role)
                staff_workload[key].append(count)

        total_penalty = 0.0
        for key, workloads in staff_workload.items():
            if len(workloads) < 2:
                continue
            mean = sum(workloads) / len(workloads)
            variance = sum((w - mean) ** 2 for w in workloads) / len(workloads)
            std_dev = math.sqrt(variance)
            total_penalty += std_dev * 5.0

        return total_penalty

    def penalty_service_changes(self, staff_id):
        """
        S4 : Minimiser les changements de service sur une semaine.
        """
        staff_assignments = self.assignment_by_staff.get(staff_id, [])
        if not staff_assignments:
            return 0.0

        week_services = defaultdict(set)
        for a in staff_assignments:
            shift = self.shift_by_id[a.shift_id]
            shift_date = shift.start_datetime.date()
            week_num = shift_date.isocalendar()[1]
            service_id = shift.care_unit.service_id
            week_services[week_num].add(service_id)

        penalty = 0.0
        for week_num, services in week_services.items():
            if len(services) > 1:
                penalty += (len(services) - 1) * 3.0

        return penalty

    def penalty_weekend_equity(self, staff_id):
        """
        S5 : Équité des gardes de week-end sur le trimestre.
        """
        staff_assignments = self.assignment_by_staff.get(staff_id, [])
        if not staff_assignments:
            return 0.0

        weekend_count = 0
        total_shifts = len(staff_assignments)

        for a in staff_assignments:
            shift = self.shift_by_id[a.shift_id]
            shift_date = shift.start_datetime.date()
            if shift_date.weekday() >= 5:
                weekend_count += 1

        if total_shifts == 0:
            return 0.0

        ratio = weekend_count / total_shifts
        max_ratio = get_rule_value("max_weekend_ratio", DEFAULT_MAX_WEEKEND_SHIFTS_RATIO)

        if ratio > max_ratio:
            return (ratio - max_ratio) * 20.0
        return 0.0

    def penalty_adaptation_period(self, staff_id):
        """
        S6 : Éviter d'affecter un soignant à un service inconnu sans adaptation.
        """
        staff_assignments = self.assignment_by_staff.get(staff_id, [])
        if not staff_assignments:
            return 0.0

        known_services = set()
        historical = m.ShiftAssignment.objects.filter(
            staff_id=staff_id,
            shift__start_datetime__date__lt=self.start_date,
        ).select_related("shift__care_unit__service")

        for ha in historical:
            known_services.add(ha.shift.care_unit.service_id)

        penalty = 0.0
        for a in staff_assignments:
            shift = self.shift_by_id[a.shift_id]
            service_id = shift.care_unit.service_id

            if service_id not in known_services:
                adaptation_days = get_rule_value("adaptation_period_days", DEFAULT_ADAPTATION_PERIOD_DAYS)

                ssa = m.StaffServiceAssignment.objects.filter(
                    staff_id=staff_id,
                    service_id=service_id,
                ).order_by("-start_date").first()

                if ssa:
                    days_in_service = (self.end_date - ssa.start_date).days
                    if days_in_service < adaptation_days:
                        penalty += 8.0
                else:
                    penalty += 15.0

        return penalty

    def penalty_continuity(self):
        """
        S7 : Continuité des soins.
        """
        penalty = 0.0

        service_staff_days = defaultdict(lambda: defaultdict(set))

        for a in self.assignments:
            shift = self.shift_by_id[a.shift_id]
            shift_date = shift.start_datetime.date()
            service_id = shift.care_unit.service_id
            service_staff_days[service_id][shift_date].add(a.staff_id)

        for service_id, day_staff in service_staff_days.items():
            dates = sorted(day_staff.keys())
            if len(dates) < 2:
                continue

            for i in range(1, len(dates)):
                if (dates[i] - dates[i-1]).days <= 2:
                    prev_staff = day_staff[dates[i-1]]
                    curr_staff = day_staff[dates[i]]
                    continuity = len(prev_staff & curr_staff)
                    max_possible = max(len(prev_staff), len(curr_staff))
                    if max_possible > 0:
                        continuity_ratio = continuity / max_possible
                        if continuity_ratio < 0.5:
                            penalty += (1 - continuity_ratio) * 2.0

        return penalty

    def total_penalty(self):
        """Calcule la pénalité totale (fonction objectif à minimiser)."""
        total = 0.0

        for staff in self.staff_list:
            total += self.penalty_consecutive_nights(staff.id) * 1.5
            total += self.penalty_preferences(staff.id) * 1.0
            total += self.penalty_service_changes(staff.id) * 1.0
            total += self.penalty_weekend_equity(staff.id) * 0.8
            total += self.penalty_adaptation_period(staff.id) * 1.2

        total += self.penalty_workload_balance() * 2.0
        total += self.penalty_continuity() * 1.5

        return total

    def penalty_details(self):
        """Retourne le détail des pénalités par contrainte."""
        details = {
            "consecutive_nights": 0.0,
            "preferences": 0.0,
            "workload_balance": self.penalty_workload_balance(),
            "service_changes": 0.0,
            "weekend_equity": 0.0,
            "adaptation_period": 0.0,
            "continuity": self.penalty_continuity(),
        }

        for staff in self.staff_list:
            details["consecutive_nights"] += self.penalty_consecutive_nights(staff.id) * 1.5
            details["preferences"] += self.penalty_preferences(staff.id) * 1.0
            details["service_changes"] += self.penalty_service_changes(staff.id) * 1.0
            details["weekend_equity"] += self.penalty_weekend_equity(staff.id) * 0.8
            details["adaptation_period"] += self.penalty_adaptation_period(staff.id) * 1.2

        return details


# ──────────────────────────────────────────────────────────────────────────────
#  VÉRIFICATEUR DE CONTRAINTES DURES (version optimiseur)
# ──────────────────────────────────────────────────────────────────────────────

def check_hard_constraints(staff, shift, existing_assignments=None):
    """
    Vérifie si une affectation est légale (contraintes dures).
    """
    from .validators import validate_assignment

    result = validate_assignment(staff, shift)
    return result["ok"], result.get("code"), result.get("detail")


def check_hard_constraints_batch(staff, shift, tentative_assignments):
    """
    Vérifie les contraintes dures en tenant compte des affectations
    déjà faites dans la génération en cours.
    """
    # C1 — Soignant actif
    if not staff.is_active:
        return False, "C1", "Soignant inactif"

    # C2 — Absence
    shift_date = shift.start_datetime.date()
    absence = m.Absence.objects.filter(
        staff=staff,
        start_date__lte=shift_date,
        expected_end_date__gte=shift_date,
    ).first()
    if absence:
        return False, "C2", f"Absent du {absence.start_date} au {absence.expected_end_date}"

    # C3 — Certifications
    required_certs = shift.required_certifications.all()
    for cert in required_certs:
        has_cert = m.StaffCertification.objects.filter(
            staff=staff, certification=cert
        ).first()
        if not has_cert:
            return False, "C3", f"Certification manquante : {cert.name}"
        if has_cert.expiration_date and has_cert.expiration_date < shift_date:
            return False, "C3", f"Certification expirée : {cert.name}"

    # C4 — Contrat autorise nuit
    contract = m.Contract.objects.filter(
        staff=staff,
        start_date__lte=shift_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=shift_date)
    ).select_related("contract_type").first()

    if not contract:
        return False, "C4", "Aucun contrat actif"

    if shift.shift_type.requires_rest_after and not contract.contract_type.night_shift_allowed:
        return False, "C4", "Nuit non autorisée par contrat"

    # C5 — Chevauchement (inclure tentative_assignments)
    for ta in tentative_assignments:
        if ta.staff_id != staff.id:
            continue
        ta_shift = ta.shift
        if ta_shift.start_datetime < shift.end_datetime and ta_shift.end_datetime > shift.start_datetime:
            return False, "C5", "Chevauchement avec affectation en cours"

    # Vérifier aussi en base
    overlap = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__start_datetime__lt=shift.end_datetime,
        shift__end_datetime__gt=shift.start_datetime,
    ).first()
    if overlap:
        return False, "C5", "Chevauchement avec affectation existante"

    # C6 — Repos post-nuit
    rest_hours = 11
    night_end_limit = shift.start_datetime - timedelta(hours=rest_hours)

    # En base
    previous_night = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__shift_type__requires_rest_after=True,
        shift__end_datetime__gt=night_end_limit,
        shift__end_datetime__lte=shift.start_datetime,
    ).first()
    if previous_night:
        return False, "C6", "Repos post-garde insuffisant"

    # Dans les tentative_assignments
    for ta in tentative_assignments:
        if ta.staff_id != staff.id:
            continue
        if ta.shift.shift_type.requires_rest_after:
            if ta.shift.end_datetime > night_end_limit and ta.shift.end_datetime <= shift.start_datetime:
                return False, "C6", "Repos post-garde insuffisant (tentative)"

    # C7 — Quota heures hebdo
    week_start = shift_date - timedelta(days=shift_date.weekday())
    week_end = week_start + timedelta(days=6)

    existing = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__start_datetime__date__gte=week_start,
        shift__start_datetime__date__lte=week_end,
    )
    tentative_week = [ta for ta in tentative_assignments
                      if ta.staff_id == staff.id
                      and week_start <= ta.shift.start_datetime.date() <= week_end]

    hours_worked = sum(
        (a.shift.end_datetime - a.shift.start_datetime).total_seconds() / 3600
        for a in existing
    )
    hours_worked += sum(
        (ta.shift.end_datetime - ta.shift.start_datetime).total_seconds() / 3600
        for ta in tentative_week
    )

    new_hours = (shift.end_datetime - shift.start_datetime).total_seconds() / 3600
    max_hours = contract.contract_type.max_hours_per_week

    if hours_worked + new_hours > max_hours:
        return False, "C7", f"Quota hebdo dépassé : {hours_worked + new_hours:.1f}h/{max_hours}h"

    # C8 — Préférences hard
    hard_prefs = m.Preference.objects.filter(
        staff=staff,
        is_hard_constraint=True,
        start_date__lte=shift_date,
        end_date__gte=shift_date,
    ).first()
    if hard_prefs:
        return False, "C8", f"Contrainte impérative : {hard_prefs.description}"

    return True, None, None


# ──────────────────────────────────────────────────────────────────────────────
#  GÉNÉRATEUR DE PLANNING — Heuristique gloutonne + recherche locale
# ──────────────────────────────────────────────────────────────────────────────

class PlanningGenerator:
    """
    Génère un planning automatique en respectant les contraintes dures
    et en minimisant les contraintes molles.
    """

    def __init__(self, start_date, end_date, service_id=None, care_unit_id=None):
        self.start_date = start_date
        self.end_date = end_date
        self.service_id = service_id
        self.care_unit_id = care_unit_id

        self.generated_assignments = []
        self.uncovered_shifts = []
        self.score = 0.0
        self.score_details = {}

    def _get_shifts(self):
        """Récupère les shifts à couvrir."""
        qs = m.Shift.objects.filter(
            start_datetime__date__gte=self.start_date,
            start_datetime__date__lte=self.end_date,
        ).select_related("care_unit__service", "shift_type").prefetch_related(
            "required_certifications", "assignments"
        )

        if self.care_unit_id:
            qs = qs.filter(care_unit_id=self.care_unit_id)
        elif self.service_id:
            qs = qs.filter(care_unit__service_id=self.service_id)

        return list(qs.order_by("start_datetime"))

    def _get_staff(self):
        """Récupère les soignants disponibles."""
        qs = m.Staff.objects.filter(is_active=True).prefetch_related(
            "staff_roles__role",
            "staff_specialties__specialty",
            "certifications__certification",
            "contracts__contract_type",
        )
        return list(qs)

    def _score_candidate(self, staff, shift, tentative_assignments):
        """
        Score d'un soignant pour un shift donné.
        Plus le score est bas, meilleur est le candidat.
        """
        ok, code, detail = check_hard_constraints_batch(staff, shift, tentative_assignments)
        if not ok:
            return float('inf'), f"Contrainte dure {code}: {detail}"

        score = 0.0

        # S1 : Nuits consécutives
        consecutive_nights = self._count_consecutive_nights(staff, shift, tentative_assignments)
        max_nights = get_rule_value("max_consecutive_nights", DEFAULT_MAX_CONSECUTIVE_NIGHTS)
        if consecutive_nights >= max_nights:
            score += 50.0
        elif consecutive_nights == max_nights - 1:
            score += 20.0

        # S3 : Équilibrage charge
        current_load = self._get_staff_load(staff, tentative_assignments)
        avg_load = self._get_avg_load_for_service(shift.care_unit.service_id, tentative_assignments)
        if current_load > avg_load + 2:
            score += 10.0
        elif current_load < avg_load - 1:
            score -= 5.0

        # S4 : Changements de service
        service_changes = self._count_service_changes(staff, shift, tentative_assignments)
        score += service_changes * 3.0

        # S5 : Week-end équité
        weekend_ratio = self._get_weekend_ratio(staff, tentative_assignments)
        max_ratio = get_rule_value("max_weekend_ratio", DEFAULT_MAX_WEEKEND_SHIFTS_RATIO)
        if weekend_ratio > max_ratio:
            score += 15.0

        # S6 : Adaptation
        if not self._is_known_service(staff, shift.care_unit.service_id):
            score += 12.0

        # S2 : Préférences
        pref_penalty = self._check_preference_match(staff, shift)
        score += pref_penalty

        # S7 : Continuité
        continuity_bonus = self._check_continuity(staff, shift, tentative_assignments)
        score -= continuity_bonus * 3.0

        return score, "OK"

    def _count_consecutive_nights(self, staff, shift, tentative_assignments):
        """Compte les nuits consécutives incluant ce shift."""
        shift_date = shift.start_datetime.date()
        nights = set()

        # En base
        past_nights = m.ShiftAssignment.objects.filter(
            staff=staff,
            shift__shift_type__requires_rest_after=True,
            shift__start_datetime__date__lt=shift_date,
        ).select_related("shift")
        for a in past_nights:
            nights.add(a.shift.start_datetime.date())

        # Tentative
        for ta in tentative_assignments:
            if ta.staff_id == staff.id and ta.shift.shift_type.requires_rest_after:
                nights.add(ta.shift.start_datetime.date())

        if shift.shift_type.requires_rest_after:
            nights.add(shift_date)

        if not nights:
            return 0

        nights_list = sorted(nights)
        consecutive = 1
        for i in range(len(nights_list) - 2, -1, -1):
            if (nights_list[i + 1] - nights_list[i]).days <= 1:
                consecutive += 1
            else:
                break

        return consecutive

    def _get_staff_load(self, staff, tentative_assignments):
        """Nombre de gardes déjà assignées au soignant sur la période."""
        count = m.ShiftAssignment.objects.filter(
            staff=staff,
            shift__start_datetime__date__gte=self.start_date,
            shift__start_datetime__date__lte=self.end_date,
        ).count()

        for ta in tentative_assignments:
            if ta.staff_id == staff.id:
                count += 1

        return count

    def _get_avg_load_for_service(self, service_id, tentative_assignments):
        """Charge moyenne des soignants pour ce service."""
        staff_ids = set()
        ssas = m.StaffServiceAssignment.objects.filter(
            service_id=service_id,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=self.start_date),
        ).values_list("staff_id", flat=True)
        staff_ids.update(ssas)

        if not staff_ids:
            return 0

        total_load = 0
        for staff_id in staff_ids:
            load = self._get_staff_load(m.Staff.objects.get(id=staff_id), tentative_assignments)
            total_load += load

        return total_load / len(staff_ids)

    def _count_service_changes(self, staff, shift, tentative_assignments, target_shift=None):
        """Compte le nombre de services différents sur la semaine."""
        if target_shift is None:
            target_shift = shift

        target_date = target_shift.start_datetime.date()
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)

        services = set()

        # Shifts en base
        existing = m.ShiftAssignment.objects.filter(
            staff=staff,
            shift__start_datetime__date__gte=week_start,
            shift__start_datetime__date__lte=week_end,
        ).select_related("shift__care_unit__service")
        for a in existing:
            services.add(a.shift.care_unit.service_id)

        # Tentative
        for ta in tentative_assignments:
            if ta.staff_id == staff.id:
                ta_date = ta.shift.start_datetime.date()
                if week_start <= ta_date <= week_end:
                    services.add(ta.shift.care_unit.service_id)

        services.add(shift.care_unit.service_id)

        return max(0, len(services) - 1)

    def _get_weekend_ratio(self, staff, tentative_assignments):
        """Ratio de gardes de week-end."""
        total = 0
        weekend = 0

        # Base
        existing = m.ShiftAssignment.objects.filter(
            staff=staff,
            shift__start_datetime__date__gte=self.start_date,
            shift__start_datetime__date__lte=self.end_date,
        ).select_related("shift")
        for a in existing:
            total += 1
            if a.shift.start_datetime.date().weekday() >= 5:
                weekend += 1

        # Tentative
        for ta in tentative_assignments:
            if ta.staff_id == staff.id:
                total += 1
                if ta.shift.start_datetime.date().weekday() >= 5:
                    weekend += 1

        if total == 0:
            return 0.0
        return weekend / total

    def _is_known_service(self, staff, service_id):
        """Vérifie si le soignant a déjà travaillé dans ce service."""
        historical = m.ShiftAssignment.objects.filter(
            staff=staff,
            shift__start_datetime__date__lt=self.start_date,
            shift__care_unit__service_id=service_id,
        ).exists()

        if historical:
            return True

        current = m.StaffServiceAssignment.objects.filter(
            staff=staff,
            service_id=service_id,
        ).exists()

        return current

    def _check_preference_match(self, staff, shift):
        """Vérifie si le shift correspond aux préférences du soignant."""
        penalty = 0.0
        shift_date = shift.start_datetime.date()
        shift_hour = shift.start_datetime.hour

        prefs = m.Preference.objects.filter(
            staff=staff,
            is_hard_constraint=False,
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=shift_date),
            Q(end_date__isnull=True) | Q(end_date__gte=shift_date),
        )

        for pref in prefs:
            desc = pref.description.lower()
            weight = 3.0

            if "[poids=" in desc:
                try:
                    weight = float(desc.split("[poids=")[1].split("]")[0])
                except (ValueError, IndexError):
                    pass

            if "matin" in desc or "jour" in desc:
                if shift.shift_type.requires_rest_after:
                    penalty += weight * 2.0
                elif shift_hour >= 14:
                    penalty += weight * 1.0

            elif "soir" in desc or "nuit" in desc:
                if not shift.shift_type.requires_rest_after and shift_hour < 14:
                    penalty += weight * 1.5

            elif "week-end" in desc or "weekend" in desc:
                if shift_date.weekday() >= 5:
                    if "éviter" in desc or "pas" in desc:
                        penalty += weight * 3.0
                else:
                    if "travailler" in desc:
                        penalty += weight * 0.5

        return penalty

    def _check_continuity(self, staff, shift, tentative_assignments):
        """Vérifie si affecter ce soignant améliore la continuité."""
        shift_date = shift.start_datetime.date()
        service_id = shift.care_unit.service_id

        nearby_dates = [
            shift_date - timedelta(days=1),
            shift_date + timedelta(days=1),
        ]

        continuity_score = 0.0
        count = 0

        for d in nearby_dates:
            # Base
            existing = m.ShiftAssignment.objects.filter(
                staff=staff,
                shift__start_datetime__date=d,
                shift__care_unit__service_id=service_id,
            ).exists()

            if existing:
                continuity_score += 1.0
                count += 1

            # Tentative
            for ta in tentative_assignments:
                if ta.staff_id == staff.id and ta.shift.start_datetime.date() == d:
                    if ta.shift.care_unit.service_id == service_id:
                        continuity_score += 1.0
                        count += 1
                        break

        if count > 0:
            return continuity_score / count
        return 0.0

    def _sort_shifts_by_priority(self, shifts):
        """Trie les shifts par ordre de priorité (les plus difficiles en premier)."""
        def shift_priority(shift):
            # Plus le score est BAS, plus le shift est prioritaire (tri croissant)
            score = 0

            # Nuits en premier (score bas = haute priorité)
            if shift.shift_type.requires_rest_after:
                score -= 100

            # Week-ends ensuite
            if shift.start_datetime.date().weekday() >= 5:
                score -= 50

            # Moins il y a de certifications requises, plus c'est facile à pourvoir
            # Donc on augmente le score (baisse la priorité)
            required_certs = len(list(shift.required_certifications.all()))
            score += required_certs * 5

            return score

        return sorted(shifts, key=shift_priority)

    def generate_greedy(self):
        """Phase 1 : Algorithme glouton."""
        shifts = self._get_shifts()
        staff_list = self._get_staff()
        tentative_assignments = []

        shifts = self._sort_shifts_by_priority(shifts)

        for shift in shifts:
            # Besoin en personnel
            current_assignments = [a for a in tentative_assignments if a.shift_id == shift.id]
            existing_db = shift.assignments.count()
            total_assigned = len(current_assignments) + existing_db
            needed = shift.min_staff - total_assigned

            if needed <= 0:
                continue

            # Trouver les meilleurs candidats
            candidates = []
            for staff in staff_list:
                score, reason = self._score_candidate(staff, shift, tentative_assignments)
                if score < float('inf'):
                    candidates.append((staff, score, reason))

            candidates.sort(key=lambda x: x[1])

            # Prendre les 'needed' meilleurs
            assigned_count = 0
            for staff, score, reason in candidates:
                if assigned_count >= needed:
                    break
                if assigned_count >= shift.max_staff:
                    break

                assignment = m.ShiftAssignment(staff=staff, shift=shift)
                tentative_assignments.append(assignment)
                self.generated_assignments.append(assignment)
                assigned_count += 1

            if assigned_count < needed:
                self.uncovered_shifts.append({
                    "shift": shift,
                    "needed": needed,
                    "assigned": assigned_count,
                    "reason": candidates[0][2] if candidates else "Aucun candidat valide"
                })

        return self.generated_assignments

    def improve_local_search(self, max_iterations=50):
        """Phase 2 : Recherche locale par échanges (swap)."""
        if not self.generated_assignments:
            return

        for iteration in range(max_iterations):
            improved = False

            for i in range(len(self.generated_assignments)):
                for j in range(i + 1, len(self.generated_assignments)):
                    a1 = self.generated_assignments[i]
                    a2 = self.generated_assignments[j]

                    if a1.shift_id != a2.shift_id:
                        if (a1.shift.start_datetime.date() != a2.shift.start_datetime.date() or
                            a1.shift.shift_type_id != a2.shift.shift_type_id):
                            continue

                    # Essayer le swap
                    new_a1 = m.ShiftAssignment(staff=a2.staff, shift=a1.shift)
                    new_a2 = m.ShiftAssignment(staff=a1.staff, shift=a2.shift)

                    tentative = [a for a in self.generated_assignments if a != a1 and a != a2]

                    ok1, _, _ = check_hard_constraints_batch(a2.staff, a1.shift, tentative)
                    ok2, _, _ = check_hard_constraints_batch(a1.staff, a2.shift, tentative)

                    if not ok1 or not ok2:
                        continue

                    all_assignments_before = self.generated_assignments
                    all_assignments_after = tentative + [new_a1, new_a2]

                    penalty_before = self._quick_penalty(all_assignments_before)
                    penalty_after = self._quick_penalty(all_assignments_after)

                    if penalty_after < penalty_before - 0.5:
                        self.generated_assignments = all_assignments_after
                        improved = True

            if not improved:
                break

    def _quick_penalty(self, assignments):
        """Calcul rapide de pénalité pour la recherche locale."""
        penalty = 0.0

        staff_assignments = defaultdict(list)
        for a in assignments:
            staff_assignments[a.staff_id].append(a)

        for staff_id, staff_assigns in staff_assignments.items():
            nights = []
            for a in staff_assigns:
                if a.shift.shift_type.requires_rest_after:
                    nights.append(a.shift.start_datetime.date())
            nights.sort()
            if len(nights) >= 2:
                consecutive = 1
                for i in range(1, len(nights)):
                    if (nights[i] - nights[i-1]).days <= 1:
                        consecutive += 1
                        if consecutive > 3:
                            penalty += 10.0
                    else:
                        consecutive = 1

        return penalty

    def save_assignments(self):
        """Sauvegarde les affectations générées en base."""
        saved = []
        for assignment in self.generated_assignments:
            ok, code, detail = check_hard_constraints(assignment.staff, assignment.shift)
            if not ok:
                continue

            try:
                assignment.save()
                saved.append(assignment)
            except Exception:
                pass

        return saved

    def run(self):
        """Exécute la génération complète."""
        self.generate_greedy()
        self.improve_local_search()

        all_staff = self._get_staff()
        all_shifts = self._get_shifts()

        penalty_calc = SoftConstraintPenalty(
            shifts=all_shifts,
            assignments=self.generated_assignments,
            staff_list=all_staff,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.score = penalty_calc.total_penalty()
        self.score_details = penalty_calc.penalty_details()

        return {
            "assignments": self.generated_assignments,
            "uncovered": self.uncovered_shifts,
            "score": self.score,
            "score_details": self.score_details,
        }


# ──────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

def generate_planning(start_date, end_date, service_id=None, care_unit_id=None, save=True):
    """
    Génère automatiquement un planning pour la période donnée.

    Args:
        start_date: date de début (inclusive)
        end_date: date de fin (inclusive)
        service_id: optionnel, restreint au service donné
        care_unit_id: optionnel, restreint à l'unité de soin donnée
        save: si True, sauvegarde en base de données

    Returns:
        dict avec:
            - assignments: liste des affectations créées
            - uncovered: liste des shifts non couverts
            - score: score global (pénalité totale)
            - score_details: détail par contrainte molle
            - saved_count: nombre d'affectations sauvegardées
    """
    generator = PlanningGenerator(
        start_date=start_date,
        end_date=end_date,
        service_id=service_id,
        care_unit_id=care_unit_id,
    )

    result = generator.run()

    if save:
        saved = generator.save_assignments()
        result["saved_count"] = len(saved)
    else:
        result["saved_count"] = 0

    return result