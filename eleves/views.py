from functools import wraps
import csv
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Eleve, Scolarite, Sante, Parent, MedecinTraitant, Matiere, Note, UserProfile, AuditLog, BreachReport
from .forms import (
    EleveForm, ScolariteForm, SanteForm,
    ParentForm, MedecinForm, MatiereForm, NoteForm,
    UserCreateForm, UserProfileForm,
    EleveRectifyForm, ParentRectifyForm,
    BreachReportForm,
)
from .serializers import (
    EleveSerializer,
    EleveListSerializer,
    ParentSerializer,
    MedecinTraitantSerializer,
    MatiereSerializer,
    NoteSerializer,
)
from .roles import (
    ADMIN, SCOLARITE, PROFESSEUR, VIE_SCOLAIRE, INFIRMIER, CANTINE,
    ELEVE, PARENT, STAFF_ROLES, has_role, get_role,
)
from .permissions import IsStaffRole, CanManageNotes


# ─── Helpers & decorators ─────────────────────────────────────────────────────

def _get_profile(user):
    try:
        return user.profile
    except Exception:
        return None


def _audit(request, action, target="", details=""):
    """Enregistre une action dans le journal d'audit. Ne leve jamais d'exception."""
    try:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            target=str(target)[:200],
            ip_address=ip or None,
            details=str(details)[:1000],
        )
    except Exception:
        pass


