# Index de la documentation — Le Panier-Sûr

Ce document est le point d'entrée de toute la documentation technique du projet. Il décrit le chemin complet de la donnée depuis le scraping jusqu'à l'EDA, et référence chaque doc détaillée.

---

## 1. Vue d'ensemble du projet

**Le Panier-Sûr** est un outil de classification de champignons à partir de critères physiques (couleur, texture, taille, habitat, saison, odeur, saveur, morphologie du pied). L'objectif final est de permettre à un utilisateur de soumettre les caractéristiques d'un champignon et d'obtenir son nom ou son statut de comestibilité.

```
Web (guidedeschampignons.com)
│
│  [scrap.ipynb]
▼
data/raw/  ─────────────────── 219 espèces × 17 colonnes texte + images base64
│
│  [transform.ipynb]
▼
data/transform/  ───────────── 217 espèces × 174 colonnes structurées (ML-ready)
│
│  [augment.ipynb]
▼
data/augmented/  ───────────── 217 000 lignes × 165 colonnes (1 000× par espèce)
│
│  [visualisation_clean.ipynb]
│  [visualisation_augmented.ipynb]
▼
EDA / rapports  ────────────── distributions, corrélations, déséquilibre de classes
│
│  [TODO — modélisation]
▼
Modèle ML  ─────────────────── classification par nom (217 classes) ou statut (6 classes)
│
│  [TODO — application]
▼
API + Frontend  ─────────────── interface de prédiction (web/api/ + web/frontend/)
```

---

## 2. Chemin de la donnée — étape par étape

### Étape 0 — Source

| Attribut | Valeur |
|---|---|
| Site source | `https://www.guidedeschampignons.com` |
| Pages scrappées | 3 pages d'index (`/tous-les-champignons/page/1` → `/page/3`) |
| Espèces référencées | ~219 fiches |

Chaque fiche contient : nom commun, nom scientifique, synonyme, statut de comestibilité, 10 champs descriptifs (chapeau, pores, lames, pied, chair, odeur, saveur, habitat, saison, confusion), catégories, image.

---

### Étape 1 — Scraping → `data/raw/`

| Notebook | `etl/scraping/scrap.ipynb` |
|---|---|
| Documentation | `docs/scraping.md` |
| Durée | ~3 min (0,5 s par fiche, ~219 fiches) |

**Entrée** : URLs extraites des pages d'index.

**Sorties** :

| Fichier | Lignes | Colonnes | Contenu |
|---|---|---|---|
| `champignons_data.csv` | 219 | 17 | Texte brut (nom, statut, 10 descriptions…) |
| `champignons_images.csv` | 219 | 3 | nom, image_url, image_base64 (data URI) |

**Transformations** : aucune — données brutes telles que sur le site.

**Pertes potentielles** : fiches avec structure HTML anormale (sautées avec `try/except`).

---

### Étape 2 — Transformation → `data/transform/`

| Notebook | `etl/transform/transform.ipynb` |
|---|---|
| Documentation | `docs/transformation.md` |

**Entrée** : `data/raw/champignons_data.csv` (219 lignes × 17 colonnes).

**Sortie** : `data/transform/champignons_clean.csv` (217 lignes × 174 colonnes).

**Pertes** : 2 espèces supprimées car aucune partie anatomique interne décrite (ni chair, ni pied, ni pores, ni lames) → inutilisables pour le modèle.

**Transformations réalisées** :

| # | Étape | Colonnes produites |
|---|---|---|
| 1 | Indicateurs de présence | `a_un_chapeau`, `a_des_pores`, `a_des_lames`, `a_un_pied`, `a_de_la_chair` |
| 2 | Normalisation texte | Minuscules + suppression des accents (colonnes internes, non exportées) |
| 3 | Extraction binaire par dictionnaires | ~60 colonnes `{partie}_{type}_{valeur}` (couleurs, textures, odeurs, saveurs, attache, morpho pied, consistance chair) |
| 4 | Parsing des tailles (Regex) | `chapeau_taille_min_cm`, `chapeau_taille_max_cm`, `pied_taille_min_cm`, `pied_taille_max_cm` |
| 5 | Saison → binaire mensuel | `saison_mois_01` … `saison_mois_12` |
| 6 | Habitat → binaire | `habitat_type_feuillus`, `habitat_type_chenes`… (15 colonnes) |
| 7 | Drop des colonnes non-ML | `url`, `image_url`, `categories`, `confusion`, `synonyme`, `nom_scientifique` |

