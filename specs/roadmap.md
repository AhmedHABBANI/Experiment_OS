# Roadmap de développement — ExperimentOS

## Principes

Le développement suit quatre règles :

1. construire d’abord le moteur statistique ;
2. garder chaque incrément exécutable et testable ;
3. stabiliser les contrats avant l’interface finale ;
4. valider scientifiquement avant d’améliorer la présentation.

Chaque étape produit du code, des tests, une commande d’exécution, un résultat attendu et une documentation minimale.

---

## Phase 0 — Initialisation

### Objectif

Créer une base propre et reproductible.

### Livrables

- arborescence initiale ;
- `README.md` minimal ;
- `CODEX.md` et `specs/` ;
- `.gitignore` ;
- `pyproject.toml` ;
- projet Vite React ;
- Docker Compose minimal ;
- endpoint `/api/v1/health` ;
- page frontend affichant l’état de l’API.

### Sortie

- `docker compose up --build` fonctionne ;
- le frontend appelle le backend ;
- Ruff, Pytest, ESLint et Vitest sont configurés ;
- un test backend et un test frontend passent.

---

## Phase 1 — Contrats de la bibliothèque statistique

### Objectif

Créer les types communs avant tout calcul.

### Livrables

- enums : métrique, alternative, source ;
- exceptions métier ;
- `StatisticalResult` ;
- intervalle de confiance ;
- avertissements structurés ;
- validation des groupes ;
- normalisation binaire et continue.

### Tests

- groupe vide ;
- valeurs non numériques ;
- binaire invalide ;
- variance nulle ;
- données manquantes ;
- sérialisation.

### Sortie

La bibliothèque est importable sans FastAPI et tous les tests unitaires passent.

---

## Phase 2 — Simulation

### Binaire

Paramètres :

- `n_a`, `n_b` ;
- `p_a`, `p_b` ;
- seed ;
- données manquantes.

### Continue

Distributions :

- normale ;
- exponentielle ;
- lognormale.

Paramètres :

- tailles ;
- moyennes ou paramètres équivalents ;
- écarts-types ;
- seed ;
- données manquantes ;
- outliers ;
- variances différentes.

### Tests

- reproductibilité ;
- tailles ;
- proportions et moyennes empiriques ;
- contamination ;
- paramètres invalides.

### API/UI minimale

- endpoints de simulation ;
- formulaires simples ;
- aperçu ;
- téléchargement CSV.

---

## Phase 3 — Statistiques descriptives

### Binaire

- effectif ;
- succès/échecs ;
- proportion ;
- erreur standard ;
- intervalle ;
- différence absolue ;
- uplift ;
- odds ;
- odds ratio.

### Continue

- moyenne ;
- médiane ;
- variance ;
- écart-type ;
- erreur standard ;
- min/max ;
- quantiles ;
- IQR ;
- différence des moyennes et médianes.

### Graphiques

- taux avec intervalles ;
- histogrammes ;
- boxplots ;
- QQ plots.

### Validation

Comparer NumPy, pandas et Statsmodels sur des cas connus.

---

## Phase 4 — Tests binaires

### Test z de deux proportions

- statistique z ;
- p-value ;
- différence ;
- intervalle ;
- effets ;
- avertissements asymptotiques ;
- comparaison Statsmodels.

### Fisher exact

- tableau 2 × 2 ;
- odds ratio ;
- p-value ;
- gestion des zéros ;
- comparaison SciPy.

### Interprétation

- H0/H1 ;
- décision au seuil ;
- taille d’effet ;
- avertissement sur la non-preuve de H0.

### Monte-Carlo

- faux positifs sous H0 ;
- puissance pour plusieurs écarts.

---

## Phase 5 — Tests continus paramétriques

### Student

- hypothèse de variances égales ;
- t, degrés de liberté, p-value ;
- différence et intervalle ;
- Cohen’s d.

### Welch

- variances différentes ;
- degrés de liberté de Welch–Satterthwaite ;
- différence et intervalle ;
- taille d’effet.

### Diagnostics

- effectifs ;
- variance nulle ;
- déséquilibre ;
- outliers ;
- QQ plots.

### Validation

- comparaison SciPy ;
- cas égaux/inégaux ;
- faux positifs ;
- puissance.

---

## Phase 6 — Méthodes non paramétriques et simulées

### Mann–Whitney

- U ;
- p-value ;
- effet de rang ;
- interprétation prudente.

### Permutation

- différence de moyennes ;
- alternative ;
- seed ;
- nombre de permutations ;
- distribution nulle ;
- p-value empirique.

### Bootstrap

- différence de moyenne ou médiane ;
- seed ;
- réplications ;
- erreur standard ;
- intervalle percentile ;
- distribution bootstrap.

### Validation

- reproductibilité ;
- références disponibles ;
- couverture empirique ;
- stabilité selon le nombre de réplications.

---

## Phase 7 — Import CSV

### Livrables

- upload ;
- aperçu ;
- détection des types ;
- choix du séparateur ;
- mapping groupe A/B ;
- mapping de métrique ;
- mapping binaire vers 0/1 ;
- validation continue ;
- résumé des exclusions ;
- dataset normalisé.

### Sécurité

