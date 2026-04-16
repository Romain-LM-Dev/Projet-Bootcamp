"""
Commande pour peupler la base de données avec des données de test équilibrées
"""
from django.core.management.base import BaseCommand
from datetime import date, time
from django.contrib.auth.models import User

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
            from optimization.models import OptimizationResult, OptimizationRun, OptimizationConfig, OptimizationAlgorithm
            from planning.models import PlanningSnapshot, Preference
            OptimizationResult.objects.all().delete()
            OptimizationRun.objects.all().delete()
            OptimizationConfig.objects.all().delete()
            OptimizationAlgorithm.objects.all().delete()
            PlanningSnapshot.objects.all().delete()
            Preference.objects.all().delete()
            Absence.objects.all().delete()
            ShiftAssignment.objects.all().delete()
            Shift.objects.all().delete()
            StaffRole.objects.all().delete()
            StaffSpecialty.objects.all().delete()
            Contract.objects.all().delete()
            Staff.objects.all().delete()
            CareUnit.objects.all().delete()
            Service.objects.all().delete()
            ShiftType.objects.all().delete()
            AbsenceType.objects.all().delete()
            Rule.objects.all().delete()
            Role.objects.all().delete()
            Specialty.objects.all().delete()
            ContractType.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Donnees supprimees avec succes'))

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
        self.stdout.write(self.style.SUCCESS('  OK Configuration d\'optimisation créée'))

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

        # 9. Personnel (22 agents)
        # Dimensionnement : 22 agents x ~35h/semaine = ~96 slots theoriques.
        # Apres absences (~10 slots perdus) : ~86 slots disponibles.
        # Besoin couverture complete (2/2) sur 32 postes : 60 affectations -> confortable.
        self.stdout.write('Creation du personnel...')
        spec_list = list(specialties.values())
        ct_list   = list(contract_types.values())
        staff_members = []
        for idx, (first_name, last_name, role_code) in enumerate([
            ('Marie',    'Dupont',    'IDE'), ('Pierre',   'Martin',    'IDE'),
            ('Sophie',   'Bernard',   'AS'),  ('Thomas',   'Petit',     'MED'),
            ('Julie',    'Robert',    'IDE'), ('Nicolas',  'Richard',   'AS'),
            ('Camille',  'Durand',    'IDE'), ('Julien',   'Dubois',    'MED'),
            ('Laura',    'Moreau',    'IDE'), ('Kevin',    'Simon',     'AS'),
            ('Isabelle', 'Laurent',   'IDE'), ('Antoine',  'Lefevre',   'AS'),
            ('Emma',     'Blanc',     'IDE'), ('Lucas',    'Rousseau',  'AS'),
            ('Manon',    'Garnier',   'IDE'), ('Hugo',     'Faure',     'MED'),
            ('Celine',   'Bonnet',    'AS'),  ('Romain',   'Lambert',   'IDE'),
            ('Lea',      'Marchand',  'AS'),  ('Theo',     'Renard',    'IDE'),
            ('Clara',    'Fontaine',  'AS'),  ('Paul',     'Legrand',   'IDE'),
        ]):
            email = f"{first_name.lower()}.{last_name.lower()}@hopital.fr"
            staff, _ = Staff.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name, 'last_name': last_name,
                    'employee_id': f"EMP{idx+1:03d}",
                    'is_active': True, 'hire_date': date(2022, 1, 1)
                }
            )
            staff_members.append(staff)
            StaffRole.objects.get_or_create(staff=staff, role=roles[role_code])

            # Specialite et contrat deterministes (rotation cyclique)
            spec = spec_list[idx % len(spec_list)]
            StaffSpecialty.objects.get_or_create(staff=staff, specialty=spec, defaults={'level': 2})

            ct = ct_list[idx % len(ct_list)]
            Contract.objects.get_or_create(
                staff=staff, contract_type=ct,
                defaults={'start_date': date(2024, 1, 1), 'workload_percent': 100, 'is_current': True}
            )
            self.stdout.write(f'  OK {first_name} {last_name} ({role_code})')

        # Les postes et affectations sont créés par setup_test_week
        # seed_data ne gère que les données de référence (personnel, services, etc.)

        # Résumé
        self.stdout.write(self.style.SUCCESS('\n[OK] Base de donnees prete !'))
        self.stdout.write(
            f'  {Service.objects.count()} services | '
            f'{CareUnit.objects.count()} unites de soin | '
            f'{Staff.objects.count()} membres du personnel'
        )
        self.stdout.write('  Postes : aucun — lancez ensuite : python manage.py setup_test_week')