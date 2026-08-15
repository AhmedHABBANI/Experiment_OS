# Guide d'interprétation déterministe

ExperimentOS transforme chaque résultat statistique en sections textuelles stables,
sans LLM et sans génération libre. L'objectif est d'expliquer le calcul sans dépasser
ce que les données et la méthode permettent de conclure.

## Les huit éléments d'une interprétation

Une interprétation complète expose :

1. la question statistique ;
2. l'hypothèse nulle H0 ;
3. l'hypothèse alternative H1 ;
4. la décision au seuil alpha ;
5. l'effet observé, orienté B moins A ;
6. l'incertitude disponible ;
7. l'importance pratique ;
8. le contexte des avertissements.

Les mêmes entrées produisent exactement les mêmes phrases. La seed influence les
résultats simulés de permutation ou bootstrap, mais pas les règles de rédaction.

## Décision statistique

Pour un test d'hypothèse, ExperimentOS compare la p-value au seuil `alpha` :

- si `p < alpha`, les données fournissent suffisamment d'éléments pour rejeter H0 ;
- sinon, elles ne fournissent pas suffisamment d'éléments pour rejeter H0.

Le second cas n'accepte pas H0. Une p-value supérieure au seuil peut être compatible
avec un effet trop faible, un échantillon trop petit, une forte variabilité ou une
absence réelle d'effet. Le test seul ne permet pas de choisir entre ces explications.

La p-value n'est ni la probabilité que H0 soit vraie, ni la probabilité que le résultat
se reproduise. Elle mesure la compatibilité des données avec le modèle nul, selon la
statistique et les hypothèses du test.

## Effet et direction

Les différences sont orientées `B - A` :

- valeur positive : B est plus élevé sur l'échelle analysée ;
- valeur négative : B est plus faible ;
- valeur nulle : égalité observée dans l'échantillon.

Une direction positive n'est pas automatiquement bénéfique. Le sens produit dépend
de la métrique. ExperimentOS rapporte également une taille d'effet standardisée ou
relative lorsqu'elle est disponible, par exemple Cohen's d, l'odds ratio ou la
corrélation bisérielle de rang.

## Intervalle et incertitude

Un intervalle de confiance décrit un ensemble de valeurs compatibles avec les données
et la procédure au niveau choisi. ExperimentOS indique s'il :

- traverse zéro et reste compatible avec plusieurs directions d'effet ;
- se trouve entièrement au-dessus de zéro ;
- se trouve entièrement au-dessous de zéro.

Il ne signifie pas qu'il existe, après observation, une probabilité de 95 % que le
paramètre fixe soit dans cet intervalle. Fisher et Mann–Whitney ne fournissent pas
d'intervalle pour leur effet dans la V1; l'interprétation le dit explicitement.

La permutation décrit l'incertitude Monte-Carlo de la p-value et sa résolution
minimale, pas un intervalle de la différence. Le bootstrap fournit un intervalle
percentile et une erreur standard, mais aucune p-value ni décision de rejet.

## Significativité pratique

La significativité statistique répond à une question de compatibilité avec H0. Elle
ne dit pas si l'effet est assez grand pour justifier une décision produit.

La V1 ne reçoit pas encore de seuil pratique dans le contrat d'analyse. Elle affiche
donc systématiquement que l'importance pratique n'a pas été évaluée. Il faut comparer
séparément l'estimation et son intervalle à un seuil métier défini avant l'analyse.

Un petit effet peut être statistiquement significatif avec beaucoup de données. Un
effet potentiellement important peut rester non significatif avec une estimation
imprécise. Ces situations ne sont pas contradictoires.

## Avertissements

Les warnings structurés sont ajoutés à l'interprétation sans modifier automatiquement
la décision ou sélectionner un autre test. Ils demandent un examen humain : petits
comptes attendus, outliers IQR, déséquilibre des tailles, ex æquo ou portée exacte de
Mann–Whitney.

Un warning ne prouve pas que le résultat est faux. Son absence ne prouve pas que le
plan expérimental, la mesure ou l'indépendance sont valides.

## Exemples représentatifs

### Résultat significatif, effet positif

Supposons `B - A = 0,04`, `p = 0,012`, `alpha = 0,05` et un intervalle
`[0,01 ; 0,07]`. L'interprétation rejette H0 au seuil choisi, décrit B comme supérieur
de 4 points de pourcentage et précise que l'intervalle reste au-dessus de zéro. Elle
ne déclare pas que le traitement fonctionne avec certitude ni qu'il est rentable.

### Résultat non significatif, intervalle large

Supposons `B - A = 2,5`, `p = 0,18` et un intervalle `[-1,2 ; 6,2]`. L'interprétation
ne rejette pas H0 et souligne que l'intervalle reste compatible avec une baisse, une
absence d'effet ou une hausse. Elle ne conclut pas que les groupes sont identiques.

### Effet faible mais significatif

Supposons une différence moyenne de `0,1` unité, un intervalle `[0,04 ; 0,16]` et une
p-value faible. La décision statistique peut rejeter H0, mais l'importance pratique
reste non évaluée tant qu'aucun seuil métier n'est comparé à cet effet.

### Bootstrap

Supposons une différence médiane de `3` unités et un intervalle percentile
`[0,5 ; 5,8]`. ExperimentOS décrit l'estimation et l'incertitude, mais ne transforme
pas le fait que l'intervalle exclut zéro en test d'hypothèse implicite.

## Formulations interdites

Ne pas reformuler un résultat ExperimentOS ainsi :

- « H0 est vraie » ;
- « les groupes sont identiques » ;
- « le traitement fonctionne avec certitude » ;
- « la p-value est la probabilité que le résultat soit dû au hasard » ;
- « non significatif signifie aucun effet » ;
- « statistiquement significatif signifie important pour le produit » ;
- « Mann–Whitney prouve une différence de médianes » sans hypothèses supplémentaires.

Une conclusion correcte conserve la décision conditionnelle au seuil, la direction
et l'amplitude estimées, l'incertitude, les hypothèses et les avertissements.
