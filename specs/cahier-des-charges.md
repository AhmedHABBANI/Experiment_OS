# Cahier des charges — ExperimentOS V1

## 1. Finalité

ExperimentOS est une application locale d’expérimentation statistique. Elle permet de simuler ou importer une expérience A/B, d’examiner les données, de choisir manuellement une méthode fréquentiste, d’interpréter les résultats et de les exporter.

Chaîne fonctionnelle :

```text
configuration
→ simulation ou import
→ validation
→ statistiques descriptives
→ choix manuel du test
→ analyse
→ interprétation
→ visualisation
→ export
```

Le projet doit démontrer une maîtrise des statistiques fondamentales, de l’incertitude, de la reproductibilité et de l’ingénierie full-stack.

## 2. Objectifs

### Fonctionnels

L’utilisateur doit pouvoir :

1. choisir entre simulation et import CSV ;
2. configurer une expérience A/B ;
3. travailler avec une métrique binaire ou continue ;
4. sélectionner lui-même un test ;
5. consulter statistiques descriptives et diagnostics ;
6. exécuter l’analyse ;
7. visualiser les résultats ;
8. exporter JSON, CSV et PDF.

### Scientifiques

Le système doit :

- calculer correctement les statistiques ;
- exposer les hypothèses de la méthode ;
- fournir l’incertitude et une taille d’effet ;
- éviter les conclusions abusives ;
- distinguer significativité statistique et importance pratique ;
- signaler les limites et conditions fragiles.

### Techniques

Le système doit :

- séparer moteur statistique, API et interface ;
- fonctionner avec Docker Compose ;
- être couvert par des tests ;
- ne conserver aucune donnée ;
- être reproductible ;
- rester extensible vers une future approche bayésienne.

## 3. Périmètre

### Inclus

- A/B uniquement ;
- métriques binaires et continues ;
- simulation ;
- import CSV ;
- mapping manuel ;
- tests fréquentistes ;
- graphiques interactifs ;
- interprétations déterministes ;
- exports JSON, CSV, PDF ;
- exécution locale ;
- CI GitHub Actions.

### Exclu

- authentification ;
- base de données ;
- historique ;
- cloud ;
- A/B/n ;
- tests séquentiels ;
- Bayes ;
- analyse causale avancée ;
- intégrations produit ;
- LLM ;
- traitement distribué.

## 4. Parcours utilisateur

### 4.1 Accueil

Deux entrées :

- `Simulate an experiment`
- `Import a CSV`

Afficher aussi les limites du produit et l’absence de stockage permanent.

### 4.2 Simulation

#### Paramètres communs

- nom facultatif ;
- taille de A ;
- taille de B ;
- seed ;
- type de métrique.

#### Métrique binaire

- probabilité de succès de A ;
- probabilité de succès de B ou effet absolu ;
- taux de valeurs manquantes.

#### Métrique continue

- distribution ;
- moyenne de A ;
- moyenne de B ou effet ;
- écart-type de A ;
- écart-type de B ;
- taux de valeurs manquantes ;
- proportion d’outliers ;
- intensité des outliers ;
- asymétrie lorsque disponible.

Distributions initiales :

- normale ;
- exponentielle ;
- lognormale.

Sorties :

- aperçu tabulaire ;
- statistiques descriptives ;
- histogramme ;
- boxplot ;
- QQ plot lorsque pertinent ;
- téléchargement CSV.

### 4.3 Import CSV

#### Import

- extension `.csv` ;
- taille maximale configurable ;
- UTF-8 privilégié ;
- séparateur détecté ou sélectionnable.

#### Aperçu

Afficher :

- colonnes ;
- types inférés ;
- premières lignes ;
- nombre de lignes ;
- valeurs manquantes.

#### Mapping manuel

L’utilisateur choisit :

- colonne du groupe ;
- modalité A ;
- modalité B ;
- colonne de métrique ;
- type de métrique.

Pour une métrique binaire, permettre le mapping de deux modalités vers 0 et 1.

#### Validation

Afficher :

- observations retenues ;
- observations exclues ;
- répartition A/B ;
- conversions impossibles ;
- avertissements.

