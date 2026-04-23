# Data Visualisation — Le Panier-Sûr

Documentation des notebooks d'analyse exploratoire (EDA) à exécuter avant l'entraînement du modèle.

- **Entrées** :
  - `data/transform/champignons_clean.csv` — 217 espèces, données réelles
  - `data/augmented/champignons_augmented.csv` — 217 000 lignes, données synthétiques
- **Notebooks** :
  - `etl/data_visualisation/visualisation_clean.ipynb` — EDA sur les données réelles
  - `etl/data_visualisation/visualisation_augmented.ipynb` — EDA sur les données synthétiques + comparaison

---

## 1. Vue d'ensemble

```
champignons_clean.csv (217 × 174)
    │
    └─ visualisation_clean.ipynb
           ├─ §2 Tailles numériques (histogramme, boxplot, top aberrations)
           ├─ §3 Features catégorielles (présences, couleurs, saisons, habitats)
           ├─ §4 Cible (déséquilibre nom, camembert statut)
           └─ §5 Corrélations statut × features

champignons_augmented.csv (217 000 × 165)
    │
    └─ visualisation_augmented.ipynb
           ├─ §2 Tailles numériques (idem, sur échantillon 20 000 lignes)
           ├─ §3 Features catégorielles
           ├─ §4 Cible (équilibre vérifié)
           └─ §5 Comparaison synthétique vs réel
```

Librairies : `pandas`, `numpy`, `matplotlib`, `seaborn`.

---

## 2. `visualisation_clean.ipynb` — données réelles

### §2 — Analyse des tailles numériques

Objectif : repérer les valeurs aberrantes (un champignon de 200 cm est un bug de parsing).

| Visualisation | Colonnes | Ce qu'on cherche |
|---|---|---|
| Histogramme + KDE | `chapeau_taille` (moyenne) | Distribution naturelle (~log-normale) |
| Histogramme + KDE | `pied_taille` (moyenne) | Distribution naturelle |
| Boxplot | min/max chapeau + pied | Outliers extrêmes (points au-delà des moustaches) |
| Tableau Top 10 | `chapeau_taille_max_cm` | Espèces candidates aux valeurs extrêmes |

La taille moyenne est calculée comme `(min + max) / 2` et stockée dans `chapeau_taille` / `pied_taille` pour toute la session.

**Valeurs attendues** : la majorité des chapeaux entre 2 et 20 cm, les pieds entre 2 et 15 cm.
Signaux d'alerte : toute valeur > 60 cm doit être vérifiée manuellement dans le CSV brut.

### §3 — Features catégorielles

#### 3.1 Présence des attributs

Barplot de `a_un_pied`, `a_des_pores`, `a_des_lames`. Indique la couverture anatomique du dataset.

Résultat typique :
- `a_des_lames` : ~130 espèces (agarics)
- `a_un_pied` : ~200 espèces (presque tout le règne)
- `a_des_pores` : ~40 espèces (bolets, polypores)

#### 3.2 Top 10 des couleurs

Barplot horizontal des couleurs de chapeau et de chair les plus représentées.

Encodage : les colonnes `chapeau_couleur_*` (13 couleurs) sont des binaires — on somme sur toutes les lignes pour obtenir un compte.

**Interprétation** : si "brun" domine à 70 %, le modèle risque de se baser trop sur cette couleur. À surveiller lors de l'analyse d'importance des features.

#### 3.3 Saisons

Barplot des 12 mois (`saison_mois_01` → `saison_mois_12`). Montre la saisonnalité globale du corpus.

Résultat typique : pic en juillet–octobre (saison mycologique principale en France), creux en janvier–mars.

#### 3.4 Habitats

Barplot horizontal de tous les types d'habitat (`habitat_type_*`, 15 valeurs). Met en évidence la sur-représentation des forêts de feuillus par rapport aux milieux ouverts (prairies, jardins).

### §4 — Analyse de la cible

#### 4.1 Cible `nom`

Dans le dataset nettoyé, chaque espèce est une ligne unique → histogramme plat (toutes les barres à 1). Ce graphe confirme simplement qu'il n'y a pas de doublons.

#### 4.2 Cible `statut`

Camembert des 6 classes de statut :

| Statut | Description |
|---|---|
| Mortel | Létal si ingéré |
| Toxique | Intoxication grave |
| Champignon à rejeter | Non comestible, sans risque mortel connu |
| Médiocre | Comestible mais sans intérêt gastronomique |
| Bon | Bon comestible |
| Les excellents champignons | Excellent comestible |

La répartition est **déséquilibrée** : les statuts extrêmes (mortel, excellent) sont minoritaires. À compenser avec `class_weight` ou sur-échantillonnage lors de la modélisation.

### §5 — Corrélations `statut` × features

Section dédiée à identifier quelles features discriminent le mieux les statuts.

#### 5.1 Tailles par statut

Boxplots groupés `chapeau_taille` et `pied_taille` par classe de statut + tableau `mean / median / std`.

