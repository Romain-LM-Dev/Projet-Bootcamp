"""
Commande pour preparer la semaine du 13 au 19 avril 2026 :
  - Cree les postes (Jour / Soir / Nuit) pour 2 unites de soin
  - Supprime toutes les affectations existantes sur ces postes
  - Laisse le personnel en place (cree via seed_data)

  Dimensionnement : 2 unites x 7j x 2 types + 4 nuits = 32 postes
  Capacite : 18 agents x ~4 postes max = ~72 slots bruts,
             ~60 apres absences -> couverture complete garantie.

Utilisation : python manage.py setup_test_week
"""
from django.core.management.base import BaseCommand
from datetime import date, datetime, time, timedelta

from core.models import CareUnit, ShiftType, AbsenceType
from shifts.models import Shift
from planning.models import ShiftAssignment, Absence
from staff.models import Staff


WEEK_START = date(2026, 4, 13)   # Lundi 13 avril 2026
WEEK_END   = date(2026, 4, 19)   # Dimanche 19 avril 2026

# (code ShiftType, heure_debut, heure_fin, min_staff, max_staff)
DAY_SHIFT_CONFIGS = [
    ('J', time(7,  0), time(15, 0), 1, 2),   # Jour - tous les jours
    ('S', time(15, 0), time(23, 0), 1, 2),   # Soir - tous les jours
]
# Nuit uniquement mercredi (offset 2) et samedi (offset 5)
NIGHT_SHIFT_CONFIG = ('N', time(23, 0), time(7, 0), 1, 1)
NIGHT_DAYS = {2, 5}   # mercredi et samedi (0=lundi)


