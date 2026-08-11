# Test 1 - Conversion d'un checkout e-commerce

## Cas d'usage reel

Une equipe e-commerce teste une nouvelle version de son tunnel de paiement. Les visiteurs sont repartis entre :

- `control` : checkout actuel ;
- `treatment` : nouveau checkout simplifie.

La metrique principale est la conversion : un visiteur a-t-il termine son achat ? Il s'agit donc d'une metrique binaire.

## Fichier

`conversion_checkout.csv` contient une ligne par visiteur et les colonnes suivantes :

| Colonne | Description |
| --- | --- |
| `visitor_id` | Identifiant fictif du visiteur. |
| `variant` | Variante d'experience recue par le visiteur. |
| `converted` | Resultat de conversion : `yes` ou `no`. |
| `device` | Type d'appareil, fourni comme contexte mais non analyse dans ce test. |
| `country` | Pays du visiteur, fourni comme contexte mais non analyse dans ce test. |

Toutes les donnees sont synthetiques et ne representent aucune personne reelle.

## Mapping dans ExperimentOS

Utiliser les parametres suivants :

| Parametre | Valeur |
| --- | --- |
| Separateur | Virgule, ou detection automatique |
| Colonne du groupe | `variant` |
| Modalite A | `control` |
| Modalite B | `treatment` |
| Colonne de metrique | `converted` |
| Type de metrique | `binary` |
| Valeur de succes (1) | `yes` |
| Valeur d'echec (0) | `no` |

## Problemes de qualite introduits volontairement

Trois lignes permettent de verifier la validation et le resume des exclusions :

- `V0021` appartient a la modalite supplementaire `holdout` et doit etre exclu comme groupe non mappe ;
- `V0022` ne contient aucune valeur de conversion et doit etre exclu comme metrique manquante ;
- `V0023` contient la modalite `pending`, qui ne correspond ni a `yes` ni a `no`, et doit etre exclu comme metrique invalide.

## Resultat attendu apres validation

- 24 lignes initiales ;
- 21 observations retenues ;
- groupe A : 10 observations ;
- groupe B : 11 observations ;
- 3 observations exclues ;
- motifs : 1 groupe non mappe, 1 metrique manquante et 1 metrique invalide.

Dans les observations retenues, le groupe A comporte 3 conversions sur 10 et le groupe B 7 conversions sur 11. Ce petit echantillon sert a tester le parcours d'import et non a tirer une conclusion produit fiable.
