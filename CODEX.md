# CODEX.md — ExperimentOS

## Mission

ExperimentOS est une plateforme locale permettant de simuler, importer, analyser, expliquer et exporter des expériences A/B. Le dépôt doit démontrer une compréhension réelle des statistiques, une architecture full-stack propre et une validation scientifique reproductible.

Le système comprend :

1. une bibliothèque Python statistique indépendante ;
2. une API FastAPI ;
3. un frontend React ;
4. une exécution locale avec Docker Compose.

La V1 ne comporte ni base de données, ni authentification, ni stockage permanent, ni déploiement cloud.

## Documents faisant autorité

Lire avant toute modification importante :

- `specs/cahier-des-charges.md`
- `specs/repository-architecture.yaml`
- `specs/roadmap.md`

Ordre de priorité en cas de contradiction :

1. décisions explicites de l’utilisateur ;
2. `CODEX.md` ;
3. cahier des charges ;
4. architecture YAML ;
5. roadmap ;
6. code existant.

Ne jamais modifier silencieusement une décision verrouillée. Toute proposition de changement doit exposer le problème, les options, la recommandation et les conséquences.

## Périmètre V1

### Expériences et données

- expériences A/B uniquement ;
- un groupe contrôle A et un groupe traitement B ;
- une métrique analysée à la fois ;
- métriques binaires et continues ;
- simulation paramétrable ;
- import CSV avec mapping manuel des colonnes ;
- aucune persistance entre les sessions.

### Approche statistique

La V1 est fréquentiste. L’utilisateur choisit manuellement le test. L’application peut afficher des conditions d’utilisation et des avertissements, mais ne sélectionne jamais automatiquement le test.

Tests prévus :

- test z pour deux proportions ;
- test exact de Fisher ;
- test t de Student ;
- test t de Welch ;
- test de Mann–Whitney ;
- test de permutation ;
- bootstrap de la différence.

### Résultats attendus

Lorsque cela est applicable, chaque analyse retourne :

- H0 et H1 ;
- statistique de test ;
- p-value ;
- niveau alpha ;
- estimation de l’effet ;
- intervalle de confiance ;
- taille d’effet ;
- décision statistique ;
- hypothèses et avertissements ;
- interprétation déterministe ;
- distinction entre significativité statistique et importance pratique.

Aucun LLM n’est utilisé dans la V1.

## Stack verrouillée

### Python

- Python 3.12
- NumPy, pandas, SciPy, Statsmodels
- FastAPI, Pydantic
- Pytest, Ruff

### Frontend

- React
- Vite
- JavaScript
- Tailwind CSS
- shadcn/ui
- Plotly.js avec `react-plotly.js`
- Vitest, React Testing Library, ESLint

### Exécution et qualité

- Docker et Docker Compose
- un conteneur backend
- un conteneur frontend
- GitHub Actions pour lint, tests, couverture, builds Docker et validation Compose

## Principes d’architecture

### Séparation des responsabilités

La bibliothèque statistique ne dépend pas de FastAPI.

Le backend :

- valide les requêtes ;
- normalise les entrées ;
- appelle la bibliothèque ;
- sérialise les résultats ;
- génère les exports.

Le frontend :

- gère les formulaires et la navigation ;
- appelle l’API ;
- affiche résultats, graphiques et erreurs ;
- ne contient aucun calcul statistique faisant autorité.

### Contrat de résultat commun

Tous les tests retournent une structure stable proche de :

```python
StatisticalResult(
    test_name="welch_t_test",
    metric_type="continuous",
    statistic=2.41,
    p_value=0.017,
    alpha=0.05,
    alternative="two-sided",
    estimate=1.84,
    confidence_interval=(0.34, 3.33),
    effect_size=0.28,
    effect_size_name="cohens_d",
    reject_null=True,
    assumptions=[],
    warnings=[],
    interpretation={},
    metadata={},
)
```

Les champs non applicables peuvent valoir `None`.

### Reproductibilité

Toute simulation, permutation ou procédure bootstrap accepte une seed. Les exports incluent les paramètres, la seed, la version de l’application, la date, le test et ses options.

### Validation scientifique

Comparer aux résultats de SciPy ou Statsmodels lorsque possible. Couvrir :

- cas analytiques connus ;
- comparaisons numériques ;
- taux de faux positifs sous H0 ;
- puissance empirique sous H1 ;
- couverture des intervalles ;
- stabilité des méthodes simulées ;
- reproductibilité avec seed fixe.

## Non-objectifs V1

Ne pas introduire :

- base de données ;
- comptes utilisateurs ;
- microservices ;
- Kubernetes ;
- file de messages ;
- LLM ;
- architecture de plugins ;
- méthodes bayésiennes ;
- A/B/n ;
- tests séquentiels ;
- intégrations externes.

## Règles pour Codex

Pour chaque tâche :

1. lire `CODEX.md` et les spécifications concernées ;
2. résumer la compréhension ;
3. annoncer les fichiers ciblés ;
4. effectuer un changement limité ;
5. ajouter ou mettre à jour les tests ;
6. exécuter les validations pertinentes ;
7. lister les fichiers modifiés, commandes exécutées, résultats et limites.

Codex ne doit pas :

- réécrire une grande partie du dépôt sans nécessité ;
- ajouter une dépendance sans justification ;
- déplacer la logique statistique vers les routes ou React ;
- masquer une erreur avec un `try/except` trop large ;
- dupliquer les calculs ;
- inventer des validations ;
- modifier une décision verrouillée sans discussion.

## Standards de code

### Python

- code et identifiants en anglais ;
- type hints sur les fonctions publiques ;
- docstrings utiles ;
- erreurs métier explicites ;
- Pydantic pour l’API ;
- modèles dédiés pour les résultats internes ;
- fonctions courtes ;
- aucune logique scientifique majeure dans les routes.

### JavaScript

- composants fonctionnels et hooks ;
- appels API isolés ;
- composants de graphiques séparés ;
- validation des formulaires ;
- états `loading`, `error`, `empty` et `success` explicites ;
- aucun calcul scientifique critique dans le navigateur.

## Gestion des erreurs

Prévoir des codes d’erreur stables pour :

- données invalides ;
- CSV invalide ;
- colonne ou groupe manquant ;
- type de métrique incompatible ;
- échantillon insuffisant ;
- variance nulle ;
- calcul non défini ;
- export impossible ;
- erreur interne.

Une erreur API contient un code, un message lisible, des détails contrôlés et, si possible, une action corrective.

## Définition de terminé

Une fonctionnalité n’est terminée que lorsque :

- le comportement est défini ;
- le code est implémenté ;
- les erreurs sont gérées ;
- les tests sont présents ;
- la documentation est à jour (dans STATUS.md);
- le contrat API est cohérent ;
- l’interface est utilisable ;
- les validations passent.


