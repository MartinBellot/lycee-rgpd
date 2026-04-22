from django.contrib import admin
from django.db.models import Avg
from django.utils.html import format_html
from lycee.admin_site import lycee_admin_site
from .models import Eleve, Scolarite, Sante, Parent, MedecinTraitant, Matiere, Note


class ScolariteInline(admin.StackedInline):
    model = Scolarite
    can_delete = False
    verbose_name_plural = "📚 Données scolaires (Accès : Professeurs & Scolarité)"
    fields = ("classe", "options")


class SanteInline(admin.StackedInline):
    model = Sante
    can_delete = False
    verbose_name_plural = "🏥 Données de santé — RGPD art. 9 (Accès restreint : Pôle médical & Cantine)"
    fields = ("allergies", "medecin", "habitudes_alimentaires")


class NoteInline(admin.TabularInline):
    model = Note
    extra = 1
    fields = ("matiere", "trimestre", "note", "appreciation")
    autocomplete_fields = ["matiere"]


class EleveAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "get_classe", "email", "telephone", "moyenne_generale")
    list_filter = ()
    search_fields = ("nom", "prenom", "email")
    filter_horizontal = ("parents",)
    inlines = [ScolariteInline, SanteInline, NoteInline]
    fieldsets = (
        ("🪪 Identité", {"fields": ("nom", "prenom", "date_naissance")}),
        ("📞 Coordonnées", {"fields": ("adresse", "email", "telephone")}),
        ("👨‍👩‍👧 Informations familiales", {"fields": ("parents",)}),
    )

    @admin.display(description="Classe")
    def get_classe(self, obj):
        try:
            return obj.scolarite.classe or "–"
        except Scolarite.DoesNotExist:
            return "–"

    @admin.display(description="Moyenne générale")
    def moyenne_generale(self, obj):
        avg = obj.notes.aggregate(avg=Avg("note"))["avg"]
        if avg is None:
            return "–"
        color = "green" if avg >= 10 else "red"
        return format_html('<span style="color:{}">{:.2f}/20</span>', color, avg)


class ParentAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "lien", "telephone", "email")
    search_fields = ("nom", "prenom", "email")
    list_filter = ("lien",)


class MedecinAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "telephone")
    search_fields = ("nom", "prenom")


class MatiereAdmin(admin.ModelAdmin):
    list_display = ("nom", "coefficient")
    search_fields = ("nom",)


class NoteAdmin(admin.ModelAdmin):
    list_display = ("eleve", "matiere", "trimestre", "note", "appreciation")
    list_filter = ("trimestre", "matiere")
    search_fields = ("eleve__nom", "eleve__prenom", "matiere__nom")
    autocomplete_fields = ["matiere"]


# Register everything on the custom admin site only (not admin.site)
lycee_admin_site.register(Eleve, EleveAdmin)
lycee_admin_site.register(Parent, ParentAdmin)
lycee_admin_site.register(MedecinTraitant, MedecinAdmin)
lycee_admin_site.register(Matiere, MatiereAdmin)
lycee_admin_site.register(Note, NoteAdmin)
