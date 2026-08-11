# Prompts à donner à Copilot

Ce qui reste à faire, et qui n'a pas pu être fait faute de budget OpenAlex.
Chaque section est un prompt autonome : copier le bloc entier dans Copilot Chat,
avec le dépôt ouvert.

---

## Prompt 1 — Le run de mesure (à faire en premier)

> **Contexte.** Ce dépôt est un observatoire des experts marocains en IA
> **résidant hors du Maroc** (diaspora). Le pipeline ETL a été entièrement
> réécrit pour cet objectif, mais **aucun lancement complet n'a jamais abouti** :
> le budget quotidien OpenAlex a été épuisé avant. Le nombre de profils que le
> pipeline produit est donc inconnu. Chaque brique a été validée séparément,
> jamais l'ensemble.
>
> **Tâche.** Lancer le pipeline, mesurer, et rapporter.
>
> 1. Vérifier d'abord que le budget est disponible :
>    `curl -s "https://api.openalex.org/authors?per-page=1" | head -c 200`
>    Si la réponse contient `Insufficient budget`, s'arrêter : le quota se
>    réinitialise à minuit UTC.
> 2. `python -m etl.selfcheck` — doit afficher `All checks passed`.
> 3. Lancer :
>    ```
>    python -m etl.run_etl --no-db --json-out etl/output/experts.json \
>      --rejections-csv etl/output/rejected.csv \
>      --review-csv etl/output/review_queue.csv
>    ```
> 4. Rapporter précisément :
>    - le nombre de profils **acceptés**, en file de **relecture**, et **rejetés** ;
>    - le décompte par valeur de la colonne `excluded_by` dans `rejected.csv`,
>      trié par fréquence décroissante — c'est l'entonnoir : il montre quel
>      filtre coupe le plus ;
>    - la répartition par `tier` (`Elite` / `Confirme` / `Emergent`) ;
>    - la répartition par pays de résidence ;
>    - la liste nominative des profils `Elite` et `Confirme`, avec affiliation,
>      h-index, `ai_purity` et `origin_reason`.
>
> **Important.** Si le pipeline s'interrompt sur `BudgetExhausted`, le résultat
> est un échantillon tronqué qui a l'air normal. Ne pas le publier : le signaler
> et relancer une fois le quota rétabli. Les réponses déjà obtenues sont en
> cache (`etl/cache/http`), donc la reprise ne recoûte que ce qui manque.
>
> **Ne rien modifier** dans les filtres à ce stade. Cette étape sert à mesurer,
> pas à ajuster. Les seuils ont été calibrés sur une dizaine de profils
> seulement ; les corriger sans mesure préalable revient à deviner.

---

## Prompt 2 — Faux positifs par erreur d'institution OpenAlex

> **Contexte.** `etl/filters.py` décide si un chercheur est d'origine marocaine
> avec `moroccan_career_fraction` : la part de la carrière écoulée avant la
> première affiliation marocaine. Un émigré démarre à ~0.00, un collaborateur
> étranger acquiert une affiliation marocaine tardivement.
>
> **Le problème.** OpenAlex se trompe parfois d'institution, et une erreur en
> début de carrière produit une fraction de 0.00 pour un chercheur qui n'a jamais
> mis les pieds au Maroc.
>
> Cas vérifié : **Olivier Colliot**, chercheur CNRS/ICM à Paris, est *accepté*.
> OpenAlex lui attribue une affiliation « École Supérieure des Télécommunications »
> étiquetée `MA` pour [2002, 2003, 2004]. Or il était à **Télécom Paris**
> (ex-ENST, Paris) exactement ces années-là — l'institution figure d'ailleurs
> séparément dans sa fiche, avec les mêmes années.
>
> **La signature de l'erreur** : une affiliation marocaine dont les années sont
> incluses dans celles d'une affiliation étrangère, avec des noms partageant des
> mots significatifs (« Télécommunications » / « Télécom »).
>
> **Tâche.** Détecter ce motif dans `etl/filters.py` et router ces profils vers
> `ORIGIN_REVIEW` plutôt que `ORIGIN_ACCEPT`, avec un `origin_reason` explicite.
>
> **Contraintes.**
> - Ne pas casser les vrais positifs. `python -m etl.selfcheck` doit continuer à
>   passer : **Mehdi Bennis** (Cadi Ayyad, 1989-2020) et **Omar Elharrouss**
>   (Sidi Mohamed Ben Abdellah, 2015-2018) doivent rester `accept`.
> - Ne pas coder en dur le nom d'une institution : le mécanisme doit se
>   généraliser à d'autres confusions du même type.
> - Ajouter le cas Colliot dans `etl/fixtures/origin_cases.json` avec
>   `"expected_verdict": "review"`, pour verrouiller la correction.

