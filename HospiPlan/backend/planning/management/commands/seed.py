from django.core.management.base import BaseCommand
from planning.models import (
    Staff, Role, StaffRole, Specialty, StaffSpecialty,
    ContractType, Contract, Certification, StaffCertification,
    Service, CareUnit, ShiftType, Shift, ShiftRequiredCertification,
    AbsenceType, Absence,
)
from django.utils import timezone
from datetime import date, timedelta

class Command(BaseCommand):
    help = "Alimente la base avec des données de test"

    def handle(self, *args, **kwargs):

        # ── Rôles ──────────────────────────────────────────────────
        role_inf  = Role.objects.get_or_create(name="Infirmière")[0]
        role_med  = Role.objects.get_or_create(name="Médecin")[0]
        role_aide = Role.objects.get_or_create(name="Aide-soignant")[0]

        # ── Spécialités ────────────────────────────────────────────
        sp_urg  = Specialty.objects.get_or_create(name="Urgences")[0]
        sp_chir = Specialty.objects.get_or_create(name="Chirurgie")[0]
        sp_ped  = Specialty.objects.get_or_create(name="Pédiatrie")[0]
        sp_ger  = Specialty.objects.get_or_create(name="Gériatrie")[0]

        # ── Types de contrat ───────────────────────────────────────
        cdi = ContractType.objects.get_or_create(
            name="CDI",
            defaults={"max_hours_per_week": 35, "leave_days_per_year": 25, "night_shift_allowed": True}
        )[0]
        cdd = ContractType.objects.get_or_create(
            name="CDD",
            defaults={"max_hours_per_week": 35, "leave_days_per_year": 20, "night_shift_allowed": False}
        )[0]
        stage = ContractType.objects.get_or_create(
            name="Stagiaire",
            defaults={"max_hours_per_week": 24, "leave_days_per_year": 0, "night_shift_allowed": False}
        )[0]

        # ── Certifications ─────────────────────────────────────────
        bls  = Certification.objects.get_or_create(name="BLS — Basic Life Support")[0]
        acls = Certification.objects.get_or_create(name="ACLS — Advanced Cardiac Life Support")[0]
        ped  = Certification.objects.get_or_create(name="Pédiatrie avancée")[0]
        si   = Certification.objects.get_or_create(name="Soins intensifs")[0]

        # ── Services & unités de soins ─────────────────────────────
        svc_urg  = Service.objects.get_or_create(name="Urgences",  defaults={"bed_capacity": 20, "criticality_level": 3})[0]
        svc_chir = Service.objects.get_or_create(name="Chirurgie", defaults={"bed_capacity": 30, "criticality_level": 2})[0]
        svc_ped  = Service.objects.get_or_create(name="Pédiatrie", defaults={"bed_capacity": 15, "criticality_level": 2})[0]

        cu_urg  = CareUnit.objects.get_or_create(name="Urgences",  service=svc_urg)[0]
        cu_chir = CareUnit.objects.get_or_create(name="Chirurgie", service=svc_chir)[0]
        cu_ped  = CareUnit.objects.get_or_create(name="Pédiatrie", service=svc_ped)[0]

        # ── Types de gardes ────────────────────────────────────────
        t_jour = ShiftType.objects.get_or_create(name="Jour",  defaults={"duration_hours": 12, "requires_rest_after": False})[0]
        t_nuit = ShiftType.objects.get_or_create(name="Nuit",  defaults={"duration_hours": 12, "requires_rest_after": True})[0]

        # ── Soignants ──────────────────────────────────────────────
        soignants = [
            ("Amina",   "Benali",      "a.benali@hopital.ma",     role_inf,  sp_urg,  cdi,  True),
            ("Youssef", "Chakir",      "y.chakir@hopital.ma",     role_med,  sp_chir, cdi,  True),
            ("Fatima",  "El Mansouri", "f.elmansouri@hopital.ma", role_inf,  sp_ped,  cdd,  True),
            ("Karim",   "Tazi",        "k.tazi@hopital.ma",       role_aide, sp_ger,  stage,False),
            ("Nadia",   "Ouali",       "n.ouali@hopital.ma",      role_med,  sp_urg,  cdi,  True),
        ]

        staff_objs = {}
        for prenom, nom, email, role, spec, contrat_type, actif in soignants:
            s, _ = Staff.objects.get_or_create(
                email=email,
                defaults={"first_name": prenom, "last_name": nom, "is_active": actif}
            )
            StaffRole.objects.get_or_create(staff=s, role=role)
            StaffSpecialty.objects.get_or_create(staff=s, specialty=spec)
            Contract.objects.get_or_create(
                staff=s,
                contract_type=contrat_type,
                defaults={"start_date": date(2024, 1, 1), "workload_percent": 100}
            )
            staff_objs[email] = s

        amina   = staff_objs["a.benali@hopital.ma"]
        youssef = staff_objs["y.chakir@hopital.ma"]
        fatima  = staff_objs["f.elmansouri@hopital.ma"]
        nadia   = staff_objs["n.ouali@hopital.ma"]

        # ── Certifications des soignants ───────────────────────────
        today = date.today()
        certs = [
            (amina,   bls,  date(2026, 12, 31)),
            (amina,   acls, date(2025, 6, 30)),   # expirée — pour tester C3
            (youssef, bls,  date(2027, 1, 1)),
            (youssef, acls, date(2027, 1, 1)),
            (youssef, si,   date(2027, 6, 1)),
            (fatima,  bls,  date(2026, 8, 1)),
            (fatima,  ped,  date(2026, 11, 1)),
            (nadia,   bls,  date(2026, 9, 1)),
            (nadia,   acls, date(2027, 3, 1)),
        ]
        for staff, cert, exp in certs:
            StaffCertification.objects.get_or_create(
                staff=staff, certification=cert,
                defaults={"obtained_date": date(2023, 1, 1), "expiration_date": exp}
            )

        # ── Postes de garde (cette semaine) ────────────────────────
        from datetime import datetime
        base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        shifts_data = [
            (cu_urg,  t_jour, 0,  7, 19, 2, [bls]),
            (cu_urg,  t_nuit, 0, 19, 31, 1, [bls, acls]),
            (cu_chir, t_jour, 0,  8, 20, 1, [bls, si]),
            (cu_ped,  t_jour, 1,  7, 19, 1, [bls, ped]),
            (cu_urg,  t_jour, 1,  7, 19, 2, [bls]),
        ]

        for cu, stype, day_offset, h_start, h_end, min_s, req_certs in shifts_data:
            start = (base + timedelta(days=day_offset)).replace(hour=h_start % 24)
            end   = (base + timedelta(days=day_offset + (1 if h_end >= 24 else 0))).replace(hour=h_end % 24)
            shift, _ = Shift.objects.get_or_create(
                care_unit=cu, shift_type=stype, start_datetime=start,
                defaults={"end_datetime": end, "min_staff": min_s, "max_staff": 5}
            )
            for c in req_certs:
                ShiftRequiredCertification.objects.get_or_create(shift=shift, certification=c)

        # ── Types d'absence ────────────────────────────────────────
        at_mal = AbsenceType.objects.get_or_create(name="Congé maladie",   defaults={"impacts_quota": True})[0]
        at_ann = AbsenceType.objects.get_or_create(name="Congé annuel",    defaults={"impacts_quota": False})[0]
        at_mat = AbsenceType.objects.get_or_create(name="Congé maternité", defaults={"impacts_quota": False})[0]

        # ── Absences de test ───────────────────────────────────────
        Absence.objects.get_or_create(
            staff=fatima, absence_type=at_mal,
            defaults={
                "start_date": date.today() - timedelta(days=2),
                "expected_end_date": date.today() + timedelta(days=5),
                "is_planned": False,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            "✅ Base alimentée avec succès ! "
            f"{Staff.objects.count()} soignants, "
            f"{Shift.objects.count()} postes, "
            f"{Absence.objects.count()} absences."
        ))