def require_roles(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = "/students/login/" if set(roles) <= {ELEVE, PARENT} else "/admin/login/"
                return redirect(f"{login_url}?next={request.path}")
            if not has_role(request.user, *roles):
                return render(request, "eleves/access_denied.html",
                              {"required": roles, "user_role": get_role(request.user)}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


staff_required = require_roles(*STAFF_ROLES)


# ─── API ViewSets ────────────────────────────────────────────────────────────

class EleveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom", "prenom", "scolarite__classe", "email"]
    ordering_fields = ["nom", "prenom"]

    def get_queryset(self):
        user = self.request.user
        role = get_role(user)
        qs = Eleve.objects.prefetch_related("parents", "notes__matiere").select_related(
            "scolarite", "sante__medecin"
        )
        if role == ELEVE:
            profile = _get_profile(user)
            return qs.filter(pk=profile.eleve_id) if profile and profile.eleve else qs.none()
        if role == PARENT:
            profile = _get_profile(user)
            return qs.filter(parents=profile.parent) if profile and profile.parent else qs.none()
        if role == PROFESSEUR:
            profile = _get_profile(user)
            return qs.filter(scolarite__classe__iexact=profile.classe) if profile else qs.none()
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return EleveListSerializer
        return EleveSerializer

    @action(detail=True, methods=["get"])
    def bulletin(self, request, pk=None):
        eleve = self.get_object()
        role = get_role(request.user)
        notes_par_trimestre = {}
        for t, label in Note.TRIMESTRE_CHOICES:
            notes = eleve.notes.filter(trimestre=t).select_related("matiere")
            if role == PROFESSEUR:
                profile = _get_profile(request.user)
                if profile:
                    notes = notes.filter(matiere__in=profile.matieres.all())
            notes_par_trimestre[label] = NoteSerializer(notes, many=True).data
        return Response({"eleve": EleveSerializer(eleve).data, "bulletin": notes_par_trimestre})


class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated, IsStaffRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom", "prenom", "email"]


class MedecinViewSet(viewsets.ModelViewSet):
    queryset = MedecinTraitant.objects.all()
    serializer_class = MedecinTraitantSerializer
    permission_classes = [IsAuthenticated, IsStaffRole]


class MatiereViewSet(viewsets.ModelViewSet):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializer
    permission_classes = [IsAuthenticated, IsStaffRole]


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, CanManageNotes]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["trimestre", "note", "date"]

    def get_queryset(self):
        qs = Note.objects.select_related("eleve", "matiere")
        role = get_role(self.request.user)
        if role == PROFESSEUR:
            profile = _get_profile(self.request.user)
            if profile:
                return qs.filter(
                    eleve__scolarite__classe__iexact=profile.classe,
                    matiere__in=profile.matieres.all(),
                )
        return qs


# ─── Custom Admin – Dashboard ────────────────────────────────────────────────

@staff_required
def dashboard(request):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    context = {
        "nb_eleves": Eleve.objects.count(),
        "nb_classes": Scolarite.objects.values("classe").exclude(classe="").distinct().count(),
        "nb_notes": Note.objects.count(),
        "derniers_eleves": Eleve.objects.select_related("scolarite").order_by("-created_at")[:5],
        "user_role": role,
    }
    if role == PROFESSEUR and profile:
        context["nb_eleves"] = Eleve.objects.filter(
            scolarite__classe__iexact=profile.classe
        ).count()
    return render(request, "eleves/dashboard.html", context)


# ─── Custom Admin – Eleves ───────────────────────────────────────────────────

@staff_required
def eleve_list(request):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    q = request.GET.get("q", "")
    classe = request.GET.get("classe", "")
    eleves = Eleve.objects.prefetch_related("parents").select_related("scolarite")
    if role == PROFESSEUR and profile:
        eleves = eleves.filter(scolarite__classe__iexact=profile.classe)
    if q:
        eleves = eleves.filter(Q(nom__icontains=q) | Q(prenom__icontains=q))
    if classe and role != PROFESSEUR:
        eleves = eleves.filter(scolarite__classe__iexact=classe)
    classes = (
        Scolarite.objects.values_list("classe", flat=True)
        .exclude(classe="")
        .distinct()
        .order_by("classe")
    )
    return render(request, "eleves/eleve_list.html", {
        "eleves": eleves, "classes": classes, "q": q, "classe": classe,
        "user_role": role,
    })


@staff_required
def eleve_detail(request, pk):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    qs = Eleve.objects.prefetch_related("parents", "notes__matiere").select_related(
        "scolarite", "sante__medecin"
    )
    if role == PROFESSEUR and profile:
        eleve = get_object_or_404(qs, pk=pk, scolarite__classe__iexact=profile.classe)
    else:
        eleve = get_object_or_404(qs, pk=pk)
    notes_par_trimestre = {}
    for t, label in Note.TRIMESTRE_CHOICES:
        notes = eleve.notes.filter(trimestre=t).select_related("matiere")
        if role == PROFESSEUR and profile:
            notes = notes.filter(matiere__in=profile.matieres.all())
        moyenne = notes.aggregate(avg=Avg("note"))["avg"]
        notes_par_trimestre[label] = {"notes": notes, "moyenne": moyenne}
    _audit(request, "access", target=f"Élève #{eleve.pk} – {eleve}")
    return render(request, "eleves/eleve_detail.html", {
        "eleve": eleve,
        "notes_par_trimestre": notes_par_trimestre,
        "user_role": role,
        "prof_matieres": profile.matieres.all() if role == PROFESSEUR and profile else None,
    })


@require_roles(ADMIN, SCOLARITE)
def eleve_create(request):
    id_form = EleveForm(request.POST or None)
    sc_form = ScolariteForm(request.POST or None)
    sa_form = SanteForm(request.POST or None)
    if request.method == "POST":
        if id_form.is_valid() and sc_form.is_valid() and sa_form.is_valid():
            eleve = id_form.save()
            scolarite = sc_form.save(commit=False)
            scolarite.eleve = eleve
            scolarite.save()
            sante = sa_form.save(commit=False)
            sante.eleve = eleve
            sante.save()
            _audit(request, "create", target=f"Élève #{eleve.pk} – {eleve}")
            messages.success(request, "Eleve cree avec succes.")
            return redirect("eleve_detail", pk=eleve.pk)
    return render(request, "eleves/eleve_form.html", {
        "id_form": id_form,
        "sc_form": sc_form,
        "sa_form": sa_form,
        "form_title": "Ajouter un eleve",
        "cancel_url": "/admin/eleves/",
        "user_role": get_role(request.user),
    })


@require_roles(ADMIN, SCOLARITE)
def eleve_edit(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    scolarite, _ = Scolarite.objects.get_or_create(eleve=eleve)
    sante, _ = Sante.objects.get_or_create(eleve=eleve)
    id_form = EleveForm(request.POST or None, instance=eleve)
    sc_form = ScolariteForm(request.POST or None, instance=scolarite)
    sa_form = SanteForm(request.POST or None, instance=sante)
    if request.method == "POST":
        if id_form.is_valid() and sc_form.is_valid() and sa_form.is_valid():
            id_form.save()
            sc_form.save()
            sa_form.save()
            _audit(request, "update", target=f"Élève #{pk}")
            messages.success(request, "Eleve mis a jour.")
            return redirect("eleve_detail", pk=pk)
    return render(request, "eleves/eleve_form.html", {
        "id_form": id_form,
        "sc_form": sc_form,
        "sa_form": sa_form,
        "form_title": f"Modifier",
        "cancel_url": f"/admin/eleves/{pk}/",
        "eleve": eleve,
        "user_role": get_role(request.user),
    })


@require_roles(ADMIN)
def eleve_delete(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == "POST":
        _audit(request, "delete", target=f"Élève #{pk} – {eleve}")
        eleve.delete()
        messages.success(request, "Eleve supprime.")
        return redirect("eleve_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": eleve,
        "delete_warning": "Toutes les donnees scolaires, de sante et les notes associees seront egalement supprimees.",
        "cancel_url": f"/admin/eleves/{pk}/",
    })


# ─── Custom Admin – Parents ──────────────────────────────────────────────────

@require_roles(ADMIN, SCOLARITE, VIE_SCOLAIRE)
def parent_list(request):
    q = request.GET.get("q", "")
    parents = Parent.objects.prefetch_related("eleves")
    if q:
        parents = parents.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q)
        )
    return render(request, "eleves/parent_list.html", {
        "parents": parents, "q": q, "user_role": get_role(request.user),
    })


