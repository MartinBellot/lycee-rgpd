
# Lycée RGPD – Gestion des élèves

Application Django de gestion des données d'un lycée, conçue en TOTALE conformité avec le RGPD.

---

## Stack technique

| Composant | Version |
|---|---|
| Python | 3.10 |
| Django | 5.2 |
| Django REST Framework | 3.17 |
| Base de données | SQLite (fichier `db.sqlite3`) |

---

## Lancer le serveur

```bash
cd /Users/martinbellot/Desktop/PROG/SUP/RGPD
source .venv/bin/activate
python manage.py runserver
```

Accès : http://127.0.0.1:8000

---

## Architecture RGPD – Séparation des données

Les données de chaque élève sont réparties dans **trois tables distinctes** selon le principe de minimisation :

| Table | Contenu | Sensibilité |
|---|---|---|
| `eleves_eleve` | Identité (nom, prénom, date de naissance) | Standard |
| `eleves_scolarite` | Classe, niveau, options | Standard |
| `eleves_sante` | Allergies, régime, médecin traitant | Sensible (Art. 9 RGPD) |

Seul le personnel habilité accède aux données de santé (admin, scolarité, infirmier, cantine limité aux habitudes alimentaires).

---

## Système de rôles (RBAC)

Huit rôles définis dans `eleves/roles.py` :

| Rôle | Constante | Type | Portail |
|---|---|---|---|
| Administrateur | `admin` | Staff | `/admin/` + `/django-admin/` |
| Scolarité | `scolarite` | Staff | `/admin/` |
| Professeur | `professeur` | Staff | `/admin/` (sa classe uniquement) |
| Vie scolaire | `vie_scolaire` | Staff | `/admin/` |
| Infirmier·ère | `infirmier` | Staff | `/admin/` |
| Cantine | `cantine` | Staff | `/admin/` |
| Élève | `eleve` | Étudiant | `/students/dashboard/` |
| Parent | `parent` | Étudiant | `/students/parent/` |

---

## Matrice des droits

