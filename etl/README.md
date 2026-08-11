# ETL Experts Marocains

Ce dossier contient un pipeline ETL Python pour collecter des profils d'experts marocains en IA depuis:
- OpenAlex API (source principale, sans clé)
- GitHub API (complément, token fortement recommandé)
- ORCID (optionnel)
- Google Scholar (optionnel, dataset curé en entrée)

## 1) Installation

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r etl/requirements.txt
```

## 2) Configuration

```bash
copy etl\.env.example etl\.env      # Windows
cp etl/.env.example etl/.env        # macOS / Linux
```

Variables importantes:
- `GITHUB_TOKEN` — sans token, GitHub n'autorise que 60 requêtes/heure et la source
  ne remonte quasiment rien. OpenAlex suffit à alimenter le pipeline seul.
- `OPENALEX_MAILTO` — votre email, pour rejoindre le "polite pool" OpenAlex (plus rapide/stable).
- `MAX_PAGES` / `PAGE_SIZE` — volume collecté (200 profils OpenAlex par défaut).
- `MIN_MOROCCAN_AFFILIATION_YEARS` — anti faux-positifs (voir §5).
- `REQUIRE_SENIORITY=true` pour un run plus strict (chercheurs confirmés uniquement).

## 3) Lancer le pipeline

Depuis la racine du repo:

```bash
# Snapshot JSON sans PostgreSQL (mode recommandé en local)
python -m etl.run_etl --no-db --json-out etl/output/experts.json --rejections-csv etl/output/rejected.csv

# Avec chargement PostgreSQL
python -m etl.run_etl --json-out etl/output/experts.json
```

Puis alimenter l'API backend:

```bash
cd backend
python seed.py --json-path ../etl/output/experts.json
```

Le fichier `etl/output/rejected.csv` liste chaque profil écarté et le filtre responsable
(colonne `excluded_by`) — c'est le premier endroit à regarder si le pipeline ne sort rien.

## 4) Ce que fait le pipeline

1. Extraction multi-source
2. Nettoyage et normalisation
3. Déduplication (identité forte, puis score de rapprochement inter-sources)
4. Scoring normalisé 0..1 et attribution d'un tier (`Elite` / `Confirme` / `Emergent`)
5. Filtrage: profils IA + signal marocain + seuils qualité
6. Chargement dans PostgreSQL (`experts`) ou export JSON

## 5) Notes sur la qualité des données

**Découverte OpenAlex.** Les auteurs sont cherchés via
`/authors?filter=affiliations.institution.country_code:MA + topics.id:<topics IA>`,
en deux stratégies: `resident` (institution actuelle au Maroc) et `diaspora`
(institution marocaine dans l'historique, actuellement à l'étranger).

> À ne pas refaire: `/authors?search=machine learning` ne cherche que dans le *nom*
> de l'auteur. Cet appel remontait des entités littéralement nommées
> "Machine Learning" et aucun chercheur — c'était la cause du pipeline vide.

**Faux positifs.** OpenAlex rattache une institution à un auteur dès un seul article
co-signé. Un chercheur étranger ayant co-signé un papier avec un labo marocain apparaît
donc comme "affilié Maroc". Le filtre `moroccan-affiliation-depth` exige donc une
affiliation marocaine étalée sur plusieurs années ou plusieurs institutions
(`MIN_MOROCCAN_AFFILIATION_YEARS`, `MIN_MOROCCAN_AFFILIATION_INSTITUTIONS`).
Augmenter ces seuils = plus de précision, moins de volume.

**GitHub.** Les critères "a contribué à pytorch/tensorflow" (`GITHUB_REQUIRE_NOTABLE_REPO`)
et "a un repo taggé IA" (`GITHUB_REQUIRE_AI_TOPIC_REPO`) sont désactivés par défaut:
ils rejetaient la quasi-totalité des profils réels. Le signal notable-repo n'est
observable que via les 100 derniers évènements publics de l'utilisateur.

## 6) Backend FastAPI

Voir `backend/README.md`. L'API lit la table `talents`:
- `GET /api/v1/talents`
- `GET /api/v1/talents/{id}`
- `GET /api/v1/search?q=...`
- `GET /api/v1/stats`