@require_roles(ADMIN, SCOLARITE)
def parent_create(request):
    form = ParentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        parent = form.save()
        messages.success(request, "Parent cree.")
        return redirect("parent_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter un parent", "cancel_url": "/admin/parents/",
    })


@require_roles(ADMIN, SCOLARITE)
def parent_edit(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    form = ParentForm(request.POST or None, instance=parent)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Parent mis a jour.")
        return redirect("parent_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier", "cancel_url": "/admin/parents/",
    })


@require_roles(ADMIN, SCOLARITE)
def parent_delete(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    if request.method == "POST":
        parent.delete()
        messages.success(request, "Parent supprime.")
        return redirect("parent_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": parent, "cancel_url": "/admin/parents/",
    })


# ─── Custom Admin – Medecins ─────────────────────────────────────────────────

@require_roles(ADMIN, SCOLARITE, INFIRMIER)
def medecin_list(request):
    return render(request, "eleves/medecin_list.html", {
        "medecins": MedecinTraitant.objects.all(),
        "user_role": get_role(request.user),
    })


@require_roles(ADMIN, SCOLARITE, INFIRMIER)
def medecin_create(request):
    form = MedecinForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        m = form.save()
        messages.success(request, "Medecin cree.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter un medecin", "cancel_url": "/admin/medecins/",
    })


@require_roles(ADMIN, SCOLARITE, INFIRMIER)
def medecin_edit(request, pk):
    medecin = get_object_or_404(MedecinTraitant, pk=pk)
    form = MedecinForm(request.POST or None, instance=medecin)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Medecin mis a jour.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier", "cancel_url": "/admin/medecins/",
    })


@require_roles(ADMIN, SCOLARITE, INFIRMIER)
def medecin_delete(request, pk):
    medecin = get_object_or_404(MedecinTraitant, pk=pk)
    if request.method == "POST":
        medecin.delete()
        messages.success(request, "Medecin supprime.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": medecin, "cancel_url": "/admin/medecins/",
    })


# ─── Custom Admin – Matieres ─────────────────────────────────────────────────

@require_roles(ADMIN, SCOLARITE, PROFESSEUR)
def matiere_list(request):
    return render(request, "eleves/matiere_list.html", {
        "matieres": Matiere.objects.all(), "user_role": get_role(request.user),
    })


@require_roles(ADMIN, SCOLARITE)
def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        m = form.save()
        messages.success(request, "Matiere creee.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter une matiere", "cancel_url": "/admin/matieres/",
    })


@require_roles(ADMIN, SCOLARITE)
def matiere_edit(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    form = MatiereForm(request.POST or None, instance=matiere)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Matiere mise a jour.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier", "cancel_url": "/admin/matieres/",
    })


@require_roles(ADMIN, SCOLARITE)
def matiere_delete(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == "POST":
        matiere.delete()
        messages.success(request, "Matiere supprimee.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": matiere, "cancel_url": "/admin/matieres/",
    })