| Action | admin | scolarite | professeur | vie_scolaire | infirmier | cantine | eleve | parent |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Dashboard `/admin/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Liste élèves | ✅ | ✅ | ✅ (sa classe) | ✅ | ✅ | ✅ | ❌ | ❌ |
| Créer / modifier élève | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Supprimer élève | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Données scolaires (lecture) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Données de santé complètes | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Habitudes alimentaires | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Notes – lecture | ✅ | ✅ | ✅ (sa classe + ses matières) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Notes – créer / modifier / supprimer | ✅ | ✅ | ✅ (sa classe + ses matières) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Parents (lecture) | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Parents – créer / modifier / supprimer | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Médecins traitants CRUD | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Matières – lecture | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Matières – créer / modifier / supprimer | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gestion des utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `/django-admin/` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Portail élève `/students/dashboard/` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (ses notes) | ❌ |
| Portail parent `/students/parent/` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (ses enfants) |

---

## Comptes de démonstration

### Portail staff — http://127.0.0.1:8000/admin/

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| `admin` | `admin123` | Administrateur (accès total + `/django-admin/`) |
| `scolarite` | `scolarite123` | Scolarité |
| `prof.dupont` | `prof123` | Professeur – Terminale S (Maths, Physique-Chimie) |
| `viescolaire` | `vs123` | Vie scolaire |
| `infirmerie` | `inf123` | Infirmier·ère |
| `cantine` | `cantine123` | Cantine |

### Portail élèves/parents — http://127.0.0.1:8000/students/login/

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| `lucas.eleve` | `eleve123` | Élève (Hugo Bernard) |
| `emma.eleve` | `eleve123` | Élève (Lucas Durand) |
| `marie.parent` | `parent123` | Parent (Marie Durand) |

---

## URLs principales

### Portail staff

| URL | Description |
|---|---|
| `/admin/` | Tableau de bord staff |
| `/admin/eleves/` | Liste des élèves |
| `/admin/eleves/<pk>/` | Fiche élève |
| `/admin/eleves/new/` | Créer un élève |
| `/admin/eleves/<pk>/edit/` | Modifier un élève |
| `/admin/eleves/<pk>/delete/` | Supprimer un élève |
| `/admin/parents/` | Liste des parents |
| `/admin/medecins/` | Liste des médecins traitants |
| `/admin/matieres/` | Liste des matières |
| `/admin/notes/` | Liste des notes |
| `/admin/utilisateurs/` | Gestion des comptes (admin seulement) |
| `/django-admin/` | Interface admin Django native (admin seulement) |

### Portail élèves/parents

| URL | Description |
|---|---|
| `/students/login/` | Connexion élève/parent |
| `/students/logout/` | Déconnexion |
| `/students/dashboard/` | Tableau de bord élève (notes par trimestre) |
| `/students/parent/` | Tableau de bord parent (liste des enfants) |
| `/students/parent/eleve/<pk>/` | Bulletin d'un enfant |
| `/students/rgpd/` | Mes données (Art. 15 – Droit d'accès) |
| `/students/rgpd/rectifier/` | Corriger mes coordonnées (Art. 16 – Rectification) |
| `/students/rgpd/effacer/` | Supprimer mon compte (Art. 17 – Droit à l'effacement) |
| `/students/rgpd/exporter/?format=json` | Export JSON (Art. 20 – Portabilité) |
| `/students/rgpd/exporter/?format=csv` | Export CSV (Art. 20 – Portabilité) |

### API REST

| URL | Description |
|---|---|
| `/api/eleves/` | Liste/détail élèves (JSON) |
| `/api/parents/` | Liste/détail parents (JSON) |
| `/api/medecins/` | Liste/détail médecins (JSON) |
| `/api/matieres/` | Liste/détail matières (JSON) |
| `/api/notes/` | Liste/détail notes (JSON) |

---

## Structure du projet

```
RGPD/
├── lycee/
│   ├── settings.py          # Configuration Django
│   ├── urls.py              # Routage principal
│   └── admin_site.py        # LyceeAdminSite (accès restreint admin)
├── eleves/
│   ├── models.py            # Eleve, Scolarite, Sante, Parent, Matiere, Note, UserProfile
│   ├── roles.py             # Constantes de rôles + helpers
│   ├── permissions.py       # Classes de permission DRF
│   ├── forms.py             # Formulaires métier + UserCreateForm + UserProfileForm
│   ├── views.py             # Toutes les vues (staff + students portal)
│   ├── serializers.py       # Sérialiseurs DRF
│   ├── urls.py              # Toutes les routes
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_add_user_profile.py
└── templates/
    ├── base.html            # Layout staff (navbar role-aware)
    ├── eleves/              # Templates portail staff
    │   ├── dashboard.html
    │   ├── eleve_list.html
    │   ├── eleve_detail.html   # Conditionnel selon le rôle
    │   ├── access_denied.html
    │   ├── user_list.html
    │   └── user_form.html
    └── students/            # Templates portail élèves/parents
        ├── base.html
        ├── login.html
        ├── eleve_dashboard.html
        ├── parent_dashboard.html
        └── child_bulletin.html
```

---

## Conformité RGPD

| Principe | Implémentation |
|---|---|
| **Minimisation** | 3 tables séparées ; chaque rôle n'accède qu'aux données nécessaires |
| **Contrôle d'accès** | RBAC via `UserProfile.role` ; décorateurs `@require_roles(...)` |
| **Données sensibles** | `eleves_sante` accessible uniquement aux rôles habilités |
| **Portail citoyen** | Élèves et parents consultent uniquement leurs propres données |
| **Droit d'accès** | Art. 15 — `/students/rgpd/` affiche toutes les données personnelles |
| **Droit de rectification** | Art. 16 — `/students/rgpd/rectifier/` permet de corriger email, téléphone, adresse |
| **Droit à l'effacement** | Art. 17 — `/students/rgpd/effacer/` supprime le compte (données scolaires conservées per obligation légale) |
| **Droit à la portabilité** | Art. 20 — `/students/rgpd/exporter/` fournit un export JSON ou CSV structuré |
| **Admin séparé** | `/django-admin/` réservé aux administrateurs (`has_permission` override) |
| **Journalisation** | Django admin conserve les actions via `LogEntry` |
| **Export SQL** | Endpoint `/django-admin/export-schema/` pour la documentation du schéma |
