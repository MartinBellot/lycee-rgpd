from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Parent(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    lien = models.CharField(
        max_length=20,
        choices=[("pere", "Père"), ("mere", "Mère"), ("tuteur", "Tuteur légal")],
        default="tuteur",
    )

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_lien_display()})"


class MedecinTraitant(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)

    class Meta:
        verbose_name = "Médecin traitant"
        verbose_name_plural = "Médecins traitants"

    def __str__(self):
        return f"Dr {self.prenom} {self.nom}"


class Eleve(models.Model):
    """
    Table Identité – données d'identification de l'élève.
    RGPD : base légale = mission d'intérêt public (art. 6 §1 e).
    Accès : ensemble du personnel administratif.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    adresse = models.TextField(blank=True, verbose_name="Adresse postale")
    email = models.EmailField(blank=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    parents = models.ManyToManyField(
        Parent, blank=True, related_name="eleves", verbose_name="Parents / Tuteurs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Scolarite(models.Model):
    """
    Table Scolarité – données scolaires de l'élève.
    RGPD : base légale = mission d'intérêt public (art. 6 §1 e).
    Accès : professeurs et personnel de scolarité uniquement.
    """
    eleve = models.OneToOneField(
        Eleve, on_delete=models.CASCADE, related_name="scolarite"
    )
    classe = models.CharField(max_length=20, blank=True, verbose_name="Classe")
    options = models.TextField(blank=True, verbose_name="Options choisies")

    class Meta:
        verbose_name = "Données scolaires"
        verbose_name_plural = "Données scolaires"

    def __str__(self):
        return f"Scolarité – {self.eleve}"


class Sante(models.Model):
    """
    Table Santé – données sensibles au sens de l'art. 9 RGPD.
    Accès RESTREINT : pôle médical (allergies + médecin) et cantine (habitudes alimentaires).
    Toute consultation doit être tracée et justifiée.
    """
    eleve = models.OneToOneField(
        Eleve, on_delete=models.CASCADE, related_name="sante"
    )
    allergies = models.TextField(blank=True, verbose_name="Allergies")
    medecin = models.ForeignKey(
        MedecinTraitant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Médecin traitant",
    )
    habitudes_alimentaires = models.TextField(
        blank=True, verbose_name="Habitudes alimentaires"
    )

    class Meta:
        verbose_name = "Données de santé"
        verbose_name_plural = "Données de santé"

    def __str__(self):
        return f"Santé – {self.eleve}"


class Matiere(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Matière")
    coefficient = models.DecimalField(
        max_digits=4, decimal_places=2, default=1, verbose_name="Coefficient"
    )

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Note(models.Model):
    TRIMESTRE_CHOICES = [
        (1, "1er trimestre"),
        (2, "2e trimestre"),
        (3, "3e trimestre"),
    ]

    eleve = models.ForeignKey(
        Eleve, on_delete=models.CASCADE, related_name="notes", verbose_name="Élève"
    )
    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE, related_name="notes", verbose_name="Matière"
    )
    note = models.DecimalField(
        max_digits=4, decimal_places=2, verbose_name="Note /20"
    )
    appreciation = models.TextField(blank=True, verbose_name="Appréciation")
    trimestre = models.IntegerField(
        choices=TRIMESTRE_CHOICES, default=1, verbose_name="Trimestre"
    )
    date = models.DateField(auto_now_add=True, verbose_name="Date")

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ["trimestre", "matiere"]

    def __str__(self):
        return f"{self.eleve} – {self.matiere} T{self.trimestre} : {self.note}/20"

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ["eleve", "trimestre", "matiere"]

    def __str__(self):
        return f"{self.eleve} – {self.matiere} : {self.note}/20 (T{self.trimestre})"


# ─── Profil utilisateur (rôles RGPD) ─────────────────────────────────────────

class UserProfile(models.Model):
    from eleves.roles import ROLE_CHOICES, SCOLARITE  # imported inline to avoid circular

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="Utilisateur"
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin",        "Administrateur"),
            ("scolarite",    "Scolarité"),
            ("professeur",   "Professeur"),
            ("vie_scolaire", "Vie scolaire"),
            ("infirmier",    "Infirmier·ère"),
            ("cantine",      "Cantine"),
            ("eleve",        "Élève"),
            ("parent",       "Parent / Tuteur"),
        ],
        default="scolarite",
        verbose_name="Rôle",
    )
    # Lien pour le rôle « élève »
    eleve = models.ForeignKey(
        Eleve,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        verbose_name="Élève associé",
    )
    # Lien pour le rôle « parent » → vers le modèle Parent RGPD existant
    parent = models.ForeignKey(
        Parent,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        verbose_name="Parent associé",
    )
    # Pour le rôle « professeur »
    classe = models.CharField(
        max_length=50, blank=True, verbose_name="Classe enseignée"
    )
    matieres = models.ManyToManyField(
        Matiere, blank=True, verbose_name="Matières enseignées"
    )

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_staff_role(self):
        from eleves.roles import STAFF_ROLES
        return self.role in STAFF_ROLES


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un UserProfile pour chaque nouvel utilisateur."""
    if created:
        UserProfile.objects.get_or_create(user=instance)

