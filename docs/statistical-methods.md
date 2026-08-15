# Guide des méthodes statistiques

ExperimentOS propose sept méthodes fréquentistes pour comparer deux groupes
indépendants A et B sur une seule métrique. L'application ne choisit jamais une
méthode automatiquement : l'utilisateur sélectionne le test après avoir examiné le
type de métrique, le plan expérimental, les diagnostics et les hypothèses.

Ce guide décrit l'implémentation actuelle. Il ne remplace ni la conception correcte
d'une expérience, ni une analyse métier de l'importance pratique du résultat.

## Convention commune

La direction de référence est toujours **groupe B moins groupe A** :

- binaire : proportion B moins proportion A ;
- continu : moyenne B moins moyenne A ;
- permutation : moyenne B moins moyenne A ;
- bootstrap : moyenne ou médiane B moins moyenne ou médiane A.

Une estimation positive favorise donc B sur l'échelle de la métrique. Une valeur
négative favorise A. Cette convention ne dit pas qu'une hausse est souhaitable :
pour une métrique comme le temps d'erreur, une différence négative peut être le but.

### Alternatives

| Valeur | Hypothèse alternative exprimée avec la convention B - A |
| --- | --- |
| `two-sided` | B diffère de A dans l'une ou l'autre direction. |
| `greater` | B est supérieur à A. |
| `less` | B est inférieur à A. |

L'alternative doit être choisie avant de regarder le résultat. Utiliser une
alternative unilatérale après observation des données invalide l'interprétation
nominale de la p-value.

### Contrat de résultat

Les analyses renvoient un `StatisticalResult` commun : nom du test, type de
métrique, statistique, p-value lorsqu'elle existe, alpha, alternative, estimation,
intervalle de confiance lorsqu'il existe, taille d'effet, décision, hypothèses,
avertissements, interprétation déterministe et métadonnées de reproductibilité.

`reject_null = true` signifie uniquement que la p-value est inférieure ou égale à
`alpha`. Une décision de non-rejet ne prouve jamais que H0 est vraie ou que les
groupes sont identiques.

## Vue d'ensemble

| Méthode | Métrique | Quantité principalement comparée | Incertitude / effet |
| --- | --- | --- | --- |
| Test z de deux proportions | Binaire | Proportions | IC de Wald, odds ratio, risk ratio |
| Test exact de Fisher | Binaire | Tableau 2 x 2 | Odds ratio, pas d'IC dans la V1 |
| Test t de Student | Continue | Moyennes, variances égales | IC t poolé, Cohen's d |
| Test t de Welch | Continue | Moyennes, variances libres | IC de Welch, Cohen's d |
| Mann–Whitney U | Continue | Distribution des rangs | Corrélation bisérielle de rang |
| Test de permutation | Continue | Différence de moyennes | Distribution nulle et p-value empirique |
| Bootstrap de différence | Continue | Différence de moyenne ou médiane | Erreur standard et IC percentile |

Cette table décrit les méthodes, elle ne constitue pas un moteur de sélection.

## 1. Test z de deux proportions

**Nom interne :** `two_proportion_z_test`  
**Endpoint :** `POST /api/v1/analyses/two-proportion-z`

Le test compare les taux de succès de deux échantillons binaires indépendants.

- H0 bilatérale : la proportion de succès de B est égale à celle de A.
- Estimation : `p_B - p_A`.
- Statistique : z calculé avec une proportion poolée sous H0.
- Intervalle : intervalle de Wald non poolé pour `p_B - p_A`.
- Taille d'effet principale : odds ratio lorsqu'il est fini.
- Métadonnées : risk ratio, proportions, succès, effectifs et direction.

L'approximation normale suppose des observations indépendantes et des comptes
attendus suffisamment grands. ExperimentOS produit `SMALL_EXPECTED_COUNT` lorsque
le minimum des quatre comptes attendus est inférieur à 5. Un odds ratio non fini
est retourné comme `None` plutôt que comme une valeur JSON infinie.

## 2. Test exact de Fisher

**Nom interne :** `fisher_exact_test`  
**Endpoint :** `POST /api/v1/analyses/fisher-exact`

Fisher évalue l'association entre le groupe et le résultat binaire à partir du
tableau de contingence 2 x 2. L'implémentation délègue le calcul exact à SciPy.

- H0 bilatérale : l'affectation A/B et le résultat succès/échec sont indépendants.
- Statistique et taille d'effet : odds ratio de B par rapport à A.
- Métadonnées : tableau `[B, A]`, risk ratio et différence `p_B - p_A`.
- Intervalle de confiance : non fourni dans la V1.

Le test est exact pour la p-value conditionnelle et ne repose pas sur
l'approximation normale du test z. Cela ne rend pas l'odds ratio toujours défini :
une cellule nulle peut produire `NON_FINITE_ODDS_RATIO` et une taille d'effet `None`.

## 3. Test t de Student

**Nom interne :** `student_t_test`  
**Endpoint :** `POST /api/v1/analyses/student-t`

Le test compare les moyennes de deux groupes continus indépendants en supposant une
variance commune.

- H0 bilatérale : les moyennes de B et A sont égales.
- Estimation : `moyenne_B - moyenne_A`.
- Variance : estimation poolée des deux groupes.
- Degrés de liberté : `n_A + n_B - 2`.
- Intervalle : intervalle t basé sur la variance poolée.
- Taille d'effet : Cohen's d avec écart-type poolé.

Les observations doivent être indépendantes, la métrique doit être quantitative et
le modèle suppose des variances égales. Une variance poolée nulle rend le calcul
indéfini. Les avertissements signalent aussi les tailles très déséquilibrées et les
valeurs atypiques détectées par les barrières IQR à 1,5 fois l'IQR.

