
# Lycée RGPD – Gestion des élèves | DOCUMENTATION TECHNIQUE

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
| `/admin/audit/` | Journal d'audit complet (admin seulement) |
| `/admin/audit/signalements/` | Liste des signalements de violation (admin seulement) |
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

### DPO & Sécurité (tous utilisateurs)

| URL | Description |
|---|---|
| `/dpo/` | Page de contact DPO (accès public) |
| `/dpo/signalement/` | Signalement de violation de données (anonyme ou authentifié) |

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

## Contact DPO, Signalement et Journalisation

### Contact DPO (Délégué à la Protection des Données)

**URL :** `GET /dpo/` — accès public, aucune authentification requise

Page centralisant toutes les informations de contact du référent RGPD, les 6 droits des personnes avec liens directs vers les fonctionnalités correspondantes, et un lien vers le formulaire de signalement. Affichée dans la navbar des deux portails.

**Coordonnées DPO (démo) :**
- Email : dpo@lycee-rgpd.fr  
- Téléphone : 01 23 45 67 89 (lun–ven 9h–17h)
- Réponse garantie dans le délai légal d'1 mois (Art. 12 RGPD)

---

### Procédure de signalement de violation de données (Art. 33–34 RGPD)

**URL :** `GET / POST /dpo/signalement/` — accessible à tous (authentifié ou anonyme)

Tout utilisateur peut signaler une violation supposée. Si l'utilisateur est connecté, son identifiant est automatiquement associé au signalement. Un utilisateur non connecté peut laisser ses coordonnées dans le message (signalement anonyme).

**Cycle de vie d'un signalement :**

| Statut | Description |
|---|---|
| `En attente` | Signalement reçu, non traité |
| `En cours d'enquête` | Le DPO/admin a pris en charge la demande |
| `Résolu` | Violation confirmée et traitée |
| `Classé sans suite` | Fausse alerte, aucune violation avérée |

**Interface admin :** `/admin/audit/signalements/` — l'administrateur peut lire les signalements, les qualifier et ajouter des notes internes.

> L'établissement doit notifier la CNIL sous **72 heures** en cas de violation confirmée (Art. 33 RGPD). En cas de risque élevé pour les personnes, les individus concernés doivent également être informés (Art. 34 RGPD).

---

### Système de journalisation (Journal d'audit)

**URL :** `GET /admin/audit/` — réservé aux administrateurs

Toutes les actions sensibles sont enregistrées dans le modèle `AuditLog` avec : horodatage précis, utilisateur, action, cible, adresse IP, et détails.

**Actions tracées automatiquement :**

| Action | Déclencheur |
|---|---|
| `login` | Connexion réussie (portail staff ou élèves) |
| `logout` | Déconnexion (portail staff ou élèves) |
| `access` | Consultation d'une fiche élève (`/admin/eleves/<pk>/`) |
| `create` | Création d'un élève ou d'une note |
| `update` | Modification d'un élève ou d'une note |
| `delete` | Suppression d'un élève ou d'une note |
| `export` | Export RGPD (Art. 20) — format JSON ou CSV |
| `erase` | Effacement de compte (Art. 17) |
| `breach_report` | Soumission d'un signalement de violation |

**Fonctionnalités de l'interface audit :**
- Filtre par type d'action
- Filtre par nom d'utilisateur
- Affichage de l'adresse IP source (support `X-Forwarded-For` pour les proxies)
- Les 500 entrées les plus récentes sont affichées

**Modèle `AuditLog` :**  
```python
user         # FK User (SET_NULL si compte supprimé)
action       # 'access' | 'create' | 'update' | 'delete' | 'export' | 'erase' | 'login' | 'logout' | 'breach_report'
target       # Chaîne décrivant la ressource concernée (ex: "Élève #3 – Hugo Bernard")
ip_address   # Adresse IP de la requête
timestamp    # Horodatage automatique
details      # Informations complémentaires (format, description tronquée...)
```