# ─── Custom Admin – Notes ────────────────────────────────────────────────────

@require_roles(ADMIN, SCOLARITE, PROFESSEUR)
def note_list(request):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    eleve_pk = request.GET.get("eleve")
    notes = Note.objects.select_related("eleve", "matiere").order_by("eleve", "trimestre")
    if role == PROFESSEUR and profile:
        notes = notes.filter(
            eleve__scolarite__classe__iexact=profile.classe,
            matiere__in=profile.matieres.all(),
        )
    eleve = None
    if eleve_pk:
        eleve = get_object_or_404(Eleve, pk=eleve_pk)
        notes = notes.filter(eleve=eleve)
    return render(request, "eleves/note_list.html", {
        "notes": notes, "eleve": eleve, "user_role": role,
    })


@require_roles(ADMIN, SCOLARITE, PROFESSEUR)
def note_create(request):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    initial = {}
    eleve_pk = request.GET.get("eleve")
    if eleve_pk:
        initial["eleve"] = eleve_pk
    form = NoteForm(request.POST or None, initial=initial)
    if role == PROFESSEUR and profile:
        form.fields["eleve"].queryset = Eleve.objects.filter(scolarite__classe__iexact=profile.classe)
        form.fields["matiere"].queryset = profile.matieres.all()
    if request.method == "POST" and form.is_valid():
        note_obj = form.save(commit=False)
        if role == PROFESSEUR and profile:
            try:
                classe_eleve = note_obj.eleve.scolarite.classe
            except Exception:
                classe_eleve = ""
            if classe_eleve.lower() != profile.classe.lower():
                messages.error(request, "Vous ne pouvez ajouter des notes que pour votre classe.")
                return redirect("eleve_list")
            if not profile.matieres.filter(pk=note_obj.matiere_id).exists():
                messages.error(request, "Vous ne pouvez ajouter des notes que pour vos matieres.")
                return redirect("eleve_list")
        note_obj.save()
        _audit(request, "create", target=f"Note – {note_obj.eleve} – {note_obj.matiere} T{note_obj.trimestre}")
        messages.success(request, "Note enregistree.")
        return redirect("eleve_detail", pk=note_obj.eleve.pk)
    cancel = f"/admin/eleves/{eleve_pk}/" if eleve_pk else "/admin/notes/"
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter une note", "cancel_url": cancel,
    })


@require_roles(ADMIN, SCOLARITE, PROFESSEUR)
def note_edit(request, pk):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    note = get_object_or_404(Note, pk=pk)
    if role == PROFESSEUR and profile:
        try:
            classe_eleve = note.eleve.scolarite.classe
        except Exception:
            classe_eleve = ""
        if (classe_eleve.lower() != profile.classe.lower()
                or not profile.matieres.filter(pk=note.matiere_id).exists()):
            return render(request, "eleves/access_denied.html",
                          {"required": [PROFESSEUR], "user_role": role}, status=403)
    form = NoteForm(request.POST or None, instance=note)
    if role == PROFESSEUR and profile:
        form.fields["eleve"].queryset = Eleve.objects.filter(scolarite__classe__iexact=profile.classe)
        form.fields["matiere"].queryset = profile.matieres.all()
    if request.method == "POST" and form.is_valid():
        form.save()
        _audit(request, "update", target=f"Note #{pk} – {note.eleve} – {note.matiere}")
        messages.success(request, "Note mise a jour.")
        return redirect("eleve_detail", pk=note.eleve.pk)
    return render(request, "eleves/admin_form.html", {
        "form": form,
        "form_title": "Modifier la note",
        "cancel_url": f"/admin/eleves/{note.eleve.pk}/",
    })


@require_roles(ADMIN, SCOLARITE, PROFESSEUR)
def note_delete(request, pk):
    role = get_role(request.user)
    profile = _get_profile(request.user)
    note = get_object_or_404(Note, pk=pk)
    if role == PROFESSEUR and profile:
        try:
            classe_eleve = note.eleve.scolarite.classe
        except Exception:
            classe_eleve = ""
        if (classe_eleve.lower() != profile.classe.lower()
                or not profile.matieres.filter(pk=note.matiere_id).exists()):
            return render(request, "eleves/access_denied.html",
                          {"required": [PROFESSEUR], "user_role": role}, status=403)
    eleve_pk = note.eleve.pk
    if request.method == "POST":
        _audit(request, "delete", target=f"Note #{pk} – {note.eleve} – {note.matiere}")
        note.delete()
        messages.success(request, "Note supprimee.")
        return redirect("eleve_detail", pk=eleve_pk)
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": note, "cancel_url": f"/admin/eleves/{eleve_pk}/",
    })