## 4. Test t de Welch

**Nom interne :** `welch_t_test`  
**Endpoint :** `POST /api/v1/analyses/welch-t`

Welch compare également les moyennes, sans imposer l'égalité des variances.

- H0 bilatérale : les moyennes de B et A sont égales.
- Estimation : `moyenne_B - moyenne_A`.
- Erreur standard : calculée avec une variance propre à chaque groupe.
- Degrés de liberté : approximation de Welch–Satterthwaite.
- Intervalle : intervalle t de Welch.
- Taille d'effet : Cohen's d calculé avec une variance poolée dédiée à l'effet.

Les observations restent supposées indépendantes. Welch tolère des variances et
tailles différentes, mais ne neutralise pas automatiquement l'asymétrie sévère, les
outliers ou une mauvaise conception expérimentale. Les mêmes avertissements IQR et
de déséquilibre d'effectifs que Student sont retournés.

## 5. Mann–Whitney U

**Nom interne :** `mann_whitney_u_test`  
**Endpoint :** `POST /api/v1/analyses/mann-whitney`

Mann–Whitney compare les distributions de rang de deux groupes indépendants.
ExperimentOS rapporte la statistique U du groupe B.

- H0 bilatérale : les distributions de rang ne montrent pas de déplacement entre B
  et A.
- Statistique : U pour B, calculée avec la méthode automatique de SciPy.
- Taille d'effet : corrélation bisérielle de rang.
- Métadonnée complémentaire : probabilité de supériorité de B sur A.
- Intervalle de confiance : non fourni dans la V1.

Ce test n'est pas automatiquement un test de différence des médianes. Cette lecture
nécessite des hypothèses supplémentaires sur la forme des distributions. Le warning
`MANN_WHITNEY_NOT_MEDIAN_TEST` est donc toujours présent; `TIES_PRESENT` s'ajoute
quand des ex æquo sont détectés.

## 6. Test de permutation de la moyenne

**Nom interne :** `permutation_mean_test`  
**Endpoint :** `POST /api/v1/analyses/permutation`

Le test mélange les étiquettes A/B pour construire une distribution nulle empirique
de la différence de moyennes.

- H0 : les observations sont échangeables entre A et B sous l'absence d'effet.
- Statistique observée : `moyenne_B - moyenne_A`.
- Répétitions : de 100 à 100 000, 10 000 par défaut dans l'API.
- P-value : proportion empirique avec correction Monte-Carlo `(+1)/(N+1)`.
- Intervalle de confiance et taille d'effet standardisée : non fournis dans la V1.

La seed doit être un entier ou `None`. Une seed fixe reproduit exactement la
distribution nulle et la p-value. Plus de permutations réduisent la granularité et
la variabilité Monte-Carlo, au prix d'un temps de calcul supérieur.

## 7. Bootstrap de différence

**Noms internes :** `bootstrap_mean_difference` et
`bootstrap_median_difference`  
**Endpoint :** `POST /api/v1/analyses/bootstrap-difference`

Le bootstrap rééchantillonne séparément A et B avec remise afin d'estimer
l'incertitude de `statistique_B - statistique_A`. Le paramètre `statistic` choisit
`mean` ou `median`.

- Estimation : différence observée de moyennes ou de médianes.
- Répétitions : de 100 à 100 000, 10 000 par défaut dans l'API.
- Incertitude : écart-type de la distribution bootstrap.
- Intervalle : percentile bilatéral au niveau demandé, 95 % par défaut.
- Reproductibilité : seed entière ou `None`.
- P-value et décision de rejet : non applicables dans cette procédure V1.

L'intervalle percentile est simple et reproductible, mais il ne corrige ni le biais
ni l'accélération. Avec de petits échantillons, des distributions très asymétriques
ou des queues lourdes, sa couverture peut s'écarter du niveau nominal. Le bootstrap
n'efface pas non plus une dépendance entre observations : le rééchantillonnage V1
suppose des observations indépendantes dans chaque groupe.

## Avertissements communs

Un avertissement ne sélectionne pas une autre méthode et n'annule pas
automatiquement le résultat. Il signale une condition à examiner :

| Code | Méthodes | Signification |
| --- | --- | --- |
| `SMALL_EXPECTED_COUNT` | z proportions | Approximation normale fragile. |
| `NON_FINITE_ODDS_RATIO` | Fisher | Odds ratio non représentable comme nombre fini. |
| `IMBALANCED_SAMPLE_SIZES` | Student, Welch | Rapport entre effectifs au moins égal à 4. |
| `IQR_OUTLIERS_DETECTED` | Student, Welch | Valeurs hors des barrières IQR détectées. |
| `MANN_WHITNEY_NOT_MEDIAN_TEST` | Mann–Whitney | Le test porte sur les rangs, pas automatiquement sur les médianes. |
| `TIES_PRESENT` | Mann–Whitney | Des ex æquo influencent le calcul des rangs. |

Les diagnostics et avertissements doivent être lus avec le contexte métier. Ils ne
sont ni une preuve de validité ni une règle automatique de remplacement du test.

## Validation scientifique du projet

Les implémentations analytiques sont comparées à Statsmodels ou SciPy. Les méthodes
simulées sont testées pour la reproductibilité des seeds, la stabilité, la couverture
et leur accord avec des références disponibles. Des tests Monte-Carlo vérifient
également les taux de faux positifs et la puissance sur des scénarios contrôlés.

Ces validations contrôlent le moteur, mais ne garantissent pas qu'un jeu de données
réel respecte l'indépendance, l'assignation aléatoire, l'absence de biais de mesure ou
la pertinence pratique de la métrique.
