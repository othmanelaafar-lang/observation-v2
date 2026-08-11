# RUNBOOK — Observatoire IA

Marche à suivre pour installer, lancer et vérifier le projet.

---

## ⚠️ À lire en premier

**La base livrée dans le dépôt contient l'ancienne population.**

`backend/observatoire.db` est versionnée et contient 137 profils, dont **133 en
poste au Maroc**. Elle date d'avant la correction de l'objectif : l'observatoire
recense les Marocains **résidant hors du Maroc** (diaspora), pas ceux restés au
pays.

L'application démarre donc immédiatement et affiche des profils, mais **ce n'est
pas encore la bonne liste**. Il faut relancer le pipeline (§3) pour la produire.

C'est aussi le filet de sécurité : si le pipeline donne un résultat décevant,
`git checkout backend/observatoire.db` rétablit une base qui fonctionne.

---

## 1. Installation (une seule fois)

```bash
git clone https://github.com/othmanelaafar-lang/observation.git
cd observation

python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
pip install -r etl/requirements.txt
npm install

cp etl/.env.example etl/.env       # Windows : copy etl\.env.example etl\.env
cp backend/.env.example backend/.env
```

Ouvrir `etl/.env` et renseigner une seule ligne :

```
OPENALEX_MAILTO=ton.email@exemple.com
```

Cela donne accès au « polite pool » d'OpenAlex (plus rapide, plus stable).
**Cela n'augmente pas le budget quotidien** — voir §6.

`GITHUB_TOKEN` est facultatif : OpenAlex et ORCID suffisent.

---

## 2. Vérifier l'installation — gratuit

```bash
python -m etl.selfcheck
```

Contrôle les imports, la configuration, le cache, la logique d'origine et de
classement (rejouée sur 6 profils étiquetés à la main), et joint ORCID en
direct. **Ne consomme aucun budget OpenAlex.**

Doit se terminer par `All checks passed`. Sinon, corriger avant §3 : découvrir
une installation cassée *après* avoir épuisé le budget coûte une journée.

---

## 3. Lancer le pipeline — consomme du budget

```bash
python -m etl.run_etl --no-db \
  --json-out etl/output/experts.json \
  --rejections-csv etl/output/rejected.csv \
  --review-csv etl/output/review_queue.csv
```

Coût mesuré : **environ 0,01 $** (≈ 39 requêtes pour l'hydratation ORCID, plus
la découverte OpenAlex). Le budget quotidien gratuit couvre largement.

Les réponses sont mises en cache dans `etl/cache/http`. **Les relances suivantes
sont gratuites et hors-ligne.** Pour forcer un rafraîchissement : supprimer ce
dossier.

Trois sorties :

| Fichier | Contenu |
|---|---|
| `experts.json` | profils **acceptés** — à charger dans l'API |
| `review_queue.csv` | signal marocain présent mais non corroboré — **à relire à la main** |
| `rejected.csv` | profils écartés + le filtre responsable (colonne `excluded_by`) |

`rejected.csv` est le premier endroit à regarder si le résultat est vide ou trop
maigre : il indique quel filtre a coupé, et combien.

---

## 4. Charger la base

```bash
cd backend
alembic upgrade head          # une seule fois, crée/migre le schéma
python seed.py --json-path ../etl/output/experts.json
cd ..
```

Le seeder **remplace** le contenu de la table. Pour revenir en arrière :

```bash
git checkout backend/observatoire.db
```

---

## 5. Lancer l'application

Deux terminaux, depuis la racine du dépôt.

**Terminal 1 — API :**
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — interface :**
```bash
npm run dev
```

Ouvrir **http://localhost:5173/explorer**

Vérifications rapides :
- http://127.0.0.1:8000/docs — Swagger
- http://127.0.0.1:8000/api/v1/stats — compte des profils chargés
- Filtre « Niveau » dans l'interface — `Elite` / `Confirme` / `Emergent`

---

## 6. Problèmes connus

### « Insufficient budget… Resets at midnight UTC »

OpenAlex facture chaque requête sur un quota quotidien. Ce n'est **pas** du
throttling : ni l'attente, ni `OPENALEX_MAILTO`, ni un nouveau lancement n'y
changent quoi que ce soit.

- attendre minuit UTC (remise à zéro), **ou**
- ajouter du crédit sur https://openalex.org/pricing (quelques centimes suffisent)

Le pipeline s'arrête maintenant net avec `BudgetExhausted` au lieu de continuer
avec des données partielles. Un run interrompu ainsi **ne doit pas être publié** :
il produit un échantillon tronqué qui a l'air normal.

### L'interface est vide alors que l'API répond

Vite bascule sur le port 5174 ou 5175 quand 5173 est pris, et le navigateur
bloque alors les appels API. Symptôme trompeur : la page ressemble à une base
vide. Les trois ports sont autorisés dans `backend/.env.example` ; vérifier que
`backend/.env` contient bien la même ligne `CORS_ORIGINS`.

Contrôler dans la console du navigateur (F12) : une erreur CORS y est explicite.

### Le pipeline sort très peu de profils

Regarder `rejected.csv`, colonne `excluded_by`, et compter par valeur. Les
seuils sont tous dans `etl/.env` :

| Pour élargir | Baisser |
|---|---|
| trop peu de profils IA | `MIN_AI_PURITY`, `MIN_AI_WORKS` |
| trop peu de diaspora | `MIN_MOROCCAN_AFFILIATION_YEARS`, `MIN_MOROCCAN_AFFILIATION_INSTITUTIONS` |
| trop peu d'élites | `TIER_ELITE_MIN_H_INDEX` |

Élargir augmente le volume **et** les faux positifs. Relire `review_queue.csv`
avant de baisser un seuil.

---

## 7. Limites à connaître avant de présenter

**Le run diaspora complet n'a jamais été mesuré.** Le code est en place et
validé pièce par pièce, mais aucun lancement complet n'a abouti (budget épuisé).
Le nombre de profils attendu est donc inconnu. C'est la première chose à faire.

**OpenAlex confond parfois des institutions.** Un chercheur français du CNRS
(Olivier Colliot) est accepté à tort : OpenAlex rattache son passage à *Télécom
Paris* (2002-2004) à une « École Supérieure des Télécommunications » étiquetée
marocaine. Sa carrière semble alors commencer au Maroc.

**OpenAlex fusionne parfois deux homonymes.** Le profil « Rachid Alami » mélange
un roboticien du CNRS à Toulouse et un chercheur marocain en énergie nucléaire.

Conséquence pratique : **relire les profils un par un avant publication**, en
particulier ceux dont la preuve marocaine tient à une seule institution sur peu
d'années. La colonne `origin_reason` du JSON donne le motif retenu.

**Les seuils sont calibrés sur une dizaine de profils** vérifiés à la main. Ils
sont à réajuster quand le volume augmentera.