**Structure du CSV produit (174 colonnes)** :

```
nom, statut                                  ← labels
chapeau, pores, lames, pied, chair,
odeur, saveur, habitat, saison               ← texte brut (debug / inspection)
a_un_chapeau, a_des_pores, …                 ← présences (5)
chapeau_couleur_*, chapeau_texture_*, …      ← features binaires (~60)
chapeau_taille_min_cm, …_max_cm,
pied_taille_min_cm, …_max_cm                 ← tailles (4)
saison_mois_01 … saison_mois_12              ← saison (12)
habitat_type_*                               ← habitat (15)
```

---

### Étape 3 — Augmentation → `data/augmented/`

| Notebook | `etl/add_data/augment.ipynb` |
|---|---|
| Documentation | `docs/add_data.md` |

**Entrée** : `data/transform/champignons_clean.csv` (217 lignes × 174 colonnes).

**Sortie** : `data/augmented/champignons_augmented.csv` (217 000 lignes × 165 colonnes).

**Raison** : 217 singletons ne peuvent pas entraîner un modèle. L'augmentation produit 1 000 observations synthétiques par espèce pour simuler des collectes partielles.

**Colonnes exclues** du CSV augmenté (non générables) : 9 colonnes texte brutes (`chapeau`, `pores`, `lames`, `pied`, `chair`, `odeur`, `saveur`, `habitat`, `saison`) → 174 - 9 = 165 colonnes.

**Méthodes de génération** :

| Type de colonne | Méthode |
|---|---|
| Tailles (`min`, `max`) | Gaussienne tronquée dans `[min, max]` (`σ = 0.25 × amplitude`) |
| Features binaires | Réplication directe (dropout optionnel sur les `1`) |
| Saison | Tirage d'un seul mois parmi les mois actifs de l'espèce |
| Labels (`nom`, `statut`) | Copie identique × N |

---

### Étape 4 — EDA (Analyse Exploratoire)

| Notebook | `etl/data_visualisation/visualisation_clean.ipynb` |
|---|---|
| Données analysées | `data/transform/champignons_clean.csv` |

| Notebook | `etl/data_visualisation/visualisation_augmented.ipynb` |
|---|---|
| Données analysées | `data/augmented/champignons_augmented.csv` |

| Documentation | `docs/data_visualisation.md` |
|---|---|

**Ce qu'on vérifie** :

| Analyse | Outil | Objectif |
|---|---|---|
| Distributions des tailles | Histogramme + Boxplot | Repérer les aberrations (> 60 cm) |
| Présences anatomiques | Barplot | Couverture du dataset |
| Top 10 couleurs | Barplot horizontal | Déséquilibre de couleurs |
| Saisonnalité | Barplot mensuel | Répartition temporelle |
| Habitats | Barplot | Biais géographiques |
| Déséquilibre des classes | Histogramme + Pie | Statuts sous-représentés à pondérer |
| Corrélations `statut` × features | Heatmap + Barplots point-biserial | Features discriminantes par classe |
| Cohérence génération | KDE, scatter, tableau delta | Biais introduits par l'augmentation |

---

### Étapes suivantes (non encore réalisées)

| Étape | Notebook | Dossier cible |
|---|---|---|
| Entraînement ML | À créer | `etl/modeling/` |
| Évaluation (accuracy, F1, matrice de confusion) | À créer | `etl/modeling/` |
| API de prédiction | À créer | `web/api/` |
| Interface utilisateur (Streamlit / Flask) | À créer | `web/frontend/` |