---

## Prompt 3 — Homonymes fusionnés

> **Contexte.** OpenAlex fusionne parfois deux chercheurs homonymes en une seule
> fiche. Exemple vérifié : **Rachid Alami** mélange un roboticien du CNRS à
> Toulouse (h-index 50, robotique et IA) et un chercheur marocain en énergie
> nucléaire et épidémiologie (CNESTEN, 2002-2025). La fiche fusionnée passe tous
> les filtres : affiliation marocaine profonde *et* forte production en IA — sauf
> qu'elles appartiennent à deux personnes différentes.
>
> **Tâche.** Détecter les fiches probablement fusionnées et les envoyer en
> relecture au lieu de les accepter.
>
> **Pistes** (à évaluer, pas à appliquer aveuglément) :
> - incohérence thématique : les `topics` liés aux affiliations marocaines
>   n'ont aucun recouvrement avec ceux des affiliations étrangères ;
> - deux blocs d'affiliations simultanés dans des pays différents, sur des
>   domaines disjoints ;
> - l'ORCID de la fiche ne mentionne aucune institution marocaine alors que
>   OpenAlex en revendique plusieurs.
>
> **Contrainte.** Mesurer l'effet sur l'ensemble du lot avant de conclure : une
> heuristique trop large renverrait toute la diaspora en relecture, ce qui
> reviendrait à supprimer le filtre. Rapporter combien de profils changent de
> verdict, pas seulement que le cas Alami est réglé.

---

## Prompt 4 — Élargir la découverte ORCID

> **Contexte.** `etl/config.py` liste 24 établissements marocains interrogés sur
> ORCID via `past-institution-affiliation-name`. Le balayage actuel remonte
> **1930 candidats distincts**.
>
> ORCID indexe les noms **anglais** : « International University of Rabat »
> renvoie 65 résultats, « Universite Internationale de Rabat » en renvoie 1.
> Toujours tester la variante anglaise.
>
> **Interdit.** Ne pas ajouter d'acronymes seuls. Une institution marocaine
> déclarée est un chemin d'**acceptation directe** dans `origin_verdict`, donc
> une collision fait entrer un étranger sans autre contrôle. Vérifié :
> « ENSAM » remonte du personnel SNCF, ONERA et Université de Lorraine (Arts et
> Métiers, France) ; « EMSI » remonte l'Electron Microscope Society of India et
> des chercheurs de Rice et Stanford ; « INSEA » remonte Trabzon University.
> `ENSIAS` est la seule exception retenue, aucune autre institution ne porte ce
> nom.
>
> **Tâche.** Ajouter des établissements manquants (facultés de médecine, INPT,
> IAV Hassan II, ENSA, FST, écoles privées…). Pour chacun :
>
> 1. Tester d'abord le nombre de résultats :
>    ```python
>    from etl.sources.orcid_discovery import _orcid_search
>    p = _orcid_search('past-institution-affiliation-name:"<NOM>"', 0, 8)
>    print(p.get("num-found"))
>    for r in p.get("expanded-result"): print(r.get("institution-name"))
>    ```
> 2. **Lire les résultats** : si des institutions étrangères apparaissent, le nom
>    est ambigu — ne pas l'ajouter.
> 3. N'ajouter que ce qui rapporte des résultats sans ambiguïté.
>
> ORCID est gratuit et non facturé : ces essais ne coûtent rien.

---

## Prompt 5 — Régénérer le PDF de présentation

> `docs/algorithme.html` décrit l'algorithme et sert de support de présentation.
> Le régénérer en PDF après toute modification de la méthode :
>
> ```bash
> "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
>   --headless --disable-gpu --no-pdf-header-footer \
>   --print-to-pdf=docs/Observatoire-IA-Algorithme.pdf \
>   docs/algorithme.html
> ```
>
> Sous Windows, remplacer par le chemin de `chrome.exe`.
>
> Vérifier que les chiffres cités dans le HTML correspondent au dernier run
> mesuré (prompt 1) avant de régénérer.