**Note technique :** `_audit()` est un helper silencieux — toute exception interne est ignorée pour ne jamais perturber le flux principal de l'application.

---

## Droits RGPD des utilisateurs (Art. 15, 16, 17, 20)

Les quatre droits fondamentaux du RGPD sont accessibles depuis le portail élèves/parents via le menu **"🔍 Mes données"** ou les raccourcis sur les tableaux de bord.

---

### Droit d'accès aux données — Art. 15

**URL :** `GET /students/rgpd/`

Affiche l'ensemble des données personnelles détenues par l'établissement, regroupées par catégorie :

| Profil | Données affichées |
|---|---|
| **Élève** | Identité (nom, prénom, date de naissance, email, téléphone, adresse), scolarité (classe, options), liste complète des notes avec matière, coefficient, trimestre, appréciation |
| **Parent** | Coordonnées (email, téléphone), liste des enfants avec leur classe |

> Accessible uniquement à l'utilisateur connecté (`@login_required`). Chaque utilisateur ne voit que ses propres données.

---

### Droit de rectification — Art. 16

**URL :** `GET / POST /students/rgpd/rectifier/`

Permet de corriger les coordonnées de contact. Les champs éditables sont volontairement limités aux données de contact — les données d'identité officielle (nom, prénom, date de naissance) et les données scolaires ne peuvent être modifiées que par le personnel habilité.

| Profil | Champs modifiables |
|---|---|
| **Élève** | Email, téléphone, adresse |
| **Parent** | Email, téléphone |

Formulaires dédiés : `EleveRectifyForm`, `ParentRectifyForm` (définis dans `eleves/forms.py`).

---

### Droit à l'effacement — Art. 17

**URL :** `GET / POST /students/rgpd/effacer/`

Supprime le compte de connexion après confirmation par mot de passe.

**Ce qui est supprimé :**
- Le compte utilisateur Django (`User`)
- Le profil de rôle (`UserProfile`)
- La session active (déconnexion immédiate)

**Ce qui est conservé** (obligation légale — Art. 6 §1 e RGPD) :
- La fiche élève (`Eleve`) et son dossier scolaire
- La fiche parent (`Parent`)
- Les notes et bulletins

Après suppression, l'utilisateur est redirigé vers `/students/login/?effacement=ok` avec un message de confirmation.

> **Sécurité :** la référence à `request.user` est sauvegardée avant l'appel à `logout()`, afin d'éviter que `request.user` devienne `AnonymousUser` avant la suppression.

---

### Droit à la portabilité — Art. 20

**URL :** `GET /students/rgpd/exporter/?format=json` ou `?format=csv`

Génère un téléchargement structuré et lisible par machine de toutes les données personnelles.

#### Format JSON
```json
{
  "compte": { "username": "lucas.eleve", "date_inscription": "..." },
  "identite": { "nom": "Bernard", "prenom": "Hugo", ... },
  "scolarite": { "classe": "Terminale S", "options": "..." },
  "notes": [
    { "matiere": "Mathematiques", "coefficient": 4, "trimestre": "T1",
      "note": 15.5, "appreciation": "Bon travail", "date": "2025-11-10" }
  ]
}
```

#### Format CSV
Fichier tabulaire avec sections séparées par des lignes vides :

```
Section,Champ,Valeur
Identite,Nom,Bernard
Identite,Prenom,Hugo
...
Notes,Matiere,Coefficient,Trimestre,Note /20,Appreciation,Date
Notes,Mathematiques,4,T1,15.5,Bon travail,2025-11-10
```

Le nom de fichier téléchargé suit le format `rgpd_<username>_<date>.<ext>`.

---



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
| **Journalisation** | `AuditLog` : accès, créations, modifications, suppressions, exports, connexions |
| **Contact DPO** | `/dpo/` public — coordonnées, droits, formulaire de signalement |
| **Signalement violation** | `/dpo/signalement/` — tout utilisateur (authentifié ou anonyme) peut signaler |