# ─── Custom Admin – Gestion des utilisateurs ─────────────────────────────────

@require_roles(ADMIN)
def user_list(request):
    from django.contrib.auth.models import User
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "eleves/user_list.html", {"users": users, "user_role": ADMIN})


@require_roles(ADMIN)
def user_create(request):
    user_form = UserCreateForm(request.POST or None)
    profile_form = UserProfileForm(request.POST or None)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user = user_form.save()
        profile = user.profile
        profile.role = profile_form.cleaned_data["role"]
        profile.eleve = profile_form.cleaned_data.get("eleve")
        profile.parent = profile_form.cleaned_data.get("parent")
        profile.classe = profile_form.cleaned_data.get("classe", "")
        profile.save()
        profile.matieres.set(profile_form.cleaned_data.get("matieres", []))
        messages.success(request, "Utilisateur cree.")
        return redirect("user_list")
    return render(request, "eleves/user_form.html", {
        "user_form": user_form, "profile_form": profile_form,
        "form_title": "Creer un utilisateur", "cancel_url": "/admin/utilisateurs/",
    })


@require_roles(ADMIN)
def user_edit(request, pk):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    user_form = UserCreateForm(request.POST or None, instance=user, edit_mode=True)
    profile_form = UserProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        pf = profile_form.save(commit=False)
        pf.user = user
        pf.save()
        profile_form.save_m2m()
        messages.success(request, "Utilisateur mis a jour.")
        return redirect("user_list")
    return render(request, "eleves/user_form.html", {
        "user_form": user_form, "profile_form": profile_form,
        "form_title": f"Modifier – {user.username}", "cancel_url": "/admin/utilisateurs/",
        "edit_user": user,
    })


@require_roles(ADMIN)
def user_delete(request, pk):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk)
    if request.user.pk == pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("user_list")
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, "Utilisateur supprime.")
        return redirect("user_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": user, "cancel_url": "/admin/utilisateurs/",
    })


# ─── Portail eleves/parents (/students/) ──────────────────────────────────────

