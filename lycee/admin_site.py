import sqlite3
import datetime
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.conf import settings


class LyceeAdminSite(AdminSite):
    site_header = "Administration Lycée"
    site_title = "Lycée | Admin"
    index_title = "Tableau de bord d'administration"
    index_template = "admin/lycee_index.html"

    def has_permission(self, request):
        """Restreint l'accès au /django-admin/ aux seuls Administrateurs."""
        from eleves.roles import has_role, ADMIN
        return request.user.is_active and (
            has_role(request.user, ADMIN) or request.user.is_superuser
        )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        extra = [
            path(
                "export-schema/",
                self.admin_view(self.export_schema_view),
                name="export_schema",
            ),
        ]
        return extra + urls

    def export_schema_view(self, request):
        # RGPD table classification
        IDENTITE_TABLES = {"eleves_eleve", "eleves_parent", "eleves_eleve_parents"}
        SCOLAIRE_TABLES = {"eleves_scolarite", "eleves_note", "eleves_matiere"}
        SENSIBLE_TABLES = {"eleves_sante", "eleves_medecintraitant"}

        def rgpd_category(name):
            if name in IDENTITE_TABLES:
                return "DONNÉES D'IDENTITÉ — Art. 6 §1 e RGPD — Accès : Administration"
            if name in SCOLAIRE_TABLES:
                return "DONNÉES SCOLAIRES — Art. 6 §1 e RGPD — Accès : Professeurs & Scolarité"
            if name in SENSIBLE_TABLES:
                return "DONNÉES SENSIBLES — Art. 9 RGPD — Accès RESTREINT : Pôle médical & Cantine"
            return "TABLES SYSTÈMES / DJANGO"

        db_path = settings.DATABASES["default"]["NAME"]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE sql IS NOT NULL "
            "ORDER BY type DESC, name"
        )
        rows = cursor.fetchall()
        conn.close()

        header = (
            "-- ============================================\n"
            "-- Schéma SQL – Base de données Lycée RGPD\n"
            f"-- Exporté le {datetime.datetime.now():%d/%m/%Y à %H:%M:%S}\n"
            "-- Base : SQLite\n"
            "--\n"
            "-- Classification RGPD des tables :\n"
            "--   [IDENTITÉ]  eleves_eleve, eleves_parent, eleves_eleve_parents\n"
            "--   [SCOLAIRE]  eleves_scolarite, eleves_note, eleves_matiere\n"
            "--   [SENSIBLE]  eleves_sante, eleves_medecintraitant\n"
            "-- ============================================\n\n"
        )

        # Group by RGPD category then by type
        from collections import defaultdict
        groups = defaultdict(list)
        for obj_type, name, sql in rows:
            cat = rgpd_category(name)
            groups[cat].append((obj_type, name, sql))

        category_order = [
            "DONNÉES D'IDENTITÉ — Art. 6 §1 e RGPD — Accès : Administration",
            "DONNÉES SCOLAIRES — Art. 6 §1 e RGPD — Accès : Professeurs & Scolarité",
            "DONNÉES SENSIBLES — Art. 9 RGPD — Accès RESTREINT : Pôle médical & Cantine",
            "TABLES SYSTÈMES / DJANGO",
        ]

        sections = []
        for cat in category_order:
            if cat not in groups:
                continue
            border = "=" * 60
            sections.append(
                f"-- {border}\n-- {cat}\n-- {border}\n\n"
                + "\n\n".join(
                    f"-- [{obj_type.upper()}] {name}\n{sql};"
                    for obj_type, name, sql in groups[cat]
                )
            )

        response = HttpResponse(
            header + "\n\n\n".join(sections),
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="schema_lycee_rgpd.sql"'
        return response


# name='admin' so all built-in admin templates ({% url 'admin:...' %}) resolve correctly
lycee_admin_site = LyceeAdminSite(name="admin")
