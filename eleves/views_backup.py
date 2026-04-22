from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Avg, Q
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Eleve, Scolarite, Sante, Parent, MedecinTraitant, Matiere, Note
from .forms import EleveForm, ScolariteForm, SanteForm, ParentForm, MedecinForm, MatiereForm, NoteForm
from .serializers import (
    EleveSerializer,
    EleveListSerializer,
    ParentSerializer,
    MedecinTraitantSerializer,
    MatiereSerializer,
    NoteSerializer,
)

staff_required = user_passes_test(lambda u: u.is_staff, login_url="/django-admin/login/")


# ─── API ViewSets ────────────────────────────────────────────────────────────

class EleveViewSet(viewsets.ModelViewSet):
    queryset = Eleve.objects.prefetch_related(
        "parents", "notes__matiere"
    ).select_related("scolarite", "sante__medecin")
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom", "prenom", "scolarite__classe", "email"]
    ordering_fields = ["nom", "prenom", "scolarite__classe"]

    def get_serializer_class(self):
        if self.action == "list":
            return EleveListSerializer
        return EleveSerializer

    @action(detail=True, methods=["get"])
    def bulletin(self, request, pk=None):
        eleve = self.get_object()
        notes_par_trimestre = {}
        for t, label in Note.TRIMESTRE_CHOICES:
            notes = eleve.notes.filter(trimestre=t).select_related("matiere")
            notes_par_trimestre[label] = NoteSerializer(notes, many=True).data
        return Response({"eleve": EleveSerializer(eleve).data, "bulletin": notes_par_trimestre})


class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom", "prenom", "email"]


class MedecinViewSet(viewsets.ModelViewSet):
    queryset = MedecinTraitant.objects.all()
    serializer_class = MedecinTraitantSerializer
    permission_classes = [IsAuthenticated]


class MatiereViewSet(viewsets.ModelViewSet):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializer
    permission_classes = [IsAuthenticated]


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.select_related("eleve", "matiere")
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["trimestre", "note", "date"]
    filterset_fields = ["eleve", "matiere", "trimestre"]


# ─── Custom Admin – Dashboard ────────────────────────────────────────────────

@staff_required
def dashboard(request):
    context = {
        "nb_eleves": Eleve.objects.count(),
        "nb_classes": Scolarite.objects.values("classe").exclude(classe="").distinct().count(),
        "nb_notes": Note.objects.count(),
        "derniers_eleves": Eleve.objects.select_related("scolarite").order_by("-created_at")[:5],
    }
    return render(request, "eleves/dashboard.html", context)


# ─── Custom Admin – Élèves ───────────────────────────────────────────────────

@staff_required
def eleve_list(request):
    q = request.GET.get("q", "")
    classe = request.GET.get("classe", "")
    eleves = Eleve.objects.prefetch_related("parents").select_related("scolarite")
    if q:
        eleves = eleves.filter(Q(nom__icontains=q) | Q(prenom__icontains=q))
    if classe:
        eleves = eleves.filter(scolarite__classe__iexact=classe)
    classes = (
        Scolarite.objects.values_list("classe", flat=True)
        .exclude(classe="")
        .distinct()
        .order_by("classe")
    )
    return render(request, "eleves/eleve_list.html", {
        "eleves": eleves, "classes": classes, "q": q, "classe": classe,
    })


@staff_required
def eleve_detail(request, pk):
    eleve = get_object_or_404(
        Eleve.objects.prefetch_related("parents", "notes__matiere").select_related(
            "scolarite", "sante__medecin"
        ),
        pk=pk,
    )
    notes_par_trimestre = {}
    for t, label in Note.TRIMESTRE_CHOICES:
        notes = eleve.notes.filter(trimestre=t).select_related("matiere")
        moyenne = notes.aggregate(avg=Avg("note"))["avg"]
        notes_par_trimestre[label] = {"notes": notes, "moyenne": moyenne}
    return render(request, "eleves/eleve_detail.html", {
        "eleve": eleve,
        "notes_par_trimestre": notes_par_trimestre,
    })


@staff_required
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
            messages.success(request, f"Élève « {eleve} » créé avec succès.")
            return redirect("eleve_detail", pk=eleve.pk)
    return render(request, "eleves/eleve_form.html", {
        "id_form": id_form,
        "sc_form": sc_form,
        "sa_form": sa_form,
        "form_title": "Ajouter un élève",
        "cancel_url": "/admin/eleves/",
    })


@staff_required
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
            messages.success(request, f"Élève « {eleve} » mis à jour.")
            return redirect("eleve_detail", pk=pk)
    return render(request, "eleves/eleve_form.html", {
        "id_form": id_form,
        "sc_form": sc_form,
        "sa_form": sa_form,
        "form_title": f"Modifier – {eleve}",
        "cancel_url": f"/admin/eleves/{pk}/",
        "eleve": eleve,
    })


@staff_required
def eleve_delete(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == "POST":
        nom = str(eleve)
        eleve.delete()
        messages.success(request, f"Élève « {nom} » supprimé.")
        return redirect("eleve_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": eleve,
        "delete_warning": "Toutes les données scolaires, de santé et les notes associées seront également supprimées.",
        "cancel_url": f"/admin/eleves/{pk}/",
    })


