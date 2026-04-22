"""
Permissions DRF – contrôle d'accès par rôle RGPD.
"""
from rest_framework.permissions import BasePermission
from .roles import (
    ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE,
    INFIRMIER, CANTINE, ELEVE, PARENT, has_role,
)


class IsAdminRole(BasePermission):
    """Administrateur seulement."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return has_role(request.user, ADMIN)


class IsStaffRole(BasePermission):
    """Tout membre du personnel (admin, scolarité, professeur, vie scolaire, infirmier, cantine)."""
    message = "Accès réservé au personnel de l'établissement."

    def has_permission(self, request, view):
        return has_role(request.user, ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE)


class IsAdminOrScolarite(BasePermission):
    message = "Accès réservé à la scolarité et aux administrateurs."

    def has_permission(self, request, view):
        return has_role(request.user, ADMIN, SCOLARITE)


class CanReadEleve(BasePermission):
    """Peut lire les données d'un élève (tout le personnel + élève lui-même + ses parents)."""
    message = "Accès non autorisé aux données élèves."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from .models import Eleve
        if not isinstance(obj, Eleve):
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        if role in (ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE):
            return True
        if role == ELEVE:
            profile = request.user.profile
            return profile.eleve_id == obj.pk
        if role == PARENT:
            profile = request.user.profile
            return profile.parent and obj in profile.parent.eleves.all()
        return False


class CanManageNotes(BasePermission):
    """Peut créer/modifier des notes (admin, scolarité, professeur limité à sa classe+matières)."""
    message = "Vous n'êtes pas autorisé à gérer ces notes."

    def has_permission(self, request, view):
        return has_role(request.user, ADMIN, SCOLARITE, PROFESSEUR)

    def has_object_permission(self, request, view, obj):
        from .models import Note
        if not isinstance(obj, Note):
            return True
        if has_role(request.user, ADMIN, SCOLARITE):
            return True
        if has_role(request.user, PROFESSEUR):
            profile = request.user.profile
            # Le professeur ne peut gérer que les notes de sa classe et ses matières
            classe_ok = (
                hasattr(obj.eleve, 'scolarite')
                and obj.eleve.scolarite.classe.lower() == profile.classe.lower()
            )
            matiere_ok = profile.matieres.filter(pk=obj.matiere_id).exists()
            return classe_ok and matiere_ok
        return False


class CanAccessSante(BasePermission):
    """Accès aux données de santé (art. 9) : admin, scolarité, infirmier, cantine."""
    message = "Données sensibles (art. 9 RGPD) — accès non autorisé."

    def has_permission(self, request, view):
        return has_role(request.user, ADMIN, SCOLARITE, INFIRMIER, CANTINE)


class IsEleveOwner(BasePermission):
    """L'élève peut accéder uniquement à ses propres données."""
    message = "Vous n'avez accès qu'à vos propres données."

    def has_permission(self, request, view):
        return has_role(request.user, ELEVE, PARENT, ADMIN, SCOLARITE,
                        PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE)

    def has_object_permission(self, request, view, obj):
        from .models import Eleve
        if has_role(request.user, ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE):
            return True
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
        if profile.role == ELEVE:
            return profile.eleve_id == (obj.pk if isinstance(obj, Eleve) else None)
        if profile.role == PARENT:
            return profile.parent and isinstance(obj, Eleve) and obj in profile.parent.eleves.all()
        return False