Aucun fichier n’est conservé après la session.

## 5. Statistiques descriptives

### 5.1 Binaire

Par groupe :

- effectif ;
- succès ;
- échecs ;
- proportion ;
- erreur standard ;
- intervalle de confiance ;
- valeurs manquantes.

Comparaison :

- différence absolue ;
- uplift relatif ;
- odds ;
- odds ratio ;
- risque relatif lorsque défini.

### 5.2 Continue

Par groupe :

- effectif ;
- moyenne ;
- médiane ;
- variance ;
- écart-type ;
- erreur standard ;
- min/max ;
- quantiles ;
- IQR ;
- valeurs manquantes.

Comparaison :

- différence de moyennes ;
- différence de médianes ;
- ratio de moyennes lorsque défini ;
- taille d’effet ;
- intervalle de confiance.

## 6. Tests statistiques

Le choix est toujours manuel.

### 6.1 Test z pour deux proportions

Entrées : données binaires indépendantes, alpha, alternative.

Sorties :

- z ;
- p-value ;
- différence de proportions ;
- intervalle de confiance ;
- odds ratio ;
- risque relatif si défini ;
- décision ;
- avertissements asymptotiques.

### 6.2 Test exact de Fisher

Entrées : tableau 2 × 2, alternative.

Sorties :

- tableau de contingence ;
- odds ratio ;
- p-value exacte ;
- décision.

### 6.3 Test t de Student

Hypothèse de variances égales.

Sorties :

- t ;
- degrés de liberté ;
- p-value ;
- différence de moyennes ;
- intervalle ;
- Cohen’s d ;
- décision.

### 6.4 Test t de Welch

Variances potentiellement différentes.

Sorties :

- t ;
- degrés de liberté de Welch ;
- p-value ;
- différence de moyennes ;
- intervalle ;
- taille d’effet ;
- décision.

### 6.5 Mann–Whitney

Sorties :

- U ;
- p-value ;
- effet de rang ;
- décision ;
- avertissement : ne pas le présenter automatiquement comme un simple test des médianes.

### 6.6 Permutation

Paramètres :

- différence de moyennes dans la V1 ;
- nombre de permutations ;
- seed ;
- alternative.

Sorties :

- statistique observée ;
- distribution nulle ;
- p-value empirique ;
- graphique ;
- décision.

### 6.7 Bootstrap de la différence

Paramètres :

- moyenne ou médiane ;
- nombre de réplications ;
- niveau de confiance ;
- seed ;
- intervalle percentile dans la V1.

Sorties :

- estimation ;
- erreur standard bootstrap ;
- intervalle ;
- distribution ;
- graphique ;
- conclusion prudente.

## 7. Paramètres communs

- alpha, défaut 0,05 ;
- alternative bilatérale, A > B ou B > A ;
- niveau de confiance ;
- seed pour méthodes simulées ;
- nombre de réplications ;
- seuil pratique optionnel.

Validation côté frontend et backend.

## 8. Interprétation déterministe

Structure :

1. question ;
2. H0 et H1 ;
3. résultat numérique ;
4. décision au seuil choisi ;
5. effet ;
6. incertitude ;
7. comparaison au seuil pratique ;
8. avertissements.

Formulations interdites :

- « H0 est vraie » ;
- « les groupes sont identiques » ;
- « le traitement fonctionne avec certitude » ;
- « non significatif signifie aucun effet ».

Formulations acceptables :

- « les données fournissent suffisamment d’éléments pour rejeter H0 au seuil choisi » ;
- « les données ne fournissent pas suffisamment d’éléments pour rejeter H0 » ;
- « l’intervalle reste compatible avec plusieurs tailles ou directions d’effet ».

## 9. Visualisations

Outil : Plotly.js.

### Binaires

- taux avec intervalles ;
- tableau de contingence ;
- odds ou risque relatif ;
- différence de proportions.

### Continues

- histogrammes ;
- boxplots ;
- densités lorsque pertinent ;
- QQ plots ;
- intervalle de la différence.

### Méthodes simulées

- distribution nulle de permutation ;
- distribution bootstrap ;
- statistique observée ;
- limites de l’intervalle.