Signal attendu : les champignons mortels (ex. Amanites) ont souvent des pieds plus longs (volve, anneau), les polypores comestibles des chapeaux plus larges.

#### 5.2 Heatmap des proportions binaires

**Méthode** :
1. Calcul de la proportion de `1` par feature et par statut via `groupby("statut").mean()`.
2. Sélection des **25 features à plus forte variance inter-statut** (features les plus discriminantes).
3. Heatmap `RdYlBu_r` annotée.

**Lecture** : une case rouge foncé signifie que cette feature est très fréquente dans ce statut. Une case bleue foncé signifie l'inverse.

#### 5.3 Corrélation one-vs-rest

**Méthode** : pour chaque classe de statut `s`, on encode `target = (statut == s).astype(int)` puis on calcule la corrélation de Pearson entre `target` et chaque feature numérique/binaire.

Pour chaque statut :
- **Top 10 positives** (vert) : features sur-représentées dans ce statut.
- **Top 10 négatives** (rouge) : features sous-représentées.

Exemple d'interprétation : si `odeur_type_desagreable` est corrélé positivement au statut "Mortel", cela confirme que les espèces mortelles ont souvent une odeur désagréable.

#### 5.4 Heatmap globale

Matrice features × statuts pour les **25 features à plus forte corrélation absolue** (tous statuts confondus). Colorée en divergent `RdBu_r` centré sur 0. Vue synthétique pour une présentation rapide.

---

## 3. `visualisation_augmented.ipynb` — données synthétiques

Les sections §2, §3, §4 sont identiques à `visualisation_clean.ipynb` mais portent sur les 217 000 lignes. Le rendu est allégé par un échantillonnage à **20 000 lignes** (`df.sample(20_000, random_state=42)`) pour les visualisations lourdes.

### §5 — Comparaison synthétique vs réel

Section spécifique au dataset augmenté, absente du notebook clean.

#### 5.1 Tableau des moyennes

| Colonne | `réel_mean` | `augmenté_mean` | `delta_pct` |
|---|---|---|---|
| chapeau_taille_min_cm | … | … | Attendu < 5 % |
| chapeau_taille_max_cm | … | … | Attendu < 5 % |
| pied_taille_min_cm | … | … | Attendu < 5 % |
| pied_taille_max_cm | … | … | Attendu < 5 % |

Un delta > 10 % indique un biais systématique dans le générateur.

#### 5.2 Barplot de comparaison

Barplot côte à côte (hue = dataset) pour les moyennes de chaque colonne de taille.

#### 5.3 KDE superposées

Deux courbes de densité (réel vs augmenté) pour `chapeau_taille` et `pied_taille`. Les courbes doivent se superposer avec un léger élargissement (dû à la gaussienne) mais pas de décalage de mode.

#### 5.4 Scatter moyenne par espèce

Pour chaque espèce, on compare :
- Axe X : taille moyenne sur la ligne réelle (1 point par espèce)
- Axe Y : taille moyenne sur les 1 000 tirages synthétiques

Les points doivent s'aligner sur la diagonale `y = x` (tracée en pointillés gris). Un décrochage systématique signalerait un bug d'indexation des colonnes lors de la génération.

L'écart moyen absolu par espèce est affiché en pied de graphe — valeur typique < 0.5 cm.

---

## 4. Signaux d'alerte à surveiller

| Signal | Seuil d'alerte | Action |
|---|---|---|
| Taille max > 60 cm | Chapeau | Vérifier dans le CSV brut |
| Taille min = 0 cm sur tous les pieds | > 20 espèces | Bug de parsing (regex) |
| Feature binaire toujours à 0 | 100 % de 0 | Supprimer la colonne avant fit |
| Feature binaire toujours à 1 | 100 % de 1 | Idem |
| Delta moyen augmenté vs réel | > 10 % | Revoir les paramètres de génération |
| Camembert statut : une classe < 5 % | < 10 espèces | Surveiller le rappel pour cette classe |

---

## 5. Relancer les notebooks

```bash
# Dataset nettoyé
jupyter nbconvert --to notebook --execute etl/data_visualisation/visualisation_clean.ipynb

# Dataset augmenté
jupyter nbconvert --to notebook --execute etl/data_visualisation/visualisation_augmented.ipynb
```

---

## 6. Architecture des fichiers

```
Le-Panier-Sur/
├── data/
│   ├── transform/
│   │   └── champignons_clean.csv              ← entrée notebook clean
│   └── augmented/
│       └── champignons_augmented.csv          ← entrée notebook augmenté
├── etl/
│   └── data_visualisation/
│       ├── visualisation_clean.ipynb          ← EDA données réelles (30 cellules)
│       └── visualisation_augmented.ipynb      ← EDA données synthétiques (26 cellules)
└── docs/
    ├── data_visualisation.md                  ← ce document
    ├── add_data.md                            ← pipeline amont (augmentation)
    └── index.md                              ← index global du projet
```
