# API atelier de couture

API REST de gestion d'un atelier de couture : clients, mesures, commandes, paiements, livraisons et statistiques.

Stack : Python, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic, JWT (Argon2), pytest, Docker.

## Installation

### Prérequis

- Python 3.12 ou plus récent
- Docker Desktop (pour PostgreSQL et pour le lancement complet)
- Git

### Cloner et configurer

```bash
git clone https://github.com/VOTRE_UTILISATEUR/atelier-couture-api.git
cd atelier-couture-api
cp .env.example .env
```

Sous Windows PowerShell, remplacez `cp` par `Copy-Item`.

Éditez `.env` et remplacez `SECRET_KEY` par une longue chaîne aléatoire, par exemple :

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Ne committez jamais le fichier `.env`.

## Lancement avec Docker (recommandé)

```bash
docker compose up --build
```

Dans un second terminal, initialisez le compte administrateur et le catalogue :

```bash
docker compose exec api python -m app.seed
```

L'API est disponible sur `http://localhost:8000`, et la documentation Swagger sur `http://localhost:8000/docs`.

Les migrations s'appliquent automatiquement au démarrage (`alembic upgrade head`).

## Lancement en local

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell : .venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d db
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Tests

Les tests utilisent une base PostgreSQL séparée, `atelier_couture_test`, à créer une fois :

```bash
docker compose exec db psql -U atelier -d atelier_couture -c "CREATE DATABASE atelier_couture_test;"
```

Puis lancez :

```bash
python -m pytest -v
```

## Comptes de test

Le script `python -m app.seed` crée le premier administrateur à partir de `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`).

Les autres rôles se créent ensuite depuis l'administrateur, via `POST /api/v1/utilisateurs`. Les rôles sont `admin`, `accueil`, `tailleur`.

## Authentification

1. Connexion : `POST /api/v1/auth/login` (formulaire OAuth2 : `username` = e-mail, `password`).
2. Dans Swagger, cliquez sur **Authorize** et collez le jeton.

## Routes

Toutes les routes sont préfixées par `/api/v1`, sauf `/health`.

| Domaine | Méthode et chemin | Rôle |
|---|---|---|
| Santé | `GET /health` | Public |
| Auth | `POST /auth/login`, `GET /auth/me` | Public, connecté |
| Utilisateurs | `POST`, `GET`, `GET /{id}`, `PATCH /{id}` | Admin |
| Clients | `POST`, `GET` (recherche paginée), `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` | Tous, suppression admin |
| Clients | `GET /{id}/commandes`, `GET /{id}/resume` | Tous |
| Catalogue | `POST`, `GET`, `GET /{id}`, `PATCH /{id}` | Admin pour l'écriture |
| Mesures | `POST /clients/{id}/mesures`, `GET /clients/{id}/mesures`, `GET /clients/{id}/mesures/derniere` | Tailleur pour l'écriture |
| Mesures | `GET /mesures/{id}`, `PATCH /mesures/{id}`, `DELETE /mesures/{id}` | Tailleur pour la modification |
| Commandes | `POST`, `GET` (filtres), `GET /{id}`, `PATCH /{id}` | Accueil pour l'écriture |
| Commandes | `POST /{id}/lignes`, `DELETE /{id}/lignes/{ligne_id}` | Accueil |
| Commandes | `POST /{id}/statut`, `GET /{id}/historique` | Selon le statut |
| Paiements | `POST /commandes/{id}/paiements`, `GET /commandes/{id}/paiements`, `DELETE /paiements/{id}` | Accueil, annulation admin |
| Livraisons | `PUT /commandes/{id}/livraison`, `GET /commandes/{id}/livraison`, `POST /commandes/{id}/livraison/confirmer` | Accueil |
| Livraisons | `GET /livraisons` (tournée) | Tous |
| Statistiques | `GET /statistiques/tableau-de-bord`, `/chiffreaffaires`, `/typesvetement`, `/top-clients`, `/impayes` | Admin |

## Structure

```
app/
  core/        sécurité (Argon2, JWT) et dépendances (rôles)
  models/      modèles SQLAlchemy
  schemas/     schémas Pydantic (création, modification, lecture)
  services/    règles de gestion
  routers/     routes HTTP (droits et transaction)
alembic/       migrations
tests/         tests pytest
```