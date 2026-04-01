from django.urls import path
from . import views

urlpatterns = [
    # ── Soignants ──────────────────────────────────────────────
    path("staff/",                          views.StaffListView.as_view(),                    name="staff-list"),
    path("staff/<int:pk>/",                 views.StaffDetailView.as_view(),                  name="staff-detail"),

    # ── Postes de garde ────────────────────────────────────────
    path("shifts/",                         views.ShiftListView.as_view(),                    name="shift-list"),
    path("shifts/<int:pk>/",                views.ShiftDetailView.as_view(),                  name="shift-detail"),

    # ── Affectations ───────────────────────────────────────────
    path("assignments/",                    views.AssignmentListView.as_view(),               name="assignment-list"),
    path("assignments/<int:pk>/",           views.AssignmentDetailView.as_view(),             name="assignment-detail"),

    # ── Absences ───────────────────────────────────────────────
    path("absences/",                       views.AbsenceListView.as_view(),                  name="absence-list"),
    path("absences/<int:pk>/",              views.AbsenceDetailView.as_view(),                name="absence-detail"),

    # ── Rôles & Spécialités ────────────────────────────────────
    path("roles/",                          views.RoleListView.as_view(),                     name="role-list"),
    path("specialties/",                    views.SpecialtyListView.as_view(),                name="specialty-list"),

    # ── Certifications soignant ────────────────────────────────
    path("staff-certifications/",           views.StaffCertificationListCreateView.as_view(), name="staff-cert-list"),
    path("staff-certifications/<int:pk>/",  views.StaffCertificationDetailView.as_view(),     name="staff-cert-detail"),

    # ── Contrats ───────────────────────────────────────────────
    path("contracts/",                      views.ContractListCreateView.as_view(),           name="contract-list"),
    path("contracts/<int:pk>/",             views.ContractDetailView.as_view(),               name="contract-detail"),

    # ── Référentiels ───────────────────────────────────────────
    path("certifications/",                 views.CertificationListView.as_view(),            name="cert-list"),
    path("contract-types/",                 views.ContractTypeListView.as_view(),             name="contract-type-list"),
    path("shift-types/",                    views.ShiftTypeListView.as_view(),                name="shift-type-list"),
    path("absence-types/",                  views.AbsenceTypeListView.as_view(),              name="absence-type-list"),
    path("services/",                       views.ServiceListView.as_view(),                  name="service-list"),

    # ── Génération automatique de planning ─────────────────────
    path("plannings/generate/",             views.PlanningGenerateView.as_view(),             name="planning-generate"),
    path("plannings/score/",                views.PlanningScoreView.as_view(),                name="planning-score"),
]