def student_login(request):
    from django.contrib.auth import authenticate, login
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            _audit(request, "login", target=username)
            role = get_role(user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            if next_url:
                return redirect(next_url)
            if role == ELEVE:
                return redirect("student_dashboard")
            elif role == PARENT:
                return redirect("parent_dashboard")
            elif role in STAFF_ROLES:
                return redirect("/admin/")
            return redirect("/")
        else:
            error = "Identifiant ou mot de passe incorrect."
    return render(request, "students/login.html", {
        "error": error, "next": request.GET.get("next", ""),
    })


def student_logout(request):
    from django.contrib.auth import logout
    _audit(request, "logout", target=request.user.username if request.user.is_authenticated else "")
    logout(request)
    return redirect("/students/login/")


def staff_login(request):
    from django.contrib.auth import authenticate, login
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            role = get_role(user)
            if role not in STAFF_ROLES:
                error = "Ce portail est réservé au personnel du lycée."
            else:
                login(request, user)
                _audit(request, "login", target=username)
                next_url = request.POST.get("next") or request.GET.get("next", "")
                return redirect(next_url if next_url else "/admin/")
        else:
            error = "Identifiant ou mot de passe incorrect."
    return render(request, "admin/staff_login.html", {
        "error": error, "next": request.GET.get("next", ""),
    })


def staff_logout(request):
    from django.contrib.auth import logout
    _audit(request, "logout", target=request.user.username if request.user.is_authenticated else "")
    logout(request)
    return redirect("/admin/login/")


@login_required(login_url="/students/login/")
def student_portal_redirect(request):
    role = get_role(request.user)
    if role == ELEVE:
        return redirect("student_dashboard")
    elif role == PARENT:
        return redirect("parent_dashboard")
    elif role in STAFF_ROLES:
        return redirect("/admin/")
    return redirect("/students/login/")


@login_required(login_url="/students/login/")
def student_dashboard(request):
    role = get_role(request.user)
    if role != ELEVE:
        return render(request, "eleves/access_denied.html",
                      {"required": [ELEVE], "user_role": role}, status=403)
    profile = _get_profile(request.user)
    if not profile or not profile.eleve:
        return render(request, "students/eleve_dashboard.html", {"eleve": None})
    eleve = Eleve.objects.prefetch_related(
        "parents", "notes__matiere"
    ).select_related("scolarite").get(pk=profile.eleve.pk)
    notes_par_trimestre = {}
    for t, label in Note.TRIMESTRE_CHOICES:
        notes = eleve.notes.filter(trimestre=t).select_related("matiere")
        moyenne = notes.aggregate(avg=Avg("note"))["avg"]
        notes_par_trimestre[label] = {"notes": notes, "moyenne": moyenne}
    return render(request, "students/eleve_dashboard.html", {
        "eleve": eleve, "notes_par_trimestre": notes_par_trimestre,
    })


@login_required(login_url="/students/login/")
def parent_dashboard(request):
    role = get_role(request.user)
    if role != PARENT:
        return render(request, "eleves/access_denied.html",
                      {"required": [PARENT], "user_role": role}, status=403)
    profile = _get_profile(request.user)
    if not profile or not profile.parent:
        return render(request, "students/parent_dashboard.html", {"parent": None, "enfants": []})
    parent = profile.parent
    enfants = parent.eleves.prefetch_related(
        "notes__matiere"
    ).select_related("scolarite").all()
    return render(request, "students/parent_dashboard.html", {
        "parent": parent, "enfants": enfants,
    })


@login_required(login_url="/students/login/")
def parent_child_notes(request, pk):
    role = get_role(request.user)
    if role != PARENT:
        return render(request, "eleves/access_denied.html",
                      {"required": [PARENT], "user_role": role}, status=403)
    profile = _get_profile(request.user)
    if not profile or not profile.parent:
        return redirect("parent_dashboard")
    eleve = get_object_or_404(profile.parent.eleves, pk=pk)
    eleve = Eleve.objects.prefetch_related("notes__matiere").select_related("scolarite").get(pk=eleve.pk)
    notes_par_trimestre = {}
    for t, label in Note.TRIMESTRE_CHOICES:
        notes = eleve.notes.filter(trimestre=t).select_related("matiere")
        moyenne = notes.aggregate(avg=Avg("note"))["avg"]
        notes_par_trimestre[label] = {"notes": notes, "moyenne": moyenne}
    return render(request, "students/child_bulletin.html", {
        "eleve": eleve, "notes_par_trimestre": notes_par_trimestre,
        "parent": profile.parent,
    })


# ─── Droits RGPD (Art. 15, 16, 17, 20) ──────────────────────────────────────

def _build_rgpd_payload(user):
    """Construit le jeu de données complet pour les droits d'accès et portabilité."""
    role = get_role(user)
    profile = _get_profile(user)

    payload = {
        "export_date": timezone.now().date().isoformat(),
        "role": role,
        "compte": {
            "username": user.username,
            "email": user.email,
            "prenom": user.first_name,
            "nom": user.last_name,
            "date_creation_compte": user.date_joined.date().isoformat(),
        },
    }

    if role == ELEVE and profile and profile.eleve:
        eleve = (
            Eleve.objects
            .prefetch_related("notes__matiere", "parents")
            .select_related("scolarite", "sante__medecin")
            .get(pk=profile.eleve.pk)
        )
        payload["identite"] = {
            "nom": eleve.nom,
            "prenom": eleve.prenom,
            "date_naissance": eleve.date_naissance.isoformat() if eleve.date_naissance else None,
            "email": eleve.email,
            "telephone": eleve.telephone,
            "adresse": eleve.adresse,
        }
        try:
            payload["scolarite"] = {
                "classe": eleve.scolarite.classe,
                "options": eleve.scolarite.options,
            }
        except Exception:
            payload["scolarite"] = {}
        payload["notes"] = [
            {
                "matiere": n.matiere.nom,
                "coefficient": float(n.matiere.coefficient),
                "trimestre": n.trimestre,
                "note": float(n.note),
                "appreciation": n.appreciation,
                "date": n.date.isoformat(),
            }
            for n in eleve.notes.select_related("matiere").order_by("trimestre", "matiere__nom")
        ]

    elif role == PARENT and profile and profile.parent:
        parent = profile.parent
        payload["contact"] = {
            "nom": parent.nom,
            "prenom": parent.prenom,
            "lien": parent.get_lien_display(),
            "email": parent.email,
            "telephone": parent.telephone,
        }
        payload["enfants"] = [
            {
                "nom": e.nom,
                "prenom": e.prenom,
                "classe": e.scolarite.classe if hasattr(e, "scolarite") else "",
            }
            for e in parent.eleves.select_related("scolarite").all()
        ]

    return payload


@login_required(login_url="/students/login/")
def rgpd_access(request):
    """Art. 15 RGPD – Droit d'accès aux données."""
    role = get_role(request.user)
    if role not in (ELEVE, PARENT):
        return render(request, "eleves/access_denied.html",
                      {"required": [ELEVE, PARENT], "user_role": role}, status=403)
    payload = _build_rgpd_payload(request.user)
    return render(request, "students/rgpd_access.html", {"payload": payload, "role": role})


@login_required(login_url="/students/login/")
def rgpd_rectify(request):
    """Art. 16 RGPD – Droit de rectification des données de contact."""
    role = get_role(request.user)
    profile = _get_profile(request.user)

    if role == ELEVE:
        if not profile or not profile.eleve:
            messages.error(request, "Aucun profil eleve associe a ce compte.")
            return redirect("student_dashboard")
        form = EleveRectifyForm(request.POST or None, instance=profile.eleve)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Vos coordonnees ont ete mises a jour.")
            return redirect("rgpd_access")
        return render(request, "students/rgpd_rectify.html", {"form": form, "role": role})

    elif role == PARENT:
        if not profile or not profile.parent:
            messages.error(request, "Aucun profil parent associe a ce compte.")
            return redirect("parent_dashboard")
        form = ParentRectifyForm(request.POST or None, instance=profile.parent)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Vos coordonnees ont ete mises a jour.")
            return redirect("rgpd_access")
        return render(request, "students/rgpd_rectify.html", {"form": form, "role": role})

    return render(request, "eleves/access_denied.html",
                  {"required": [ELEVE, PARENT], "user_role": role}, status=403)


@login_required(login_url="/students/login/")
def rgpd_erase(request):
    """Art. 17 RGPD – Droit à l'effacement du compte utilisateur."""
    role = get_role(request.user)
    if role not in (ELEVE, PARENT):
        return render(request, "eleves/access_denied.html",
                      {"required": [ELEVE, PARENT], "user_role": role}, status=403)

    error = None
    if request.method == "POST":
        password = request.POST.get("password", "")
        if request.user.check_password(password):
            from django.contrib.auth import logout as auth_logout
            username = request.user.username
            _audit(request, "erase", target=username, details="Effacement Art. 17 RGPD")
            user = request.user
            auth_logout(request)
            user.delete()
            return redirect("/students/login/?effacement=ok")
        else:
            error = "Mot de passe incorrect."

    return render(request, "students/rgpd_erase.html", {"role": role, "error": error})


@login_required(login_url="/students/login/")
def rgpd_export(request):
    """Art. 20 RGPD – Droit à la portabilité : export JSON ou CSV."""
    role = get_role(request.user)
    if role not in (ELEVE, PARENT):
        return render(request, "eleves/access_denied.html",
                      {"required": [ELEVE, PARENT], "user_role": role}, status=403)

    fmt = request.GET.get("format", "json").lower()
    if fmt not in ("json", "csv"):
        fmt = "json"

    _audit(request, "export", target=request.user.username, details=f"Format: {fmt}")
    payload = _build_rgpd_payload(request.user)
    filename_base = f"mes_donnees_{request.user.username}_{timezone.now().date().isoformat()}"

    if fmt == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)

        if role == ELEVE:
            identite = payload.get("identite", {})
            scolarite = payload.get("scolarite", {})
            writer.writerow(["Section", "Champ", "Valeur"])
            for champ, valeur in [
                ("Nom", identite.get("nom", "")),
                ("Prenom", identite.get("prenom", "")),
                ("Date de naissance", identite.get("date_naissance", "")),
                ("Email", identite.get("email", "")),
                ("Telephone", identite.get("telephone", "")),
                ("Adresse", identite.get("adresse", "")),
            ]:
                writer.writerow(["Identite", champ, valeur])
            writer.writerow(["Scolarite", "Classe", scolarite.get("classe", "")])
            writer.writerow(["Scolarite", "Options", scolarite.get("options", "")])
            writer.writerow([])
            writer.writerow(["Notes", "Matiere", "Coefficient", "Trimestre", "Note /20", "Appreciation", "Date"])
            for n in payload.get("notes", []):
                writer.writerow(["Notes", n["matiere"], n["coefficient"], n["trimestre"],
                                  n["note"], n["appreciation"], n["date"]])

        elif role == PARENT:
            contact = payload.get("contact", {})
            writer.writerow(["Section", "Champ", "Valeur"])
            for champ, valeur in [
                ("Nom", contact.get("nom", "")),
                ("Prenom", contact.get("prenom", "")),
                ("Lien", contact.get("lien", "")),
                ("Email", contact.get("email", "")),
                ("Telephone", contact.get("telephone", "")),
            ]:
                writer.writerow(["Contact", champ, valeur])
            writer.writerow([])
            writer.writerow(["Enfants", "Nom", "Prenom", "Classe"])
            for e in payload.get("enfants", []):
                writer.writerow(["Enfants", e["nom"], e["prenom"], e["classe"]])

        return response

    # JSON (default)
    response = HttpResponse(
        json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename_base}.json"'
    return response


