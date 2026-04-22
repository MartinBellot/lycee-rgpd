# ─────────────────────────────────────────────────────────────────────────────
# Rôles RGPD – Lycée
# ─────────────────────────────────────────────────────────────────────────────

ADMIN        = "admin"
SCOLARITE    = "scolarite"
PROFESSEUR   = "professeur"
VIE_SCOLAIRE = "vie_scolaire"
INFIRMIER    = "infirmier"
CANTINE      = "cantine"
ELEVE        = "eleve"
PARENT       = "parent"

ROLE_CHOICES = [
    (ADMIN,        "Administrateur"),
    (SCOLARITE,    "Scolarité"),
    (PROFESSEUR,   "Professeur"),
    (VIE_SCOLAIRE, "Vie scolaire"),
    (INFIRMIER,    "Infirmier·ère"),
    (CANTINE,      "Cantine"),
    (ELEVE,        "Élève"),
    (PARENT,       "Parent / Tuteur"),
]

ROLE_LABELS = dict(ROLE_CHOICES)

# Rôles ayant accès à l'interface /admin/ personnalisée
STAFF_ROLES = {ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE}

# Rôles ayant accès au portail /students/
STUDENT_ROLES = {ELEVE, PARENT}


def get_role(user):
    """Retourne le rôle de l'utilisateur (str) ou None."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except Exception:
        # Superuser sans profil → admin par défaut
        if user.is_superuser:
            return ADMIN
        return None


def has_role(user, *roles):
    """Vérifie si l'utilisateur possède l'un des rôles donnés."""
    return get_role(user) in roles


def is_staff_role(user):
    """L'utilisateur a-t-il un rôle de membre du personnel ?"""
    return get_role(user) in STAFF_ROLES