Chaque graphique doit être accompagné d’un résumé textuel.

## 10. Exports

### JSON

Inclure :

- métadonnées ;
- paramètres ;
- résumé des données ;
- test ;
- résultat standardisé ;
- interprétation ;
- avertissements.

### CSV

Deux sorties possibles :

- données analysées ;
- résultats aplatis.

### PDF

Inclure :

1. titre et date ;
2. source ;
3. configuration ;
4. résumé des groupes ;
5. méthode et hypothèses ;
6. résultats ;
7. graphiques ;
8. interprétation ;
9. avertissements ;
10. informations de reproductibilité.

## 11. API

Préfixe : `/api/v1`.

Endpoints initiaux :

- `GET /health`
- `POST /simulations/binary`
- `POST /simulations/continuous`
- `POST /datasets/preview`
- `POST /datasets/validate`
- `POST /descriptive/binary`
- `POST /descriptive/continuous`
- `POST /analyses/two-proportion-z`
- `POST /analyses/fisher-exact`
- `POST /analyses/student-t`
- `POST /analyses/welch-t`
- `POST /analyses/mann-whitney`
- `POST /analyses/permutation`
- `POST /analyses/bootstrap-difference`
- `POST /exports/json`
- `POST /exports/csv`
- `POST /reports/pdf`

Des regroupements sont autorisés s’ils réduisent la duplication sans rendre les contrats ambigus.

Dataset normalisé :

```json
{
  "metric_type": "continuous",
  "group_a": [12.1, 13.4, 10.8],
  "group_b": [14.2, 15.0, 12.9],
  "metadata": {"source": "simulation", "seed": 42}
}
```

Les données binaires sont normalisées en 0 et 1.

## 12. Exigences non fonctionnelles

### Performance

- analyses classiques rapides sur des tailles usuelles ;
- progression visible pour bootstrap/permutation ;
- limites configurables ;
- taille CSV maximale.

### Sécurité et confidentialité

- aucun stockage ;
- aucun envoi externe ;
- validation stricte ;
- noms nettoyés ;
- CSV considéré comme non fiable ;
- aucune exécution de contenu importé ;
- détails internes non exposés.

### Accessibilité

- labels explicites ;
- navigation clavier raisonnable ;
- contrastes suffisants ;
- erreurs associées aux champs ;
- résumés textuels des graphiques.

### Reproductibilité

- seeds enregistrées ;
- paramètres exportés ;
- dépendances verrouillées ;
- Docker Compose ;
- commandes documentées.

## 13. Validation scientifique

### Tests unitaires

Pour chaque fonction :

- cas nominal ;
- cas limite ;
- entrée invalide ;
- comparaison de référence.

### Références

- SciPy ;
- Statsmodels ;
- NumPy.

### Monte-Carlo

Mesurer :

- faux positifs pour alpha = 0,05 ;
- puissance pour plusieurs effets ;
- couverture des intervalles ;
- reproductibilité ;
- comportement avec variances inégales ;
- comportement avec outliers.

### API et frontend

Tester :

- schémas ;
- codes HTTP ;
- erreurs structurées ;
- cohérence des résultats ;
- formulaires ;
- affichage des résultats et erreurs ;
- navigation.

## 14. Critères d’acceptation V1

La V1 est acceptée lorsque :

1. `docker compose up --build` lance frontend et backend ;
2. les simulations binaires et continues fonctionnent ;
3. l’import et le mapping fonctionnent ;
4. les sept méthodes sont disponibles ;
5. les résultats suivent un contrat commun ;
6. les graphiques principaux sont présents ;
7. l’interprétation est déterministe ;
8. JSON, CSV et PDF fonctionnent ;
9. les validations scientifiques principales passent ;
10. la CI est verte ;
11. aucune persistance n’est utilisée ;
12. un tiers peut lancer le projet avec la documentation.

## 15. Évolutions futures

Hors V1 :

- analyse de puissance ;
- taille d’échantillon ;
- correction des tests multiples ;
- simulateur de p-hacking ;
- simulations A/A ;
- Bayes ;
- A/B/n ;
- tests séquentiels ;
- publication éventuelle du package Python.
