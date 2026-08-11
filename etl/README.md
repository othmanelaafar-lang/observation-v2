# ETL Experts Marocains

> **Cible: la diaspora.** L'observatoire recense les experts marocains en IA
> **résidant hors du Maroc**. Les chercheurs actuellement en poste au Maroc sont
> volontairement exclus (`origin_verdict` les rejette avec le motif
> « based in Morocco »).

Ce dossier contient un pipeline ETL Python pour collecter des profils d'experts marocains en IA depuis:
- **ORCID** (découverte diaspora: qui a *quitté* une institution marocaine)
- **OpenAlex** (découverte + métriques: h-index, citations, sujets)
- GitHub API (complément, token fortement recommandé)
- Google Scholar (optionnel, dataset curé en entrée)

### Pourquoi deux sources de découverte

Elles sont **complémentaires, pas interchangeables**:

| | voit | ne voit pas |
|---|---|---|
| **OpenAlex** | ceux qui ont *publié* depuis une institution marocaine, puis sont partis | celui qui a étudié au Maroc sans jamais y publier — le parcours le plus courant de l'élite |
| **ORCID** | ceux qui *déclarent* une formation ou un poste marocain | celui qui ne l'a pas déclaré |

Exemple concret: Mehdi Bennis (h-index 86) est trouvé par OpenAlex — il a publié
depuis Cadi Ayyad au début de sa carrière — mais son ORCID ne mentionne que
Oulu, EURECOM et EPFL. Une découverte ORCID seule l'aurait manqué.

La requête ORCID utilise `past-institution-affiliation-name`, pas
`affiliation-org-name`: la seconde remonte surtout le personnel *actuel*
(1217 profils pour Cadi Ayyad contre 387 en « passé »), qui par définition
n'est pas la diaspora.

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
python -m etl.run_etl --no-db \
  --json-out etl/output/experts.json \
  --rejections-csv etl/output/rejected.csv \
  --review-csv etl/output/review_queue.csv

# Avec chargement PostgreSQL
python -m etl.run_etl --json-out etl/output/experts.json
```

Puis alimenter l'API backend:

```bash
cd backend
python seed.py --json-path ../etl/output/experts.json
```

Trois sorties:
- `experts.json` — profils **acceptés** (origine marocaine confirmée), à charger dans l'API.
- `review_queue.csv` — profils **à vérifier à la main**: le signal marocain existe mais
  n'est pas corroboré. Ne pas publier sans relecture.
- `rejected.csv` — profils écartés, avec le filtre responsable (colonne `excluded_by`).
  C'est le premier endroit à regarder si le pipeline ne sort rien.

## 4) Ce que fait le pipeline

1. Extraction multi-source
2. Nettoyage et normalisation
3. Déduplication (identité forte, puis score de rapprochement inter-sources)
4. Filtrage: focus IA (`ai_purity`) + signal marocain + seuils qualité
5. Enrichissement ORCID des survivants, puis routage par force de preuve
6. Attribution d'un tier sur seuils **absolus** (`Elite` / `Confirme` / `Emergent`)
7. Chargement dans PostgreSQL (`experts`) ou export JSON

### Routage par origine (étape 5)

Deux conditions doivent tenir ensemble: **être hors du Maroc aujourd'hui**, et
**être marocain d'origine**. La seconde est la difficile.

| Condition | Verdict |
|---|---|
| en poste au Maroc | **rejeté** (hors périmètre) |
| ORCID déclare une formation ou un poste au Maroc | **accepté** |
| fraction ≤ 0.15 **et** ≥ 3 années marocaines **et** ≥ 2 institutions | **accepté** |
| fraction ≤ 0.5 (présence plausible mais non confirmée) | à vérifier |
| sinon | **rejeté** |

**Le signal décisif: où la carrière a commencé.** `moroccan_career_fraction` mesure
la part de la carrière écoulée avant la première affiliation marocaine:

| | 1re publi | 1re affil. MA | fraction | |
|---|---|---|---|---|
| Mehdi Bennis | 1989 | 1989 | **0.00** | marocain |
| Rachid Alami | 1980 | 1980 | **0.00** | marocain |
| Jean-Claude Martin | 1966 | 2000 | 0.57 | étranger |
| Xin-She Yang | 1986 | 2013 | 0.68 | étranger |
| Ignacio Rojas | 1895 | 2016 | 0.93 | étranger |

Un émigré marocain démarre sa carrière au Maroc (fraction ≈ 0) **et** y reste rattaché
plusieurs années. Un collaborateur étranger acquiert une affiliation marocaine bien
après ses débuts, souvent pour une ou deux années isolées.

Les seuils ont été calibrés sur les profils réellement remontés — la zone 0.29–0.48
contenait exclusivement des faux positifs (un chercheur INRAE français avec 13 ans de
collaboration INRA-Maroc, un chercheur algérien dont ORCID indique `DZ,FR`), tandis
que les profils authentiques étaient tous à 0.00 avec 5 à 14 années marocaines.

> Calibrage effectué sur un échantillon réduit (une dizaine de profils vérifiés à la
> main). Les seuils sont dans `etl/.env`, à réajuster quand le volume augmente.

### Tiers (étape 6)

Les tiers reposent sur des **seuils absolus** (h-index, focus IA, activité récente),
pas sur le score. Le score est une normalisation min-max *à l'intérieur du lot
téléchargé*: un seul profil hors-norme écrase tous les autres et le tier d'une même
personne change d'un run à l'autre. Le score reste utilisé pour trier dans un tier.

| Tier | Condition |
|---|---|
| `Elite` | `h_index >= 40` et `ai_purity >= 0.5` et publication dans les 5 ans |
| `Confirme` | `h_index >= 25` et `ai_purity >= 0.25` |
| `Emergent` | `h_index >= 10` et `ai_purity >= 0.25` |

## 5) Notes sur la qualité des données

**Découverte OpenAlex.** Une seule requête, avec une clause **négative** qui écarte
les chercheurs restés au Maroc:

```
/authors?filter=affiliations.institution.country_code:MA,
                last_known_institutions.country_code:!MA,
                topics.id:<topics IA>