# ─── DPO Contact (public) ─────────────────────────────────────────────────────

def dpo_contact(request):
    """Page de contact du Délégué à la Protection des Données (DPO). Accès public."""
    return render(request, "shared/dpo_contact.html")


# ─── Signalement de violation de données (tous utilisateurs authentifiés) ────

def breach_report(request):
    """Permet à tout utilisateur (authentifié ou non) de signaler une violation de données."""
    role = get_role(request.user) if request.user.is_authenticated else None
    submitted = False

    if request.method == "POST":
        form = BreachReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.reporter = request.user
            report.save()
            if request.user.is_authenticated:
                _audit(request, "breach_report",
                       target=f"Signalement #{report.pk}",
                       details=form.cleaned_data["description"][:300])
            submitted = True
            form = None
    else:
        form = BreachReportForm()

    return render(request, "shared/breach_report.html", {
        "form": form,
        "submitted": submitted,
        "role": role,
    })


# ─── Journal d'audit (admin uniquement) ──────────────────────────────────────

@require_roles(ADMIN)
def audit_log_list(request):
    """Journal d'audit complet – réservé aux administrateurs."""
    action_filter = request.GET.get("action", "")
    username_filter = request.GET.get("username", "").strip()

    logs = AuditLog.objects.select_related("user").order_by("-timestamp")
    if action_filter:
        logs = logs.filter(action=action_filter)
    if username_filter:
        logs = logs.filter(user__username__icontains=username_filter)
    logs = logs[:500]

    return render(request, "admin/audit_log.html", {
        "logs": logs,
        "action_choices": AuditLog.ACTION_CHOICES,
        "action_filter": action_filter,
        "username_filter": username_filter,
        "user_role": ADMIN,
        "total": len(logs),
    })


@require_roles(ADMIN)
def breach_report_list(request):
    """Liste des signalements de violation – réservée aux administrateurs."""
    status_filter = request.GET.get("status", "")
    reports = BreachReport.objects.select_related("reporter").order_by("-submitted_at")
    if status_filter:
        reports = reports.filter(status=status_filter)

    if request.method == "POST":
        pk = request.POST.get("pk")
        new_status = request.POST.get("status")
        admin_notes = request.POST.get("admin_notes", "")
        if pk and new_status in dict(BreachReport.STATUS_CHOICES):
            rpt = get_object_or_404(BreachReport, pk=pk)
            rpt.status = new_status
            rpt.admin_notes = admin_notes
            rpt.save()
            _audit(request, "update", target=f"Signalement #{pk}",
                   details=f"Statut → {new_status}")
            messages.success(request, "Signalement mis à jour.")
            return redirect("breach_report_list")

    return render(request, "admin/breach_reports.html", {
        "reports": reports,
        "status_choices": BreachReport.STATUS_CHOICES,
        "status_filter": status_filter,
        "user_role": ADMIN,
    })


