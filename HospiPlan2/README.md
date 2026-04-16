# HospiPlan2

Plateforme de gestion et de planification des gardes hospitalières. Permet de gérer le personnel soignant, les postes de travail, les absences et de générer automatiquement un planning optimisé en respectant les contraintes métier.

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | React 18, React Router v6, Axios, Vite |
| Backend | Django 6, Django REST Framework |
| Base de données | PostgreSQL |
| Style | CSS vanilla (pas de framework UI) |

---

## Structure du projet

```
HospiPlan2/
├── backend/                  # API Django
│   ├── config/               # Settings, URLs, WSGI
│   ├── core/                 # Services, unités, types de poste, règles métier
│   ├── staff/                # Personnel, rôles, contrats, spécialités
│   ├── shifts/               # Postes de travail et templates
│   ├── planning/             # Affectations, absences, préférences
│   ├── optimization/         # Moteur de génération automatique
│   └── core/management/      # Commandes de peuplement de la base
│       commands/
│         seed_data.py        # Données de base (personnel, services…)
│         setup_test_week.py  # Postes + absences pour la semaine de test
├── frontend/                 # Application React
│   └── src/
│       ├── App.jsx           # Toutes les pages et composants
│       ├── AuthContext.jsx   # Gestion de session
│       ├── api.js            # Instance Axios + endpoints
│       └── App.css           # Styles globaux
├── start_dev.bat             # Lance backend + frontend en même temps
├── start_backend.bat         # Lance uniquement le backend
└── start_frontend.bat        # Lance uniquement le frontend
```

---

## Prérequis

- Python 3.11+
- Node.js 18+
- PostgreSQL (base `hospiplan2`, user `postgres`, mot de passe `1`)

### Créer la base PostgreSQL (une seule fois)

```sql
CREATE DATABASE hospiplan2;
```

### Installer les dépendances Python (une seule fois)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install django djangorestframework django-cors-headers psycopg2-binary python-dotenv
```

### Appliquer les migrations (une seule fois)

```bash
cd backend
python manage.py migrate
```

### Installer les dépendances Node (une seule fois)

```bash
cd frontend
npm install
```

---

## Démarrage

### Option A — Tout lancer d'un seul clic (recommandé)

Double-cliquer sur **`start_dev.bat`** à la racine du projet.

Cela ouvre deux fenêtres :
- **Backend** : réinitialise les données, crée les postes de test, lance Django sur `http://localhost:8000`
- **Frontend** : lance Vite sur `http://localhost:3000`

> Les données sont **réinitialisées à chaque démarrage** : 18 agents, 64 postes pour la semaine 13-19 avril, 4 absences de test.

### Option B — Démarrage manuel

```bash
# Terminal 1 — Backend
cd backend
venv\Scripts\activate
python manage.py seed_data --clear     # Remet tout à zéro
python manage.py setup_test_week       # Crée les postes de test
python manage.py runserver             # http://localhost:8000

# Terminal 2 — Frontend
cd frontend
npm run dev                            # http://localhost:3000
```

---

## Compte administrateur

Créé automatiquement par `seed_data` :

| Champ | Valeur |
|-------|--------|
| Identifiant | `admin` |
| Mot de passe | `admin` |

---

## Données de test générées

### Personnel (22 agents)

| Rôle | Agents |
|------|--------|
| Infirmier (IDE) | Marie Dupont, Pierre Martin, Julie Robert, Camille Durand, Laura Moreau, Isabelle Laurent, Emma Blanc, Manon Garnier, Romain Lambert, Théo Renard, Paul Legrand |
| Aide-soignant (AS) | Sophie Bernard, Nicolas Richard, Kevin Simon, Antoine Lefevre, Lucas Rousseau, Céline Bonnet, Léa Marchand, Clara Fontaine |
| Médecin (MED) | Thomas Petit, Julien Dubois, Hugo Faure |

Chaque agent a : un rôle, une spécialité, un contrat (temps plein 35h ou partiel 28h).

> Dimensionnement : 22 agents × ~35h/semaine = ~96 slots théoriques. Après absences (~10 slots perdus) : ~86 disponibles pour couvrir 60 affectations (couverture complète 2/2 sur 32 postes).

### Postes — semaine 13-19 avril 2026

