from django import forms
from django.contrib.auth.models import User
from .models import Eleve, Scolarite, Sante, Parent, MedecinTraitant, Matiere, Note, UserProfile, BreachReport


class StyledFormMixin:
    """Ajoute des classes CSS à tous les widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxSelectMultiple):
                w.attrs.setdefault("class", "form-check-list")
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault("class", "form-textarea")
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "form-select")
            else:
                w.attrs.setdefault("class", "form-control")


class EleveForm(StyledFormMixin, forms.ModelForm):
    """Formulaire pour les données d'identité (table eleves_eleve)."""

    class Meta:
        model = Eleve
        fields = [
            "nom", "prenom", "date_naissance",
            "adresse", "email", "telephone",
            "parents",
        ]
        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "adresse": forms.Textarea(attrs={"rows": 3}),
            "parents": forms.CheckboxSelectMultiple(),
        }


class ScolariteForm(StyledFormMixin, forms.ModelForm):
    """Formulaire pour les données scolaires (table eleves_scolarite)."""

    class Meta:
        model = Scolarite
        fields = ["classe", "options"]
        widgets = {
            "options": forms.Textarea(attrs={"rows": 2}),
        }


class SanteForm(StyledFormMixin, forms.ModelForm):
    """Formulaire pour les données de santé sensibles (table eleves_sante)."""

    class Meta:
        model = Sante
        fields = ["allergies", "medecin", "habitudes_alimentaires"]
        widgets = {
            "allergies": forms.Textarea(attrs={"rows": 2}),
            "habitudes_alimentaires": forms.Textarea(attrs={"rows": 2}),
        }


class ParentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Parent
        fields = ["nom", "prenom", "lien", "telephone", "email"]


class MedecinForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = MedecinTraitant
        fields = ["nom", "prenom", "telephone", "adresse"]
        widgets = {
            "adresse": forms.Textarea(attrs={"rows": 3}),
        }


class MatiereForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ["nom", "coefficient"]


class NoteForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Note
        fields = ["eleve", "matiere", "trimestre", "note", "appreciation"]
        widgets = {
            "appreciation": forms.Textarea(attrs={"rows": 2}),
        }


# ─── Gestion des utilisateurs ─────────────────────────────────────────────────

class UserCreateForm(StyledFormMixin, forms.ModelForm):
    """Crée ou modifie un utilisateur Django."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Mot de passe",
        required=False,
        help_text="Laissez vide pour conserver le mot de passe actuel (en mode édition).",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirmer le mot de passe",
        required=False,
    )

    def __init__(self, *args, edit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_mode = edit_mode
        if not edit_mode:
            self.fields["password"].required = True
            self.fields["password_confirm"].required = True

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserProfileForm(StyledFormMixin, forms.ModelForm):
    """Édite le profil (rôle + liens) d'un utilisateur."""

    class Meta:
        model = UserProfile
        fields = ["role", "eleve", "parent", "classe", "matieres"]
        widgets = {
            "matieres": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["eleve"].required = False
        self.fields["parent"].required = False
        self.fields["classe"].required = False
        self.fields["matieres"].required = False


# ─── Droits RGPD – Rectification ─────────────────────────────────────────────

class EleveRectifyForm(StyledFormMixin, forms.ModelForm):
    """Permet à un élève de rectifier ses données de contact (Art. 16 RGPD)."""

    class Meta:
        model = Eleve
        fields = ["email", "telephone", "adresse"]
        widgets = {
            "adresse": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "email": "Adresse e-mail",
            "telephone": "Téléphone",
            "adresse": "Adresse postale",
        }


class ParentRectifyForm(StyledFormMixin, forms.ModelForm):
    """Permet à un parent de rectifier ses données de contact (Art. 16 RGPD)."""

    class Meta:
        model = Parent
        fields = ["email", "telephone"]
        labels = {
            "email": "Adresse e-mail",
            "telephone": "Téléphone",
        }


class BreachReportForm(StyledFormMixin, forms.ModelForm):
    """Formulaire de signalement d'une violation de données personnelles."""

    class Meta:
        model = BreachReport
        fields = ["description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "Décrivez ce que vous avez observé : date approximative, type de données concernées, comment vous l'avez découvert...",
            }),
        }
        labels = {
            "description": "Description de ce que vous avez observé",
        }
        help_texts = {
            "description": "Toutes les informations que vous pouvez fournir nous aideront à traiter votre signalement rapidement.",
        }