```

> Attention: `last_known_institutions` est une **liste**. Un chercheur rattaché à la
> fois à une institution marocaine et à une institution étrangère est considéré comme
> résident au Maroc, donc exclu. C'est voulu (Ismaïl Berrada et El Houcine Bergou sont
> à l'UM6P), mais cela écarte aussi les doubles affiliations réelles.

> À ne pas refaire: `/authors?search=machine learning` ne cherche que dans le *nom*
> de l'auteur. Cet appel remontait des entités littéralement nommées
> "Machine Learning" et aucun chercheur — c'était la cause du pipeline vide.

**Faux positifs.** OpenAlex rattache une institution à un auteur dès un seul article
co-signé. Un chercheur étranger ayant co-signé un papier avec un labo marocain apparaît
donc comme "affilié Maroc". Le filtre `moroccan-affiliation-depth` exige donc une
affiliation marocaine étalée sur plusieurs années ou plusieurs institutions
(`MIN_MOROCCAN_AFFILIATION_YEARS`, `MIN_MOROCCAN_AFFILIATION_INSTITUTIONS`).
Augmenter ces seuils = plus de précision, moins de volume.

**IA vs. IA-comme-outil.** `ai_purity` = part des travaux de l'auteur dans les sous-domaines
IA d'OpenAlex. Un chercheur NLP est à ~1.0, un cardiologue ayant publié un article avec un
CNN est à ~0.03.

Mais la part seule pénalise l'IA interdisciplinaire: un chercheur majeur en federated
learning dont les articles sont classés en communications sans fil tombe à ~0.15 de part
tout en ayant plus de cent travaux IA. Le filtre accepte donc `ai_purity >= MIN_AI_PURITY`
**ou** `ai_works_count >= MIN_AI_WORKS`. Le cardiologue échoue aux deux.

**La profondeur de scan n'apporte pas d'élites.** La requête OpenAlex trie par
`cited_by_count:desc`: les plus cités sont déjà en page 1. Passer de 200 à 1100 profils
scannés a multiplié le volume par 5 sans ajouter un seul profil `Confirme` ou `Elite`.
Scanner plus profond augmente la couverture des profils émergents, pas le haut du panier.

**Ne pas filtrer l'élite avant la nationalité.** Le haut du classement par citations est
dominé par des chercheurs étrangers ayant co-signé un article avec un labo marocain. Sur un
lot type, `h_index >= 40` sans contrôle d'origine donnait 11 profils dont 2 marocains.
Appliquer l'ordre: origine → focus IA → seuil élite.

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
