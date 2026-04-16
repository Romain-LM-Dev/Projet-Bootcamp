"""
Backend URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets
from core.views import RuleViewSet, ServiceViewSet, CareUnitViewSet, ShiftTypeViewSet, AbsenceTypeViewSet
from staff.views import StaffViewSet, RoleViewSet, SpecialtyViewSet, CertificationViewSet, ContractTypeViewSet, ContractViewSet, StaffRoleViewSet
from shifts.views import ShiftViewSet, ShiftTemplateViewSet
from planning.views import AbsenceViewSet, PreferenceViewSet, ShiftAssignmentViewSet, PlanningSnapshotViewSet
from optimization.views import OptimizationAlgorithmViewSet, OptimizationConfigViewSet, OptimizationRunViewSet, OptimizationResultViewSet, GeneratePlanningView
from core.views import AuthLoginView, AuthLogoutView, AuthUserView

# Create router
router = DefaultRouter()

# Core endpoints
router.register(r'rules', RuleViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'care-units', CareUnitViewSet)
router.register(r'shift-types', ShiftTypeViewSet)
router.register(r'absence-types', AbsenceTypeViewSet)

# Staff endpoints
router.register(r'staff', StaffViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'staff-roles', StaffRoleViewSet)
router.register(r'specialties', SpecialtyViewSet)
router.register(r'certifications', CertificationViewSet)
router.register(r'contract-types', ContractTypeViewSet)
router.register(r'contracts', ContractViewSet)

# Shifts endpoints
router.register(r'shifts', ShiftViewSet)
router.register(r'shift-templates', ShiftTemplateViewSet)

# Planning endpoints
router.register(r'absences', AbsenceViewSet)
router.register(r'preferences', PreferenceViewSet)
router.register(r'assignments', ShiftAssignmentViewSet)
router.register(r'planning-snapshots', PlanningSnapshotViewSet)

# Optimization endpoints
router.register(r'optimization-algorithms', OptimizationAlgorithmViewSet)
router.register(r'optimization-configs', OptimizationConfigViewSet)
router.register(r'optimization-runs', OptimizationRunViewSet)
router.register(r'optimization-results', OptimizationResultViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # Custom auth endpoints
    path('api/auth/login/', AuthLoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', AuthLogoutView.as_view(), name='auth-logout'),
    path('api/auth/user/', AuthUserView.as_view(), name='auth-user'),
    path('api/generate/', GeneratePlanningView.as_view(), name='generate-planning'),
]
