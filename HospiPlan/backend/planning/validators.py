"""
validators.py — Contraintes dures d'affectation
=================================================
Chaque fonction lève une ValidationError si la contrainte est violée.
`validate_assignment` les appelle toutes dans l'ordre et renvoie un dict
  { "ok": True }  ou  { "ok": False, "code": "Cx", "detail": "..." }

Appelé depuis la vue avant toute écriture en base.
"""
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


# ── Helpers ───────────────────────────────────────────────────────────────────

def _active_contract(staff, shift_date):
    """Retourne le contrat actif du soignant à la date de la garde, ou None."""
    return staff.contracts.filter(
        start_date__lte=shift_date
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=shift_date)
    ).select_related("contract_type").first()


# On importe models ici pour éviter les imports circulaires
def _get_models():
    from planning import models as m
    return m


# ── C1 — Soignant actif ───────────────────────────────────────────────────────

def check_staff_active(staff):
    if not staff.is_active:
        raise ValidationError({
            "code": "C1",
            "detail": f"{staff.first_name} {staff.last_name} est inactif(ve)."
        })


# ── C2 — Absence déclarée ─────────────────────────────────────────────────────

def check_no_absence(staff, shift):
    m = _get_models()
    shift_date = shift.start_datetime.date()
    absence = m.Absence.objects.filter(
        staff=staff,
        start_date__lte=shift_date,
        expected_end_date__gte=shift_date,
    ).select_related("absence_type").first()
    if absence:
        raise ValidationError({
            "code": "C2",
            "detail": f"{staff.first_name} est absent(e) : {absence.absence_type.name} "
                      f"du {absence.start_date} au {absence.expected_end_date}."
        })


# ── C3 — Certifications requises & non expirées ───────────────────────────────

def check_certifications(staff, shift):
    m = _get_models()
    shift_date = shift.start_datetime.date()
    required_certs = shift.required_certifications.all()

    for cert in required_certs:
        sc = m.StaffCertification.objects.filter(
            staff=staff,
            certification=cert,
        ).first()
        if sc is None:
            raise ValidationError({
                "code": "C3",
                "detail": f"Certification manquante : {cert.name}."
            })
        if sc.expiration_date and sc.expiration_date < shift_date:
            raise ValidationError({
                "code": "C3",
                "detail": f"Certification expirée : {cert.name} "
                          f"(expirée le {sc.expiration_date})."
            })


# ── C4 — Contrat autorise ce type de garde ────────────────────────────────────

def check_contract_allows_shift(staff, shift):
    from django.db import models as dj_models
    m = _get_models()
    shift_date = shift.start_datetime.date()
    contract = staff.contracts.filter(
        start_date__lte=shift_date
    ).filter(
        dj_models.Q(end_date__isnull=True) | dj_models.Q(end_date__gte=shift_date)
    ).select_related("contract_type").first()

    if contract is None:
        raise ValidationError({
            "code": "C4",
            "detail": "Aucun contrat actif trouvé pour ce soignant à cette date."
        })

    if shift.shift_type.requires_rest_after and not contract.contract_type.night_shift_allowed:
        raise ValidationError({
            "code": "C4",
            "detail": f"Le contrat « {contract.contract_type.name} » "
                      f"n'autorise pas les gardes de nuit."
        })
    return contract  # réutilisé par C7


# ── C5 — Chevauchement de plages horaires ────────────────────────────────────

def check_no_overlap(staff, shift):
    m = _get_models()
    overlap = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__start_datetime__lt=shift.end_datetime,
        shift__end_datetime__gt=shift.start_datetime,
    ).select_related("shift").first()
    if overlap:
        raise ValidationError({
            "code": "C5",
            "detail": f"Chevauchement avec le poste « {overlap.shift} » "
                      f"({overlap.shift.start_datetime:%d/%m %H:%M} – "
                      f"{overlap.shift.end_datetime:%H:%M})."
        })


# ── C6 — Repos réglementaire après garde de nuit ─────────────────────────────

