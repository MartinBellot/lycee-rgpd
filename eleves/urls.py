from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"eleves", views.EleveViewSet, basename="api-eleve")
router.register(r"parents", views.ParentViewSet)
router.register(r"medecins", views.MedecinViewSet)
router.register(r"matieres", views.MatiereViewSet)
router.register(r"notes", views.NoteViewSet, basename="api-note")

urlpatterns = [
    # ── API REST ──────────────────────────────────────────────────
    path("api/", include(router.urls)),

    # ── Redirect root → /admin/ ───────────────────────────────────
    path("", RedirectView.as_view(url="/admin/", permanent=False)),

    # ── Custom admin – Dashboard ──────────────────────────────────
    path("admin/login/", views.staff_login, name="staff_login"),
    path("admin/logout/", views.staff_logout, name="staff_logout"),
    path("admin/", views.dashboard, name="dashboard"),

    # ── Custom admin – Élèves ─────────────────────────────────────
    path("admin/eleves/", views.eleve_list, name="eleve_list"),
    path("admin/eleves/new/", views.eleve_create, name="eleve_create"),
    path("admin/eleves/<int:pk>/", views.eleve_detail, name="eleve_detail"),
    path("admin/eleves/<int:pk>/edit/", views.eleve_edit, name="eleve_edit"),
    path("admin/eleves/<int:pk>/delete/", views.eleve_delete, name="eleve_delete"),

    # ── Custom admin – Parents ────────────────────────────────────
    path("admin/parents/", views.parent_list, name="parent_list"),
    path("admin/parents/new/", views.parent_create, name="parent_create"),
    path("admin/parents/<int:pk>/edit/", views.parent_edit, name="parent_edit"),
    path("admin/parents/<int:pk>/delete/", views.parent_delete, name="parent_delete"),

    # ── Custom admin – Médecins ───────────────────────────────────
    path("admin/medecins/", views.medecin_list, name="medecin_list"),
    path("admin/medecins/new/", views.medecin_create, name="medecin_create"),
    path("admin/medecins/<int:pk>/edit/", views.medecin_edit, name="medecin_edit"),
    path("admin/medecins/<int:pk>/delete/", views.medecin_delete, name="medecin_delete"),

    # ── Custom admin – Matières ───────────────────────────────────
    path("admin/matieres/", views.matiere_list, name="matiere_list"),
    path("admin/matieres/new/", views.matiere_create, name="matiere_create"),
    path("admin/matieres/<int:pk>/edit/", views.matiere_edit, name="matiere_edit"),
    path("admin/matieres/<int:pk>/delete/", views.matiere_delete, name="matiere_delete"),

    # ── Custom admin – Notes ──────────────────────────────────────
    path("admin/notes/", views.note_list, name="note_list"),
    path("admin/notes/new/", views.note_create, name="note_create"),
    path("admin/notes/<int:pk>/edit/", views.note_edit, name="note_edit"),
    path("admin/notes/<int:pk>/delete/", views.note_delete, name="note_delete"),

    # ── Custom admin – Utilisateurs (admin only) ──────────────────
    path("admin/utilisateurs/", views.user_list, name="user_list"),
    path("admin/utilisateurs/new/", views.user_create, name="user_create"),
    path("admin/utilisateurs/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("admin/utilisateurs/<int:pk>/delete/", views.user_delete, name="user_delete"),

    # ── Journal d'audit & signalements (admin only) ───────────────
    path("admin/audit/", views.audit_log_list, name="audit_log"),
    path("admin/audit/signalements/", views.breach_report_list, name="breach_report_list"),

    # ── DPO Contact & Signalement (public / tous authentifiés) ────
    path("dpo/", views.dpo_contact, name="dpo_contact"),
    path("dpo/signalement/", views.breach_report, name="breach_report"),

    # ── Portail élèves/parents (/students/) ───────────────────────
    path("students/", views.student_portal_redirect, name="student_portal"),
    path("students/login/", views.student_login, name="student_login"),
    path("students/logout/", views.student_logout, name="student_logout"),
    path("students/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("students/parent/", views.parent_dashboard, name="parent_dashboard"),
    path("students/parent/eleve/<int:pk>/", views.parent_child_notes, name="parent_child_notes"),

    # ── Droits RGPD (Art. 15, 16, 17, 20) ────────────────────────
    path("students/rgpd/", views.rgpd_access, name="rgpd_access"),
    path("students/rgpd/rectifier/", views.rgpd_rectify, name="rgpd_rectify"),
    path("students/rgpd/effacer/", views.rgpd_erase, name="rgpd_erase"),
    path("students/rgpd/exporter/", views.rgpd_export, name="rgpd_export"),
]
