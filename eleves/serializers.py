from rest_framework import serializers
from .models import Eleve, Scolarite, Sante, Parent, MedecinTraitant, Matiere, Note


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"


class MedecinTraitantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedecinTraitant
        fields = "__all__"


class MatiereSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matiere
        fields = "__all__"


class NoteSerializer(serializers.ModelSerializer):
    matiere_nom = serializers.CharField(source="matiere.nom", read_only=True)
    trimestre_display = serializers.CharField(source="get_trimestre_display", read_only=True)

    class Meta:
        model = Note
        fields = "__all__"


class ScolariteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scolarite
        fields = ["classe", "options"]


class SanteSerializer(serializers.ModelSerializer):
    medecin = MedecinTraitantSerializer(read_only=True)

    class Meta:
        model = Sante
        fields = ["allergies", "medecin", "habitudes_alimentaires"]


class EleveSerializer(serializers.ModelSerializer):
    parents = ParentSerializer(many=True, read_only=True)
    scolarite = ScolariteSerializer(read_only=True)
    sante = SanteSerializer(read_only=True)
    notes = NoteSerializer(many=True, read_only=True)

    class Meta:
        model = Eleve
        fields = "__all__"


class EleveListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes."""
    classe = serializers.CharField(source="scolarite.classe", read_only=True, default="")

    class Meta:
        model = Eleve
        fields = ["id", "nom", "prenom", "classe", "email", "telephone"]