# ─── Custom Admin – Parents ──────────────────────────────────────────────────

@staff_required
def parent_list(request):
    q = request.GET.get("q", "")
    parents = Parent.objects.prefetch_related("eleves")
    if q:
        parents = parents.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q)
        )
    return render(request, "eleves/parent_list.html", {"parents": parents, "q": q})


@staff_required
def parent_create(request):
    form = ParentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        parent = form.save()
        messages.success(request, f"Parent « {parent} » créé.")
        return redirect("parent_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter un parent", "cancel_url": "/admin/parents/",
    })


@staff_required
def parent_edit(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    form = ParentForm(request.POST or None, instance=parent)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Parent « {parent} » mis à jour.")
        return redirect("parent_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier – {parent}", "cancel_url": "/admin/parents/",
    })


@staff_required
def parent_delete(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    if request.method == "POST":
        nom = str(parent)
        parent.delete()
        messages.success(request, f"Parent « {nom} » supprimé.")
        return redirect("parent_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": parent, "cancel_url": "/admin/parents/",
    })


# ─── Custom Admin – Médecins ─────────────────────────────────────────────────

@staff_required
def medecin_list(request):
    medecins = MedecinTraitant.objects.all()
    return render(request, "eleves/medecin_list.html", {"medecins": medecins})


@staff_required
def medecin_create(request):
    form = MedecinForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        m = form.save()
        messages.success(request, f"Médecin « {m} » créé.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter un médecin", "cancel_url": "/admin/medecins/",
    })


@staff_required
def medecin_edit(request, pk):
    medecin = get_object_or_404(MedecinTraitant, pk=pk)
    form = MedecinForm(request.POST or None, instance=medecin)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Médecin « {medecin} » mis à jour.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier – {medecin}", "cancel_url": "/admin/medecins/",
    })


@staff_required
def medecin_delete(request, pk):
    medecin = get_object_or_404(MedecinTraitant, pk=pk)
    if request.method == "POST":
        nom = str(medecin)
        medecin.delete()
        messages.success(request, f"Médecin « {nom} » supprimé.")
        return redirect("medecin_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": medecin, "cancel_url": "/admin/medecins/",
    })


# ─── Custom Admin – Matières ─────────────────────────────────────────────────

@staff_required
def matiere_list(request):
    matieres = Matiere.objects.all()
    return render(request, "eleves/matiere_list.html", {"matieres": matieres})


@staff_required
def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        m = form.save()
        messages.success(request, f"Matière « {m} » créée.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter une matière", "cancel_url": "/admin/matieres/",
    })


@staff_required
def matiere_edit(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    form = MatiereForm(request.POST or None, instance=matiere)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Matière « {matiere} » mise à jour.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": f"Modifier – {matiere}", "cancel_url": "/admin/matieres/",
    })


@staff_required
def matiere_delete(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == "POST":
        nom = str(matiere)
        matiere.delete()
        messages.success(request, f"Matière « {nom} » supprimée.")
        return redirect("matiere_list")
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": matiere, "cancel_url": "/admin/matieres/",
    })


# ─── Custom Admin – Notes ────────────────────────────────────────────────────

@staff_required
def note_list(request):
    eleve_pk = request.GET.get("eleve")
    notes = Note.objects.select_related("eleve", "matiere").order_by("eleve", "trimestre")
    eleve = None
    if eleve_pk:
        eleve = get_object_or_404(Eleve, pk=eleve_pk)
        notes = notes.filter(eleve=eleve)
    return render(request, "eleves/note_list.html", {"notes": notes, "eleve": eleve})


@staff_required
def note_create(request):
    initial = {}
    eleve_pk = request.GET.get("eleve")
    if eleve_pk:
        initial["eleve"] = eleve_pk
    form = NoteForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        note = form.save()
        messages.success(request, "Note enregistrée.")
        return redirect("eleve_detail", pk=note.eleve.pk)
    cancel = f"/admin/eleves/{eleve_pk}/" if eleve_pk else "/admin/notes/"
    return render(request, "eleves/admin_form.html", {
        "form": form, "form_title": "Ajouter une note", "cancel_url": cancel,
    })


@staff_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)
    form = NoteForm(request.POST or None, instance=note)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Note mise à jour.")
        return redirect("eleve_detail", pk=note.eleve.pk)
    return render(request, "eleves/admin_form.html", {
        "form": form,
        "form_title": f"Modifier la note – {note}",
        "cancel_url": f"/admin/eleves/{note.eleve.pk}/",
    })


@staff_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    eleve_pk = note.eleve.pk
    if request.method == "POST":
        note.delete()
        messages.success(request, "Note supprimée.")
        return redirect("eleve_detail", pk=eleve_pk)
    return render(request, "eleves/admin_confirm_delete.html", {
        "object": note, "cancel_url": f"/admin/eleves/{eleve_pk}/",
    })
