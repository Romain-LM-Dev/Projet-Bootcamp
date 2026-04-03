"""
Commande pour peupler la base de données avec des données de test équilibrées
"""
from django.core.management.base import BaseCommand
from datetime import datetime, date, time, timedelta
from django.contrib.auth.models import User
import random

# Import models
from core.models import Service, CareUnit, ShiftType, AbsenceType, Rule
from staff.models import Staff, Role, ContractType, Contract, StaffRole, Specialty, StaffSpecialty
from shifts.models import Shift
from planning.models import ShiftAssignment, Absence
from optimization.models import OptimizationAlgorithm, OptimizationConfig


class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de test équilibrées pour HospiPlan2'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Supprime toutes les données existantes avant de peupler')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des données existantes...')
            Absence.objects.all().delete()
            ShiftAssignment.objects.all().delete()
            Shift.objects.all().delete()
            Staff.objects.all().delete()
            Service.objects.all().delete()
            CareUnit.objects.all().delete()
            ShiftType.objects.all().delete()
            AbsenceType.objects.all().delete()
            Rule.objects.all().delete()
            Role.objects.all().delete()
            Specialty.objects.all().delete()
            ContractType.objects.all().delete()
            Contract.objects.all().delete()
            StaffRole.objects.all().delete()
            StaffSpecialty.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Données supprimées avec succès'))

        # Créer superutilisateur admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@hopital.fr', 'admin')
            self.stdout.write(self.style.SUCCESS('Admin créé: admin / admin'))

        # 0. Configuration d'optimisation par défaut
        self.stdout.write('Création de la configuration d\'optimisation...')
        algo, _ = OptimizationAlgorithm.objects.get_or_create(
            name='Algorithme Glouton',
            defaults={'algo_type': 'greedy', 'is_active': True, 'description': 'Algorithme glouton avec heuristiques d\'équité'}
        )
        OptimizationConfig.objects.get_or_create(
            name='Configuration par défaut',
            defaults={
                'algorithm': algo,
                'is_active': True,
                'description': 'Configuration standard pour la génération automatique de planning',
            }
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Configuration d\'optimisation créée'))

        # 1. Types de poste (3)
        self.stdout.write('Création des types de poste...')
        shift_types = {}
        for st_data in [
            {'name': 'Jour', 'code': 'J', 'duration_hours': 8, 'start_time': time(7, 0), 'end_time': time(15, 0), 'color': '#3B82F6'},
            {'name': 'Soir', 'code': 'S', 'duration_hours': 8, 'start_time': time(15, 0), 'end_time': time(23, 0), 'color': '#F59E0B'},
            {'name': 'Nuit', 'code': 'N', 'duration_hours': 10, 'start_time': time(23, 0), 'end_time': time(7, 0), 'requires_rest_after': True, 'color': '#6366F1'},
        ]:
            st, _ = ShiftType.objects.get_or_create(code=st_data['code'], defaults=st_data)
            shift_types[st.code] = st

        # 2. Types d'absence (3)
        self.stdout.write('Création des types d\'absence...')
        absence_types = {}
        for at_data in [
            {'name': 'Congés payés', 'code': 'CP', 'is_paid': True},
            {'name': 'Maladie', 'code': 'MAL', 'is_paid': True, 'requires_justification': True},
            {'name': 'RTT', 'code': 'RTT', 'is_paid': True},
        ]:
            at, _ = AbsenceType.objects.get_or_create(code=at_data['code'], defaults=at_data)
            absence_types[at.code] = at

        # 3. Règles métier (3)
        self.stdout.write('Création des règles métier...')
        for rule_data in [
            {'name': 'Nuits consécutives max', 'rule_type': 'threshold', 'value': 5, 'unit': 'nuits', 'category': 'Planning'},
            {'name': 'Repos après nuit', 'rule_type': 'constraint', 'value': 1, 'unit': 'jour', 'category': 'Planning'},
            {'name': 'Charge max hebdo', 'rule_type': 'threshold', 'value': 48, 'unit': 'heures', 'category': 'Légal'},
        ]:
            Rule.objects.get_or_create(name=rule_data['name'], defaults=rule_data)

        # 4. Services (3)
        self.stdout.write('Création des services...')
        services = {}
        for svc_data in [
            {'name': 'Urgences', 'code': 'URG', 'bed_capacity': 30},
            {'name': 'Chirurgie', 'code': 'CHIR', 'bed_capacity': 40},
            {'name': 'Médecine', 'code': 'MED', 'bed_capacity': 50},
        ]:
            svc, _ = Service.objects.get_or_create(code=svc_data['code'], defaults=svc_data)
            services[svc.code] = svc

        # 5. Unités de soin (4)
        self.stdout.write('Création des unités de soin...')
        care_units = {}
        for cu_data in [
            {'service_code': 'URG', 'name': 'Urgences Adultes', 'code': 'URGA', 'bed_count': 20},
            {'service_code': 'URG', 'name': 'Urgences Pédiatriques', 'code': 'URGP', 'bed_count': 10},
            {'service_code': 'CHIR', 'name': 'Chirurgie A', 'code': 'CHIRA', 'bed_count': 20},
            {'service_code': 'MED', 'name': 'Médecine A', 'code': 'MEDA', 'bed_count': 25},
        ]:
            service = services[cu_data['service_code']]
            cu, _ = CareUnit.objects.get_or_create(
                service=service, code=cu_data['code'],
                defaults={'name': cu_data['name'], 'bed_count': cu_data['bed_count']}
            )
            care_units[cu.code] = cu

        # 6. Rôles (3)
        self.stdout.write('Création des rôles...')
        roles = {}
        for role_data in [
            {'name': 'Infirmier', 'code': 'IDE'},
            {'name': 'Aide-Soignant', 'code': 'AS'},
            {'name': 'Médecin', 'code': 'MED'},
        ]:
            role, _ = Role.objects.get_or_create(code=role_data['code'], defaults=role_data)
            roles[role.code] = role

        # 7. Spécialités (3)
        self.stdout.write('Création des spécialités...')
        specialties = {}
        for spec_data in [
            {'name': 'Urgences'},
            {'name': 'Chirurgie'},
            {'name': 'Médecine Générale'},
        ]:
            spec, _ = Specialty.objects.get_or_create(name=spec_data['name'])
            specialties[spec.name] = spec

        # 8. Types de contrat (2)
        self.stdout.write('Création des types de contrat...')
        contract_types = {}
        for ct_data in [
            {'name': 'Temps plein', 'code': 'TP', 'max_hours_per_week': 35, 'leave_days_per_year': 25, 'night_shift_allowed': True},
            {'name': 'Temps partiel 80%', 'code': 'TP80', 'max_hours_per_week': 28, 'leave_days_per_year': 25, 'night_shift_allowed': True},
        ]:
            ct, _ = ContractType.objects.get_or_create(code=ct_data['code'], defaults=ct_data)
            contract_types[ct.code] = ct

        # 9. Personnel (8)
        self.stdout.write('Création du personnel...')
        staff_members = []
        for first_name, last_name, role_code in [
            ('Marie', 'Dupont', 'IDE'), ('Pierre', 'Martin', 'IDE'),
            ('Sophie', 'Bernard', 'AS'), ('Thomas', 'Petit', 'MED'),
            ('Julie', 'Robert', 'IDE'), ('Nicolas', 'Richard', 'AS'),
            ('Camille', 'Durand', 'IDE'), ('Julien', 'Dubois', 'MED'),
        ]:
            email = f"{first_name.lower()}.{last_name.lower()}@hopital.fr"
            staff, _ = Staff.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name, 'last_name': last_name,
                    'employee_id': f"EMP{len(staff_members)+1:03d}",
                    'is_active': True, 'hire_date': date(2022, 1, 1)
                }
            )
            staff_members.append(staff)
            role = roles[role_code]
            StaffRole.objects.get_or_create(staff=staff, role=role)

            # Ajouter une spécialité
            spec = random.choice(list(specialties.values()))
            StaffSpecialty.objects.get_or_create(staff=staff, specialty=spec, defaults={'level': 2})

            # Ajouter un contrat
            ct = random.choice(list(contract_types.values()))
            Contract.objects.get_or_create(
                staff=staff, contract_type=ct,
                defaults={'start_date': date(2024, 1, 1), 'workload_percent': 100, 'is_current': True}
            )
            self.stdout.write(f'  ✓ {first_name} {last_name} ({role_code})')

        # 10. Postes pour 7 jours (semaine complète)
        self.stdout.write('Création des postes...')
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Lundi de la semaine courante
        shifts_created = 0

        for day_offset in range(7):  # Lundi à Dimanche
            current_date = start_of_week + timedelta(days=day_offset)

            for care_unit in CareUnit.objects.all():
                # Jour: 07:00-15:00
                Shift.objects.get_or_create(
                    care_unit=care_unit, shift_type=shift_types['J'],
                    start_datetime=datetime.combine(current_date, time(7, 0)),
                    defaults={
                        'end_datetime': datetime.combine(current_date, time(15, 0)),
                        'min_staff': 2, 'max_staff': 4, 'is_active': True
                    }
                )
                shifts_created += 1

                # Soir: 15:00-23:00
                Shift.objects.get_or_create(
                    care_unit=care_unit, shift_type=shift_types['S'],
                    start_datetime=datetime.combine(current_date, time(15, 0)),
                    defaults={
                        'end_datetime': datetime.combine(current_date, time(23, 0)),
                        'min_staff': 1, 'max_staff': 3, 'is_active': True
                    }
                )
                shifts_created += 1

        self.stdout.write(f'  ✓ {shifts_created} postes créés pour la semaine')

        # 11. Affectations (2 par poste)
        self.stdout.write('Création des affectations...')
        assignments_created = 0
        active_staff = [s for s in staff_members if s.is_active]

        for shift in Shift.objects.all():
            # Assigner 1 à 2 personnes par poste
            num_assignments = random.randint(1, min(2, len(active_staff)))
            assigned_staff = random.sample(active_staff, num_assignments)

            for staff in assigned_staff:
                if not ShiftAssignment.objects.filter(staff=staff, shift=shift).exists():
                    ShiftAssignment.objects.create(
                        staff=staff, shift=shift, status='confirmed', source='manual'
                    )
                    assignments_created += 1

        self.stdout.write(f'  ✓ {assignments_created} affectations créées')

        # 12. Quelques absences (3)
        self.stdout.write('Création des absences...')
        for i, staff in enumerate(random.sample(active_staff, min(3, len(active_staff)))):
            absence_type = random.choice([absence_types['CP'], absence_types['MAL'], absence_types['RTT']])
            start = today + timedelta(days=random.randint(1, 14))
            duration = random.randint(1, 3)

            Absence.objects.get_or_create(
                staff=staff, absence_type=absence_type, start_date=start,
                defaults={
                    'expected_end_date': start + timedelta(days=duration),
                    'is_planned': absence_type.code != 'MAL'
                }
            )

        self.stdout.write(f'  ✓ {Absence.objects.count()} absences créées')

        # Résumé
        self.stdout.write(self.style.SUCCESS('\n✅ Base de données prête !'))
        self.stdout.write(f'''
Récapitulatif :
- {Service.objects.count()} services
- {CareUnit.objects.count()} unités de soin
- {Staff.objects.count()} membres du personnel
- {Shift.objects.count()} postes (semaine complète)
- {ShiftAssignment.objects.count()} affectations
- {Absence.objects.count()} absences
        ''')