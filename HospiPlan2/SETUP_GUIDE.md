# HospiPlan2 - Guide de Configuration Complète

## ✅ État actuel

- [x] Structure du projet créée
- [x] Tous les modèles Django créés (20+ modèles)
- [x] Configuration Django settings.py mise à jour
- [ ] Serializers à créer
- [ ] Views à créer
- [ ] URLs à configurer
- [ ] Frontend React à créer
- [ ] Migrations à exécuter

## 🚀 Étapes pour finaliser le projet

### Étape 1 : Créer les serializers

Pour chaque app, créez un fichier `serializers.py` :

**core/serializers.py**
```python
from rest_framework import serializers
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class CareUnitSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    class Meta:
        model = CareUnit
        fields = '__all__'

class ShiftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftType
        fields = '__all__'

class AbsenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceType
        fields = '__all__'
```

**staff/serializers.py**
```python
from rest_framework import serializers
from .models import Staff, Role, Specialty, Certification, Contract, ContractType

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'

# ... autres serializers
```

**shifts/serializers.py**
```python
from rest_framework import serializers
from .models import Shift, ShiftTemplate

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = '__all__'
```

**planning/serializers.py**
```python
from rest_framework import serializers
from .models import Absence, Preference, ShiftAssignment, PlanningSnapshot

class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = '__all__'

class ShiftAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftAssignment
        fields = '__all__'

# ... autres serializers
```

**optimization/serializers.py**
```python
from rest_framework import serializers
from .models import OptimizationConfig, OptimizationRun

class OptimizationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizationConfig
        fields = '__all__'

class OptimizationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizationRun
        fields = '__all__'
```

### Étape 2 : Créer les views

Pour chaque app, créez un fichier `views.py` :

**core/views.py**
```python
from rest_framework import viewsets
from .models import Rule, Service, CareUnit, ShiftType, AbsenceType
from .serializers import *

class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.filter(is_active=True)
    serializer_class = RuleSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer

# ... autres ViewSets
```

**staff/views.py**
```python
from rest_framework import viewsets
from .models import Staff, Role, Specialty, Certification, Contract
from .serializers import *

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

# ... autres ViewSets
```

**shifts/views.py**
```python
from rest_framework import viewsets
from .models import Shift, ShiftTemplate
from .serializers import *

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer

class ShiftTemplateViewSet(viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.all()
    serializer_class = ShiftTemplateSerializer
```

**planning/views.py**
```python
from rest_framework import viewsets
from .models import Absence, Preference, ShiftAssignment, PlanningSnapshot
from .serializers import *

class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer

class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ShiftAssignment.objects.all()
    serializer_class = ShiftAssignmentSerializer

# ... autres ViewSets
```

**optimization/views.py**
```python
from rest_framework import viewsets, views, response
from .models import OptimizationConfig, OptimizationRun
from .serializers import *

class OptimizationConfigViewSet(viewsets.ModelViewSet):
    queryset = OptimizationConfig.objects.filter(is_active=True)
    serializer_class = OptimizationConfigSerializer

class OptimizationRunViewSet(viewsets.ModelViewSet):
    queryset = OptimizationRun.objects.all()
    serializer_class = OptimizationRunSerializer

class GeneratePlanningView(views.APIView):
    """Endpoint pour générer un planning automatiquement."""
    def post(self, request):
        # Logique de génération ici
        return response.Response({"status": "Generation started"})
```

### Étape 3 : Configurer les URLs

**config/urls.py**
```python
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets
from core.views import RuleViewSet, ServiceViewSet, CareUnitViewSet, ShiftTypeViewSet, AbsenceTypeViewSet
from staff.views import StaffViewSet, RoleViewSet, SpecialtyViewSet, CertificationViewSet, ContractViewSet
from shifts.views import ShiftViewSet, ShiftTemplateViewSet
from planning.views import AbsenceViewSet, PreferenceViewSet, ShiftAssignmentViewSet, PlanningSnapshotViewSet
from optimization.views import OptimizationConfigViewSet, OptimizationRunViewSet, GeneratePlanningView

# Router
router = DefaultRouter()

# Core
router.register(r'rules', RuleViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'care-units', CareUnitViewSet)
router.register(r'shift-types', ShiftTypeViewSet)
router.register(r'absence-types', AbsenceTypeViewSet)

# Staff
router.register(r'staff', StaffViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'specialties', SpecialtyViewSet)
router.register(r'certifications', CertificationViewSet)
router.register(r'contracts', ContractViewSet)

# Shifts
router.register(r'shifts', ShiftViewSet)
router.register(r'shift-templates', ShiftTemplateViewSet)

# Planning
router.register(r'absences', AbsenceViewSet)
router.register(r'preferences', PreferenceViewSet)
router.register(r'assignments', ShiftAssignmentViewSet)
router.register(r'planning-snapshots', PlanningSnapshotViewSet)

# Optimization
router.register(r'optimization-configs', OptimizationConfigViewSet)
router.register(r'optimization-runs', OptimizationRunViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/generate/', GeneratePlanningView.as_view(), name='generate-planning'),
]
```

### Étape 4 : Créer le frontend React

```bash
cd frontend
npm create vite@latest . -- --template react
npm install axios react-router-dom @tanstack/react-query
```

**frontend/src/App.jsx**
```jsx
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/staff">Staff</Link>
        <Link to="/shifts">Postes</Link>
        <Link to="/planning">Planning</Link>
      </nav>
      <Routes>
        <Route path="/staff" element={<StaffPage />} />
        <Route path="/shifts" element={<ShiftsPage />} />
        <Route path="/planning" element={<PlanningPage />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### Étape 5 : Exécuter les migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Étape 6 : Tester

1. Backend : http://localhost:8000/admin
2. API : http://localhost:8000/api/staff/
3. Frontend : http://localhost:5173

## 📝 Notes

- Les fichiers de cette session (Phase 3) peuvent être copiés comme référence
- Le projet HospiPlan original est fonctionnel et peut servir de template
- Pour la génération automatique, copiez l'optimizer.py de HospiPlan dans optimization/engine.py

## 🎯 Prochaines étapes avancées

1. Implémenter l'algorithme de génération automatique
2. Créer l'interface de génération dans le frontend
3. Ajouter les tests unitaires
4. Configurer pour la production