# Backend FastAPI - Observatoire IA

Backend API pour servir les talents marocains en IA.

## Endpoints principaux

- `GET /api/v1/talents`
- `GET /api/v1/talents/{talent_id}`
- `GET /api/v1/leaderboards/talent/{i}`
- `GET /api/v1/search?q=...`

## Endpoints utiles ajoutés

- `GET /api/v1/stats`
- `GET /api/v1/domains`
- `GET /api/v1/universities`
- `GET /api/v1/health`

## Setup

```bash
cd backend
python -m venv .venv
# PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Migrations (Alembic)

```bash
alembic upgrade head
```

## Seeder depuis ETL JSON

Depuis le dossier backend:

```bash
python seed.py --json-path ../etl/output/experts_elite.json
```

## Run API

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger:
- `http://127.0.0.1:8000/docs`

## Notes

- Le modèle principal est `Talent` avec relations many-to-many vers `Domain` et `University`.
- Les modèles sont prêts pour migration via Alembic dans `alembic/versions/`.