class Command(BaseCommand):
    help = 'Prepare les postes de la semaine du 13-19 avril 2026 sans affectations'

    def handle(self, *args, **options):
        self.stdout.write('\n-- Preparation semaine de test : 13 -> 19 avril 2026 --\n')

        # Verifications prealables
        # On limite a 2 unites de soin pour garantir une couverture complete
        # avec 18 agents (32 postes au lieu de 64).
        all_care_units = list(CareUnit.objects.select_related('service').all())
        if not all_care_units:
            self.stdout.write(self.style.ERROR(
                '[ERREUR] Aucune unite de soin en base. Lancez d\'abord : python manage.py seed_data'
            ))
            return
        care_units = all_care_units[:2]

        all_configs = DAY_SHIFT_CONFIGS + [NIGHT_SHIFT_CONFIG]
        shift_types = {}
        for code, _, _, _, _ in all_configs:
            try:
                shift_types[code] = ShiftType.objects.get(code=code)
            except ShiftType.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'[ERREUR] Type de poste "{code}" introuvable. Lancez d\'abord : python manage.py seed_data'
                ))
                return

        staff_count = Staff.objects.filter(is_active=True).count()
        if staff_count == 0:
            self.stdout.write(self.style.ERROR(
                '[ERREUR] Aucun membre du personnel actif. Lancez d\'abord : python manage.py seed_data'
            ))
            return

        self.stdout.write(f'  {len(all_care_units)} unites de soin en base, {len(care_units)} retenues pour la semaine de test')
        self.stdout.write(f'  {staff_count} membre(s) du personnel actif\n')

        shifts_created  = 0
        shifts_existing = 0
        assignments_deleted = 0

        current_date = WEEK_START
        while current_date <= WEEK_END:
            day_label = current_date.strftime('%A %d/%m')
            self.stdout.write(f'  {day_label}')

            day_offset = (current_date - WEEK_START).days   # 0=lundi … 6=dimanche
            configs_for_day = list(DAY_SHIFT_CONFIGS)
            if day_offset in NIGHT_DAYS:
                configs_for_day.append(NIGHT_SHIFT_CONFIG)

            for care_unit in care_units:
                for code, start_t, end_t, min_s, max_s in configs_for_day:
                    shift_type = shift_types[code]
                    start_dt = datetime.combine(current_date, start_t)
                    # Nuit : end_datetime = lendemain matin
                    if end_t < start_t:
                        end_dt = datetime.combine(current_date + timedelta(days=1), end_t)
                    else:
                        end_dt = datetime.combine(current_date, end_t)

                    shift, created = Shift.objects.get_or_create(
                        care_unit=care_unit,
                        shift_type=shift_type,
                        start_datetime=start_dt,
                        defaults={
                            'end_datetime': end_dt,
                            'min_staff': min_s,
                            'max_staff': max_s,
                            'is_active': True,
                        }
                    )

                    if created:
                        shifts_created += 1
                    else:
                        shifts_existing += 1
                        deleted, _ = ShiftAssignment.objects.filter(shift=shift).delete()
                        assignments_deleted += deleted

            current_date += timedelta(days=1)

        total_shifts = shifts_created + shifts_existing

        # ── Absences de test pour la semaine ──────────────────────────────────
        absences_created = 0
        Absence.objects.filter(
            start_date__gte=WEEK_START,
            expected_end_date__lte=WEEK_END
        ).delete()

        type_maladie = AbsenceType.objects.filter(code='MAL').first()
        type_cp      = AbsenceType.objects.filter(code='CP').first()
        type_rtt     = AbsenceType.objects.filter(code='RTT').first()

        all_staff = list(Staff.objects.filter(is_active=True).order_by('last_name'))

        # Scénarios d'absence volontairement variés pour les tests
        absence_scenarios = []
        if len(all_staff) >= 1 and type_maladie:
            # Agent 1 : malade toute la semaine
            absence_scenarios.append({
                'staff': all_staff[0],
                'type': type_maladie,
                'start': WEEK_START,
                'end': WEEK_END,
                'planned': False,
                'label': 'Maladie semaine complete',
            })
        if len(all_staff) >= 4 and type_maladie:
            # Agent 4 : malade mercredi et jeudi
            absence_scenarios.append({
                'staff': all_staff[3],
                'type': type_maladie,
                'start': date(2026, 4, 15),
                'end': date(2026, 4, 16),
                'planned': False,
                'label': 'Maladie mer-jeu',
            })
        if len(all_staff) >= 7 and type_cp:
            # Agent 7 : conges payes lundi-mercredi
            absence_scenarios.append({
                'staff': all_staff[6],
                'type': type_cp,
                'start': date(2026, 4, 13),
                'end': date(2026, 4, 15),
                'planned': True,
                'label': 'Conges payes lun-mer',
            })
        if len(all_staff) >= 10 and type_rtt:
            # Agent 10 : RTT vendredi
            absence_scenarios.append({
                'staff': all_staff[9],
                'type': type_rtt,
                'start': date(2026, 4, 17),
                'end': date(2026, 4, 17),
                'planned': True,
                'label': 'RTT vendredi',
            })

        for s in absence_scenarios:
            _, created = Absence.objects.get_or_create(
                staff=s['staff'],
                absence_type=s['type'],
                start_date=s['start'],
                defaults={
                    'expected_end_date': s['end'],
                    'is_planned': s['planned'],
                }
            )
            if created:
                absences_created += 1
                self.stdout.write(
                    f'  Absence : {s["staff"].full_name} - {s["label"]}'
                )

        self.stdout.write(self.style.SUCCESS('\n[OK] Semaine prete !\n'))
        self.stdout.write(f'  Postes crees          : {shifts_created}')
        self.stdout.write(f'  Postes deja presents  : {shifts_existing}')
        self.stdout.write(f'  Affectations retirees : {assignments_deleted}')
        self.stdout.write(f'  Total postes a couvrir: {total_shifts}')
        self.stdout.write(
            f'  Calcul : {len(care_units)} unites x 7j x 2 types (Jour+Soir)'
            f' + {len(care_units)} unites x {len(NIGHT_DAYS)}j Nuit'
            f' = {len(care_units) * 7 * 2 + len(care_units) * len(NIGHT_DAYS)} postes'
        )
        self.stdout.write(f'  Personnel dispo       : {staff_count} agents actifs')
        self.stdout.write(f'  Absences creees       : {absences_created}\n')
        self.stdout.write('  Testez maintenant :')
        self.stdout.write('    Affectation manuelle  -> ecran "Postes" dans l\'app')
        self.stdout.write(
            '    Generation automatique -> ecran "Generation auto" '
            '(13/04/2026 -> 19/04/2026)'
        )