def check_rest_after_night(staff, shift):
    m = _get_models()
    rest_hours = getattr(settings, "NIGHT_REST_HOURS", 11)

    # Chercher une garde de nuit précédente dont la fin + repos empiète sur ce début
    night_end_limit = shift.start_datetime - timedelta(hours=rest_hours)
    previous_night = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__shift_type__requires_rest_after=True,
        shift__end_datetime__gt=night_end_limit,
        shift__end_datetime__lte=shift.start_datetime,
    ).select_related("shift").first()

    if previous_night:
        rest_until = previous_night.shift.end_datetime + timedelta(hours=rest_hours)
        raise ValidationError({
            "code": "C6",
            "detail": f"Repos post-garde insuffisant. Après « {previous_night.shift} », "
                      f"le soignant doit se reposer jusqu'au "
                      f"{rest_until:%d/%m/%Y à %H:%M} (min. {rest_hours}h)."
        })


# ── C7 — Quota heures hebdomadaires ──────────────────────────────────────────

def check_weekly_quota(staff, shift, contract=None):
    from django.db import models as dj_models
    m = _get_models()

    if contract is None:
        shift_date = shift.start_datetime.date()
        contract = staff.contracts.filter(
            start_date__lte=shift_date
        ).filter(
            dj_models.Q(end_date__isnull=True) | dj_models.Q(end_date__gte=shift_date)
        ).select_related("contract_type").first()

    if contract is None:
        return  # déjà levé en C4

    max_hours = contract.contract_type.max_hours_per_week

    # Semaine ISO : lundi au dimanche
    shift_date = shift.start_datetime.date()
    week_start = shift_date - timedelta(days=shift_date.weekday())
    week_end = week_start + timedelta(days=6)

    existing = m.ShiftAssignment.objects.filter(
        staff=staff,
        shift__start_datetime__date__gte=week_start,
        shift__start_datetime__date__lte=week_end,
    ).select_related("shift")

    hours_worked = sum(
        (a.shift.end_datetime - a.shift.start_datetime).total_seconds() / 3600
        for a in existing
    )
    new_hours = (shift.end_datetime - shift.start_datetime).total_seconds() / 3600

    if hours_worked + new_hours > max_hours:
        raise ValidationError({
            "code": "C7",
            "detail": f"Quota hebdomadaire dépassé : {hours_worked + new_hours:.1f}h "
                      f"> {max_hours}h contractuelles."
        })


# ── C8 — Contraintes impératives (préférences hard) ──────────────────────────

def check_hard_preferences(staff, shift):
    m = _get_models()
    shift_date = shift.start_datetime.date()
    hard_prefs = m.Preference.objects.filter(
        staff=staff,
        is_hard_constraint=True,
        start_date__lte=shift_date,
        end_date__gte=shift_date,
    )
    if hard_prefs.exists():
        pref = hard_prefs.first()
        raise ValidationError({
            "code": "C8",
            "detail": f"Contrainte impérative du soignant : {pref.description} "
                      f"(du {pref.start_date} au {pref.end_date})."
        })


# ── Point d'entrée principal ──────────────────────────────────────────────────

def validate_assignment(staff, shift):
    """
    Exécute toutes les contraintes dures dans l'ordre.
    Retourne {"ok": True} ou {"ok": False, "code": "Cx", "detail": "..."}.
    """
    checks = [
        lambda: check_staff_active(staff),
        lambda: check_no_absence(staff, shift),
        lambda: check_certifications(staff, shift),
        lambda: check_contract_allows_shift(staff, shift),
        lambda: check_no_overlap(staff, shift),
        lambda: check_rest_after_night(staff, shift),
        lambda: check_weekly_quota(staff, shift),
        lambda: check_hard_preferences(staff, shift),
    ]

    for check in checks:
        try:
            check()
        except ValidationError as exc:
            detail = exc.message if hasattr(exc, "message") else str(exc)
            # exc.message peut être un dict
            if isinstance(exc.message, dict):
                return {"ok": False, **exc.message}
            return {"ok": False, "code": "??", "detail": detail}

    return {"ok": True}