- 2 unités de soin × 7 jours × 2 types (Jour 7h-15h, Soir 15h-23h) = **28 postes**
- 2 unités × 2 jours (mercredi + samedi) × Nuit 23h-7h = **4 postes nuit**
- **Total : 32 postes, 0 affectation** au démarrage

> Dimensionné pour 18 agents : ~60 slots disponibles après absences → couverture complète garantie par l'optimiseur.

### Absences de test

| Agent | Type | Période |
|-------|------|---------|
| Sophie Bernard | Maladie | Toute la semaine (13-19 avril) |
| Julien Dubois | Maladie | Mercredi-jeudi (15-16 avril) |
| Hugo Faure | Congés payés | Lundi-mercredi (13-15 avril) |
| Isabelle Laurent | RTT | Vendredi (17 avril) |

---

## Pages de l'application

| Route | Description |
|-------|-------------|
| `/` | Tableau de bord — stats globales et dernières générations |
| `/planning` | Planning hebdomadaire par unité de soin |
| `/staff` | Liste du personnel + création manuelle d'agents |
| `/shifts` | Liste des postes + affectation manuelle par poste |
| `/optimization` | Lancement de la génération automatique |
| `/config` | Accès à l'administration Django (requiert compte admin) |

---

## Fonctionnement du moteur d'optimisation

Accessible via **Génération auto** dans l'app ou `POST /api/generate/`.

### Algorithme

Type : **greedy heuristique** (glouton avec contraintes).

Pour chaque poste à couvrir, il :

1. Récupère tous les agents actifs
2. Élimine ceux qui sont **en absence** ce jour-là
3. Élimine ceux qui ont déjà un **poste qui se chevauche**
4. Élimine ceux dont le **contrat n'autorise pas les nuits** (si poste de nuit)
5. Élimine ceux qui dépasseraient leur **quota hebdomadaire** (max_hours_per_week)
6. Élimine ceux qui dépasseraient le **max de nuits consécutives** (règle métier, défaut = 5)
7. Trie les agents éligibles par **charge de travail croissante** (équité)
8. Affecte jusqu'à atteindre `min_staff` pour le poste

### Contraintes molles (pénalités)

Le score final reflète les pénalités accumulées :
- Nuits consécutives (pondération configurable)
- Déséquilibre de charge entre agents

### Configuration

Les poids sont ajustables dans l'admin Django → **Configuration optimisation**.

---

## API REST — Endpoints principaux

Tous préfixés par `/api/`.

### Authentification
```
POST   /api/auth/login/          Corps : { username, password }
POST   /api/auth/logout/
GET    /api/auth/user/           Retourne l'utilisateur courant
```

### Données de référence
```
GET    /api/services/
GET    /api/care-units/
GET    /api/shift-types/
GET    /api/absence-types/
GET    /api/rules/
```

### Personnel
```
GET    /api/staff/               Paramètre : ?is_active=true
POST   /api/staff/               Créer un agent
GET    /api/roles/
POST   /api/staff-roles/         Lier un agent à un rôle
GET    /api/contract-types/
POST   /api/contracts/           Créer un contrat
```

### Planning
```
GET    /api/shifts/              Paramètres : ?start_date=&end_date=
GET    /api/assignments/         Paramètres : ?shift=&staff=&start_date=&end_date=
POST   /api/assignments/         Corps : { staff: id, shift: id }
DELETE /api/assignments/{id}/    Supprimer une affectation
GET    /api/absences/            Paramètres : ?start_date=&end_date=
```

### Optimisation
```
POST   /api/generate/            Corps : { start_date, end_date, service_id? }
GET    /api/optimization-runs/   Historique des générations
```

---

## Administration Django

Accessible via l'écran **Configuration** de l'app (ou directement sur `http://localhost:3000/admin/`).

Modules disponibles :
- **Services** — pôles hospitaliers
- **Unités de soin** — salles et unités par service
- **Types de poste** — Jour / Soir / Nuit et paramètres
- **Types d'absence** — Congés / Maladie / RTT
- **Règles métier** — contraintes configurables (nuits consécutives, heures max…)
- **Configuration optimisation** — poids de l'algorithme

---

## Variables d'environnement

Fichier `backend/.env` (non versionné) :

```env
DJANGO_SECRET_KEY=...
DEBUG=True
DB_NAME=hospiplan2
DB_USER=postgres
DB_PASSWORD=1
DB_HOST=localhost
DB_PORT=5432
```