- limite de taille ;
- validation du type ;
- nettoyage du nom ;
- aucune exécution ;
- messages d’erreur sûrs.

### Tests

- colonnes manquantes ;
- séparateurs ;
- encodage ;
- modalités supplémentaires ;
- conversions impossibles ;
- fichier trop grand.

---

## Phase 8 — Interprétation déterministe

### Livrables

- règles par test ;
- gabarits stables ;
- décision statistique ;
- effet et incertitude ;
- importance pratique ;
- avertissements contextualisés.

### Cas à tester

- p-value sous/au-dessus d’alpha ;
- intervalle traversant zéro ;
- effet faible mais significatif ;
- effet important non significatif ;
- petit échantillon ;
- alternatives unilatérales.

### Sortie

Aucun texte n’affirme que H0 est vraie et aucun LLM n’est utilisé.

---

## Phase 9 — Interface complète

### Pages

- accueil ;
- simulation ;
- import ;
- configuration ;
- analyse ;
- résultats ;
- export.

### Composants

- stepper ;
- cartes ;
- formulaires ;
- tableaux ;
- alertes ;
- sélecteur de test ;
- graphiques Plotly ;
- panneaux d’hypothèses, interprétation et avertissements.

### États

- loading ;
- error ;
- empty ;
- success ;
- calcul long ;
- export en cours.

---

## Phase 10 — Exports

### JSON

Contrat complet avec paramètres, résultats, interprétation et métadonnées.

### CSV

- données analysées ;
- résultats aplatis.

### PDF

- titre et date ;
- source ;
- configuration ;
- résumé des groupes ;
- méthode ;
- résultats ;
- graphiques ;
- interprétation ;
- avertissements ;
- reproductibilité.

### Validation

Les valeurs du PDF et du CSV doivent correspondre au JSON de référence.

---

## Phase 11 — CI et documentation

### CI

- Ruff ;
- Pytest ;
- couverture ;
- ESLint ;
- Vitest ;
- build Vite ;
- builds Docker ;
- validation Docker Compose.

### Documentation

- README ;
- guide CSV ;
- guide des méthodes ;
- guide d’interprétation ;
- exemples ;
- captures ;
- commandes de développement.

### Stabilisation

- erreurs ;
- accessibilité ;
- dépendances ;
- performances ;
- logs ;
- absence de persistance.

---

## Phase 11.5 — Refonte visuelle du workspace

### Direction

- interface professionnelle, sobre et propre à un outil d'analyse statistique ;
- identité visuelle ExperimentOS plus affirmée sans composition marketing ;
- hiérarchie claire entre configuration, données, résultats et interprétation ;
- densité maîtrisée pour permettre la lecture et la comparaison répétées ;
- cohérence complète sur desktop, tablette et mobile.

### Système visuel

- palette fonctionnelle avec couleurs distinctes pour A, B, succès, prudence et erreur ;
- typographie, espacements, bordures, ombres et rayons harmonisés ;
- boutons, champs, contrôles segmentés, badges et tableaux cohérents ;
- états hover, focus, disabled, loading, empty, success et error soignés ;
- iconographie Lucide utilisée uniquement lorsqu'elle améliore le repérage.

### Workspace

- en-tête produit compact et immédiatement identifiable ;
- configuration mieux découpée sans masquer les paramètres statistiques ;
- actions principales et secondaires hiérarchisées ;
- résultats organisés pour faire ressortir décision, effet, incertitude et avertissements ;
- graphiques intégrés visuellement au reste de l'interface ;
- import CSV et exports alignés avec le même langage visuel.

### Contraintes

- aucune modification des calculs statistiques ou des contrats API ;
- aucune persistance, authentification ou dépendance externe métier ;
- aucune landing page ajoutée devant le workspace ;
- accessibilité clavier, contrastes et résumés textuels préservés ;
- pas de dépendance frontend supplémentaire sans besoin démontré.

### Validation

- tests frontend adaptés aux composants ou interactions modifiés ;
- ESLint, Vitest et build Vite réussis ;
- contrôle visuel réel sur desktop et mobile ;
- absence de débordement, chevauchement ou texte tronqué ;
- parcours simulation, import, analyse et export toujours utilisables.

### Critère de sortie

Le workspace est visuellement cohérent, agréable et crédible comme produit professionnel,
sans réduction de sa précision statistique ni régression fonctionnelle ou d'accessibilité.

---

## Phase 12 — Version portfolio

### Livrables

- README orienté recruteur ;
- diagramme d’architecture ;
- captures ou GIF ;
- résultats Monte-Carlo ;
- section `Statistical safeguards` ;
- section `Engineering decisions` ;
- section `Future work`.

### Critère final

Un lecteur comprend en moins de deux minutes :

- le problème ;
- les méthodes ;
- l’architecture ;
- les garanties scientifiques ;
- le lancement ;
- la différence avec un notebook.

---

## Première séquence recommandée

Nous commencerons ainsi :

1. initialiser le dépôt ;
2. créer le package statistique ;
3. définir `StatisticalResult` ;
4. créer les validations communes ;
5. écrire les premiers tests ;
6. ajouter ensuite FastAPI et React.

Cette séquence évite de construire une interface sur des contrats instables.
