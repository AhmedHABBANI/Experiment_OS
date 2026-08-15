# Guide d'import CSV

ExperimentOS importe un fichier CSV en mémoire, affiche un aperçu, puis demande un
mapping manuel avant de produire deux échantillons A/B normalisés. Le fichier et les
données ne sont pas conservés après la requête ou la session.

## Format accepté

Un fichier importable doit respecter les règles suivantes :

- extension `.csv` ;
- encodage UTF-8, avec ou sans marque BOM ;
- au moins une ligne d'en-tête et une ligne de données ;
- noms de colonnes non vides et uniques après suppression des espaces externes ;
- taille maximale de 5 Mio par défaut ;
- séparateur virgule, point-virgule, tabulation ou barre verticale (`|`).

Le séparateur peut être détecté automatiquement à partir des 8 192 premiers
caractères ou choisi explicitement. La limite de taille peut être modifiée avec la
variable d'environnement `EXPERIMENTOS_MAX_CSV_BYTES`, exprimée en octets. Une
valeur absente, non numérique, nulle ou négative conserve la limite de 5 Mio.

Le nom affiché est nettoyé et réduit à son nom de fichier : les composants de chemin
transmis par un navigateur ne sont jamais utilisés.

## Aperçu

L'étape `Preview CSV` appelle `POST /api/v1/datasets/preview` et retourne :

- le nom nettoyé et la taille du fichier ;
- le séparateur retenu ;
- le nombre total de lignes ;
- les colonnes, leur type inféré et leur nombre de valeurs manquantes ;
- les dix premières lignes au maximum.

Les types d'aperçu sont `boolean`, `integer`, `number` et `string`. Cette inférence
sert uniquement à présenter le fichier. Le type statistique faisant autorité est
choisi manuellement pendant le mapping.

## Mapping A/B

L'étape `Validate dataset` appelle `POST /api/v1/datasets/validate`. Il faut fournir :

| Champ | Rôle |
| --- | --- |
| Group column | Colonne qui contient l'affectation expérimentale. |
| Group A value | Modalité affectée au groupe de contrôle A. |
| Group B value | Modalité affectée au traitement B. |
| Metric column | Colonne qui contient la métrique analysée. |
| Metric type | `binary` ou `continuous`. |

La colonne de groupe et la colonne de métrique doivent être différentes. Les deux
modalités A/B doivent être non vides et distinctes. Toute autre modalité de groupe
est exclue, elle ne crée jamais un troisième groupe.

### Métrique binaire

Il faut aussi indiquer deux modalités distinctes :

- `Success value (1)` devient `1.0` ;
- `Failure value (0)` devient `0.0`.

La comparaison des modalités binaires ignore la casse : `yes`, `YES` et `Yes` sont
équivalents. Une autre valeur est exclue comme métrique invalide.

Exemple fourni : [`examples/binary_ab.csv`](../examples/binary_ab.csv).

| Mapping | Valeur |
| --- | --- |
| Group column | `variant` |
| Group A value | `control` |
| Group B value | `treatment` |
| Metric column | `converted` |
| Metric type | `binary` |
| Success value | `yes` |
| Failure value | `no` |

Résultat normalisé attendu : A = `[0, 1, 0, 1]`, B = `[1, 0, 1, 1]`.

### Métrique continue

Chaque valeur retenue doit pouvoir être convertie en nombre fini. Les booléens, le
texte non numérique, `NaN` et les valeurs infinies sont exclus comme métriques
invalides.

Exemple fourni : [`examples/continuous_ab.csv`](../examples/continuous_ab.csv).

| Mapping | Valeur |
| --- | --- |
| Group column | `variant` |
| Group A value | `control` |
| Group B value | `treatment` |
| Metric column | `revenue` |
| Metric type | `continuous` |

Résultat normalisé attendu : A = `[42.5, 38, 51.25, 46]`, B =
`[49, 55.5, 47.75, 60]`.

## Exclusions et sortie normalisée

Les lignes sont examinées dans l'ordre du fichier. Une ligne peut être exclue pour
un seul motif, selon cette priorité :

| Motif | Signification |
| --- | --- |
| `missing_group` | La valeur de groupe est absente. |
| `unmapped_group` | La valeur ne correspond ni à A ni à B. |
| `missing_metric` | La métrique est absente pour une ligne A/B. |
| `invalid_metric` | La métrique ne correspond pas au mapping binaire ou n'est pas un nombre continu fini. |

La réponse contient `group_a`, `group_b` et des métadonnées avec les nombres de
lignes initiales, retenues et exclues, le détail des exclusions et le mapping
appliqué. Les métriques binaires et continues sont retournées sous forme de nombres
flottants. Les deux groupes doivent conserver au moins une observation valide.

Le jeu plus réaliste
[`data/test1/conversion_checkout.csv`](../data/test1/conversion_checkout.csv)
contient volontairement trois anomalies. Sa
[`description`](../data/test1/description.md) détaille le cas d'usage et le résumé
d'exclusion attendu.

## Erreurs fréquentes

| Code | Cause principale |
| --- | --- |
| `INVALID_FILE_TYPE` | Extension ou type MIME non accepté. |
| `FILE_TOO_LARGE` | Limite d'octets dépassée. |
| `INVALID_ENCODING` | Contenu non UTF-8. |
| `INVALID_DELIMITER` | Séparateur explicite non pris en charge. |
| `DELIMITER_DETECTION_FAILED` | Détection automatique non fiable. |
| `MISSING_COLUMNS` | En-tête vide ou colonne mappée absente. |
| `DUPLICATE_COLUMNS` | Plusieurs colonnes ont le même nom. |
| `INVALID_MAPPING` | Même colonne choisie pour le groupe et la métrique. |
| `INVALID_GROUP_MAPPING` | Modalités A/B vides ou identiques. |
| `INVALID_BINARY_MAPPING` | Modalités succès/échec vides ou identiques. |
| `INSUFFICIENT_GROUP_DATA` | A ou B ne conserve aucune observation valide. |

Les CSV sont considérés comme non fiables : leur contenu est uniquement décodé et
analysé comme données tabulaires. ExperimentOS n'exécute aucune cellule ou formule
et n'envoie aucun contenu vers un service externe.
