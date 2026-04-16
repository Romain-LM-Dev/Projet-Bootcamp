# PlanningRH Hôpital — Phase 2

Application web de gestion du planning hospitalier.  
**Stack :** Django 5 · Django REST Framework · PostgreSQL · React (Vite)

---

## Architecture

```
frontend/          ← React (Vite)  port 5173
backend/           ← Django        port 8000
  hospital_planning/   ← projet Django
    settings.py
    urls.py
  planning/            ← application principale
    models.py       ← mapping complet du schéma SQL
    validators.py   ← contraintes dures C1–C8
    serializers.py  ← DRF serializers
    views.py        ← endpoints API
    urls.py
    admin.py
  requirements.txt
```

---

## 1. Base de données PostgreSQL

```sql
-- Créer la base
CREATE DATABASE hospital_planning;

-- Importer le schéma fourni
psql -U postgres -d hospital_planning -f database_hopital_corrige.sql
```

---

## 2. Backend Django

```bash
cd backend/

# Environnement virtuel
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# Dépendances
pip install -r requirements.txt

# Variables d'environnement (ou fichier .env)
export DB_NAME=hospital_planning
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
export NIGHT_REST_HOURS=11   # durée de repos post-garde de nuit (configurable)

# Migrations (si vous partez d'une base vierge)
python manage.py makemigrations planning
python manage.py migrate

# Superutilisateur admin
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
# → http://localhost:8000
# → Admin : http://localhost:8000/admin/
```

---

## 3. Frontend React

```bash
cd frontend/

# Dépendances
npm install

# Variable d'environnement (optionnel, valeur par défaut = localhost:8000)
echo "VITE_API_URL=http://localhost:8000/api" > .env.local

# Lancer en développement
npm run dev
# → http://localhost:5173
```

---

## 4. Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | /api/staff/ | Liste des soignants |
| POST | /api/staff/ | Créer un soignant |
| GET/PUT/PATCH/DELETE | /api/staff/{id}/ | CRUD soignant |
| GET | /api/shifts/ | Liste des postes |
| POST | /api/shifts/ | Créer un poste |
| GET/PUT/PATCH/DELETE | /api/shifts/{id}/ | CRUD poste |
| GET | /api/assignments/ | Liste des affectations |
| **POST** | **/api/assignments/** | **Créer une affectation** ← valide les contraintes C1–C8 |
| DELETE | /api/assignments/{id}/ | Supprimer une affectation |
| GET | /api/absences/ | Liste des absences |
| POST | /api/absences/ | Déclarer une absence |
| DELETE | /api/absences/{id}/ | Supprimer une absence |
| GET | /api/certifications/ | Référentiel certifications |
| GET | /api/contract-types/ | Référentiel types de contrats |
| GET | /api/shift-types/ | Référentiel types de gardes |
| GET | /api/absence-types/ | Référentiel types d'absences |
| GET | /api/services/ | Liste des services + unités |

---

## 5. Contraintes dures

Toutes vérifiées côté backend à chaque `POST /api/assignments/`.  
En cas de violation → **HTTP 409 Conflict** avec :

```json
{
  "code": "C3",
  "detail": "Certification expirée : ACLS (expirée le 2025-06-30)."
}
```

| Code | Contrainte |
|------|------------|
| C1 | Soignant actif |
| C2 | Pas d'absence déclarée |
| C3 | Certifications requises & non expirées |
| C4 | Contrat autorise ce type de garde (nuit) |
| C5 | Pas de chevauchement horaire |
| C6 | Repos réglementaire post-garde de nuit (`NIGHT_REST_HOURS`) |
| C7 | Quota hebdomadaire contractuel respecté |
| C8 | Contraintes impératives (préférences `is_hard_constraint=True`) |

---

## 6. CORS

Le frontend React tourne sur `localhost:5173`, le backend Django sur `localhost:8000`.  
`django-cors-headers` est configuré dans `settings.py` pour autoriser ces origines.  
En production, mettre à jour `CORS_ALLOWED_ORIGINS` avec le domaine réel.

---

## 7. Points de réflexion (Phase 2)

**REST** : URLs nommées par ressource (`/staff/`, `/shifts/`), verbes HTTP standard (GET/POST/PUT/PATCH/DELETE), réponses JSON avec codes HTTP sémantiques (201 Created, 204 No Content, 409 Conflict).

**409 vs 400** : une violation de contrainte dure est un *conflit métier*, pas une erreur de format — d'où le 409 avec un payload structuré `{code, detail}` permettant à l'UI d'afficher un message précis.

**CORS** : le navigateur bloque les requêtes cross-origin par défaut. `django-cors-headers` injecte les en-têtes `Access-Control-Allow-Origin` nécessaires.

**Audit log** : à implémenter avec un middleware Django ou `django-auditlog` ; garder dans la même base facilite les jointures mais une base séparée isole mieux les données d'audit en cas de restauration.

**Auth JWT** : pour la production, remplacer `AllowAny` par `JWTAuthentication` (package `djangorestframework-simplejwt`) — access token court (15 min) + refresh token (7 jours) pour renouveler sans re-connexion.
