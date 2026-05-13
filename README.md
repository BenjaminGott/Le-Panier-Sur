# 🍄 Le Panier-Sûr

> Application de galerie et d'identification de champignons — web & desktop

![Page d'accueil](./docs/assets/home_page.png)

Le Panier-Sûr est une application complète permettant de **consulter des fiches détaillées de champignons**, de **filtrer par habitat, saison et statut de comestibilité**, et d'**identifier un champignon** à partir de ses caractéristiques via un modèle XGBoost embarqué.

Le projet regroupe :
- un **pipeline ETL complet** (scraping → transformation → augmentation de données)
- un **modèle de machine learning** (XGBoost) entraîné sur données réelles et augmentées
- une **application web / desktop** (SvelteKit + Tauri) avec inférence client-side via ONNX Runtime

---

## Fonctionnalités

- **Galerie** — parcourir 217 espèces avec recherche, filtres par statut / habitat / saison / couleur du chapeau
- **Fiche champignon** — informations détaillées (comestibilité, habitats, saisons, morphologie)
- **Identification** — identifier un champignon en entrant ses caractéristiques (modèle XGBoost / ONNX)
- **Statistiques** — visualisations (répartition par statut, espèces actives par mois, top habitats)
- **Guide du cueilleur** — 7 étapes basées sur les statistiques du dataset, avec graphiques interactifs
- **Application desktop** — version `.exe` Windows via Tauri

---

## Captures d'écran

### Galerie & filtres

![Galerie](./docs/assets/home_page.png)

### Fiche espèce

![Fiche champignon](./docs/assets/details_1.png)

![Fiche champignon — suite](./docs/assets/details_2.png)

### Identification par le modèle

![Page Identifier](./docs/assets/model.png)

### Statistiques

![Statistiques](./docs/assets/stats.png)

### Guide du cueilleur

![Guide](./docs/assets/guide.png)

---

## Architecture du projet

```
Le-Panier-Sur/
├── etl/                      # Pipeline de données (notebooks Jupyter)
│   ├── scraping/             # Scraping des données
│   ├── transform/            # Nettoyage & feature engineering
│   ├── add_data/             # Augmentation des données
│   └── data_visualisation/   # EDA & visualisations
│
├── data/                     # Données brutes et transformées
│   ├── raw/                  # Données originales scrappées
│   ├── transform/            # Données texte intermédiaires
│   ├── clean_train_data/     # Données nettoyées pour l'entraînement
│   ├── clean_web/            # Données pour l'application web
│   └── augmented/            # Dataset augmenté (92 Mo)
│
├── model/                    # Modèle ML & inférence
│   ├── train_models.ipynb    # Entraînement (arbre de décision + XGBoost)
│   ├── train_xgboost.py      # Script d'entraînement XGBoost
│   ├── xgb_champignons.json  # Modèle entraîné (7.9 Mo)
│   └── predict.py            # Script d'inférence CLI
│
├── docs/assets/              # Captures d'écran & visuels
└── web/frontend/             # Application SvelteKit + Tauri
```

---

## Pipeline ETL

```
Scraping (scrap.ipynb)
        ↓
  ~217 espèces · 17 colonnes
        ↓
Transformation (transform.ipynb)
        ↓
  Nettoyage, encodage des caractéristiques morphologiques
        ↓
Augmentation (augment.ipynb)
        ↓
  Dataset enrichi (~92 Mo) pour l'entraînement
```

### Lancer le pipeline

```bash
conda env create -f environment.yml
conda activate le_panier_sur
jupyter notebook
```

Ouvrir dans l'ordre :
1. `etl/scraping/scrap.ipynb`
2. `etl/transform/transform.ipynb`
3. `etl/add_data/augment.ipynb`

---

## Modèle ML

Deux modèles entraînés :
- **Arbre de décision** — sur les données réelles nettoyées
- **XGBoost** (`xgb_champignons.json`) — sur les données augmentées, utilisé dans l'app

Le modèle est exporté en **ONNX** et embarqué dans l'application pour une inférence entièrement client-side.

### Inférence CLI

```bash
cd model
python predict.py --input sample_input.json
```

---

## Application Web / Desktop

Voir [`web/frontend/README.md`](./web/frontend/README.md) pour l'installation détaillée.

**Lancement rapide :**

```powershell
cd web\frontend
npm install
npm run dev        # Mode web (localhost:5173)
npm run tauri dev  # Mode desktop avec hot-reload
```

**Build .exe :**

```powershell
npm run tauri build
# → src-tauri/target/release/le-panier-sur.exe
# → src-tauri/target/release/bundle/msi/Le Panier-Sûr_0.1.0_x64_en-US.msi
```

---

## Prérequis

| Outil | Version |
|-------|---------|
| Python (Conda) | 3.14+ |
| Node.js | 22+ |
| Rust + Cargo | 1.95+ *(build desktop uniquement)* |
| MSVC Build Tools 2022 | *(Windows, build desktop uniquement)* |

---

## Liens

- Tableau Trello : https://trello.com/b/2zdqb5xs/le-panier-sur
- Release GitHub : https://github.com/BenjaminGott/Le-Panier-Sur/releases

---

## Licence

<!-- LICENCE à définir -->
> _Licence à ajouter_