---

## 3. Structure des fichiers

```
Le-Panier-Sur/
│
├── data/
│   ├── raw/
│   │   ├── champignons_data.csv          [Étape 1 — sortie scraping]
│   │   └── champignons_images.csv        [Étape 1 — images base64]
│   ├── transform/
│   │   └── champignons_clean.csv         [Étape 2 — sortie transformation]
│   └── augmented/
│       └── champignons_augmented.csv     [Étape 3 — sortie augmentation]
│
├── etl/
│   ├── scraping/
│   │   └── scrap.ipynb                   [Étape 1]
│   ├── transform/
│   │   └── transform.ipynb               [Étape 2]
│   ├── add_data/
│   │   └── augment.ipynb                 [Étape 3]
│   └── data_visualisation/
│       ├── visualisation_clean.ipynb     [Étape 4 — données réelles]
│       └── visualisation_augmented.ipynb [Étape 4 — données synthétiques]
│
├── docs/
│   ├── index.md                          ← ce document
│   ├── scraping.md                       ← doc Étape 1
│   ├── transformation.md                 ← doc Étape 2
│   ├── add_data.md                       ← doc Étape 3
│   └── data_visualisation.md             ← doc Étape 4
│
├── web/
│   ├── api/                              [TODO]
│   └── frontend/                         [TODO]
│
├── requirements.txt
└── README.md
```

---

## 4. Index des documents

| Document | Étape | Contenu résumé |
|---|---|---|
| [`scraping.md`](scraping.md) | Étape 1 | Comment fonctionne le scraper BeautifulSoup, structure HTML ciblée, gestion des erreurs, format des CSV bruts, comment relancer |
| [`transformation.md`](transformation.md) | Étape 2 | 7 étapes de nettoyage, dictionnaires de mots-clés, regex tailles, encodage saison / habitat, colonnes supprimées pour éviter les fuites de labels |
| [`add_data.md`](add_data.md) | Étape 3 | Pourquoi augmenter, paramètres configurables (N, sigma, dropout), méthodes de génération par type de colonne, sanity checks intégrés, recommandations pour le split train/test |
| [`data_visualisation.md`](data_visualisation.md) | Étape 4 | Structure des deux notebooks EDA, interprétation de chaque graphe, signaux d'alerte à surveiller, section corrélation statut × features |

---

## 5. Dépendances

Toutes les dépendances sont listées dans `requirements.txt`.

| Librairie | Version | Usage |
|---|---|---|
| `pandas` | 3.0.2 | Manipulation de DataFrames dans tout le pipeline |
| `numpy` | 2.4.4 | Calculs numériques, génération aléatoire (augmentation) |
| `matplotlib` | — | Graphes de base (toutes les visualisations) |
| `seaborn` | — | Graphes statistiques avancés (boxplots groupés, heatmaps, KDE) |
| `requests` | — | Requêtes HTTP (scraping) |
| `beautifulsoup4` | — | Parsing HTML (scraping) |
| `jupyter` / `ipykernel` | — | Environnement notebook |

Installation :
```bash
pip install -r requirements.txt
```

---

## 6. Ordre d'exécution recommandé

```bash
# 1. Scraping (optionnel si les CSV raw existent déjà)
jupyter nbconvert --to notebook --execute etl/scraping/scrap.ipynb

# 2. Transformation
jupyter nbconvert --to notebook --execute etl/transform/transform.ipynb

# 3. Augmentation
jupyter nbconvert --to notebook --execute etl/add_data/augment.ipynb

# 4. EDA
jupyter nbconvert --to notebook --execute etl/data_visualisation/visualisation_clean.ipynb
jupyter nbconvert --to notebook --execute etl/data_visualisation/visualisation_augmented.ipynb
```

Chaque étape peut être relancée indépendamment **si ses fichiers d'entrée existent**. Les étapes 2, 3 et 4 n'ont pas besoin d'accès internet.
