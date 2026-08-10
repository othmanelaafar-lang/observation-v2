# ETL Experts Marocains

Ce dossier contient un pipeline ETL Python pour collecter des profils d'experts marocains depuis:
- GitHub API
- OpenAlex API
- ORCID (optionnel)
- Google Scholar (optionnel, connecteur placeholder)

## 1) Installation

```bash
cd etl
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Configuration

```bash
copy .env.example .env
```

Variables importantes:
- `DATABASE_URL` connexion PostgreSQL
- `GITHUB_TOKEN` recommandé pour éviter les limites de rate
- `ENABLE_ORCID=true` pour activer ORCID
- `ENABLE_SCHOLAR=true` pour activer Scholar (placeholder actuellement)

## 3) Lancer le pipeline

Depuis la racine du repo:

```bash
python -m etl.run_etl
```

Pour obtenir un fichier JSON sans charger PostgreSQL:

```bash
python -m etl.run_etl --no-db --json-out etl/output/experts.json
```

## 4) Ce que fait le pipeline

1. Extraction multi-source
2. Nettoyage et normalisation
3. Déduplication
4. Calcul d'un score de pertinence
5. Filtrage strict: profils IA + signal marocain (résident ou diaspora) + seuil élite
6. Chargement dans PostgreSQL (`experts`)

Critères anti-débutant (configurables dans `.env`):
- recherche solide: `works_count >= MIN_WORKS_COUNT` et `h_index >= MIN_H_INDEX`
- ou citations solides: `cited_by_count >= MIN_CITATIONS`
- ou signal ingénierie: `public_repos >= MIN_GITHUB_REPOS` et `followers >= MIN_GITHUB_FOLLOWERS`

## 5) Prochaine étape (backend FastAPI)

Expose ensuite une API qui lit la table `experts`:
- `GET /experts`
- `GET /experts/{id}`
- `GET /experts/search?q=...`

Ton frontend React actuel pourra consommer directement cette API.
