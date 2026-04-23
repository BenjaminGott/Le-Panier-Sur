# Transformation des données — Le Panier-Sûr

Documentation du pipeline de nettoyage et de structuration des données de champignons en vue de l'entraînement d'un modèle de classification.

- **Entrée** : `data/raw/champignons_data.csv` (sortie du scraping)
- **Sortie** : `data/transform/champignons_clean.csv`
- **Notebook** : `etl/transform/transform.ipynb`

---

## 1. Vue d'ensemble du pipeline

```
CSV brut (~219 lignes, 17 colonnes texte)
    │
    ├─ 1. Chargement + indicateurs de présence
    │      (a_un_chapeau, a_des_pores, a_des_lames, a_un_pied, a_de_la_chair)
    │      ↳ Filtrage : suppression des lignes sans chair NI pied NI pores NI lames
    │
    ├─ 2. Normalisation
    │      (minuscules + suppression des accents)
    │
    ├─ 3. Extraction binaire par dictionnaires
    │      (couleurs, textures, odeurs, saveurs, attache, morpho pied, consistance chair)
    │
    ├─ 4. Parsing des dimensions (Regex)
    │      [partie]_taille_min_cm / [partie]_taille_max_cm
    │
    ├─ 5. Saison → 12 colonnes binaires (une par mois)
    │
    ├─ 6. Habitat → colonnes binaires (feuillus, pins, chênes, prairies, …)
    │
    └─ 7. Drop des colonnes inutiles → export CSV final
```

---

## 2. Étape 1 — Indicateurs de présence

Pour chaque champignon, 5 flags binaires indiquent si chaque partie anatomique est décrite dans les données brutes :

| Colonne | Valeur |
|---|---|
| `a_un_chapeau` | 1 si `chapeau` contient du texte utile, sinon 0 |
| `a_des_pores` | 1 si `pores` contient du texte utile, sinon 0 |
| `a_des_lames` | 1 si `lames` contient du texte utile, sinon 0 |
| `a_un_pied` | 1 si `pied` contient du texte utile, sinon 0 |
| `a_de_la_chair` | 1 si `chair` contient du texte utile, sinon 0 |

**Règle** : 0 si la cellule est NaN, chaîne vide, ou contient le mot "absent". 1 sinon.

**Pourquoi c'est utile** : l'absence d'une partie est très discriminante pour la famille :
- pas de pores → agarics (à lames)
- pas de lames → bolets, pézizes
- pas de pied → polypores

### Filtrage post-présence

Les lignes avec **aucune** des 4 parties internes (chair, pied, pores, lames) décrites sont supprimées du dataset — elles n'apportent rien au modèle. `df` et `df_clean` sont réindexés.

---

## 3. Étape 2 — Normalisation

Toutes les colonnes texte sont passées en minuscules et débarrassées de leurs accents via `unicodedata.normalize("NFD", …)` pour rendre les recherches par mot-clé robustes :

- `forêt` → `foret`
- `mèches` → `meches`
- `à` → `a`

Les recherches suivantes se font donc **toujours sur du texte sans accents**. Les variantes dans les dictionnaires doivent impérativement être écrites sans accents.

Colonnes normalisées : `chapeau`, `pores`, `lames`, `pied`, `chair`, `odeur`, `saveur`, `habitat`, `saison`.

> Le texte original reste dans `df` ; la version normalisée est stockée dans `df_norm` pour l'extraction.

---

## 4. Étape 3 — Extraction par dictionnaires

### Principe

Chaque dictionnaire associe une **étiquette canonique** (nom de colonne) à une liste de **variantes orthographiques** :

```python
COULEURS = {
    "brun": ["brun", "brune", "brunatre", "marron", "chatain", "chocolat", "cannelle"],
    ...
}
```

Pour chaque colonne texte et chaque dictionnaire associé, on produit des colonnes binaires `{partie}_{dico}_{etiquette}` valant 1 si au moins une variante est trouvée dans le texte, 0 sinon.

**Exemple** : `chapeau_couleur_brun = 1` si la description du chapeau contient "brun", "brune", "marron" ou "chatain".

La recherche utilise des **frontières de mots** (`\b...\b`) pour éviter les faux positifs (par ex. `rose` ne matche pas dans `rosâtre` — on ajoute explicitement `rosatre` aux variantes).

### Plan d'extraction

| Colonne source | Dictionnaires appliqués |
|---|---|
| `chapeau` | COULEURS, TEXTURES |
| `pores` | COULEURS, ATTACHE |
| `lames` | COULEURS, ATTACHE |
| `pied` | COULEURS, TEXTURES, PIED_MORPHO |
| `chair` | COULEURS, CHAIR_CONSISTANCE |
| `odeur` | ODEURS |
| `saveur` | SAVEURS |

### Dictionnaires disponibles

| Nom | Étiquettes | But |
|---|---|---|
| `COULEURS` | blanc, brun, jaune, rouge, orange, rose, gris, noir, vert, bleu, violet, ocre, roux | Couleur dominante |
| `TEXTURES` | lisse, meches, floconneux, visqueux, velours, ecailleux, craquele, strie | Aspect de surface |
| `ODEURS` | anise, phenol, iode, radis, farine, amande, terre, fruitee, desagreable | Odeur |
| `SAVEURS` | douce, amere, acide, piquante, poivree, iodee, desagreable, sans_saveur | Saveur |
| `ATTACHE` | libres, adnees, decurrentes, echancrees, serrees, espacees | Insertion des lames/pores sur le pied |
| `PIED_MORPHO` | anneau, volve, bulbe, massue, creux, elance, cylindrique, reseau | Structures du pied (**critique pour distinguer les amanites**) |
| `CHAIR_CONSISTANCE` | ferme, tendre, molle, cassante, elastique, epaisse, fibreuse, spongieuse | Consistance interne |

### Comment étendre un dictionnaire

- **Nouvelle étiquette** (nouvelle colonne binaire) : ajouter une clé au dict → `"turquoise": ["turquoise"]`
- **Nouvelle variante** (élargir un matching existant) : ajouter au tableau → `"brun": [..., "bai"]`
- **Nouveau dictionnaire** : définir le dict, puis l'ajouter à `EXTRACTION_PLAN` sur la ou les colonnes concernées.

Les variantes doivent être écrites **sans accents**.

---

## 5. Étape 4 — Parsing des dimensions (Regex)

Les descriptions contiennent des tailles en centimètres ou millimètres. On les extrait en colonnes numériques.

**Regex** :
```python
r"(\d+(?:[.,]\d+)?)\s*(?:a|-)?\s*(\d+(?:[.,]\d+)?)?\s*(cm|mm|centimetres?|millimetres?)"
```

- Capture un nombre (entier ou décimal avec `.` ou `,`)
- Optionnellement une plage `"X à Y"` ou `"X - Y"`
- Obligatoirement suivi d'une unité (`cm`, `mm`, `centimetres`, `millimetres`)

**Exemples** :
- `"5 à 25 cm"` → min=5, max=25
- `"3 cm"` → min=max=3
- `"7 à 15 cm"` / `"Élancé (5 à 12 cm)"` → min=5, max=12
- `"50 mm"` → min=max=5 (conversion automatique mm → cm)

**Colonnes produites** : `chapeau_taille_min_cm`, `chapeau_taille_max_cm`, `pied_taille_min_cm`, `pied_taille_max_cm`.

**Valeurs manquantes** : les NaN (partie absente ou taille non trouvée) sont remplacés par `0`.

---

## 6. Étape 5 — Saison

La colonne source a le format `"Juillet > Octobre"`.

Plutôt que de stocker mois de début / mois de fin en entiers (ce qui induit un ordre ordinal trompeur), on produit **12 colonnes binaires** :

`saison_mois_01`, `saison_mois_02`, …, `saison_mois_12` (1 = actif ce mois-ci).

**Gestion du wrap-around** : `"novembre > fevrier"` → mois 11, 12, 1, 2 actifs.

**Pourquoi binaire ?**
- Un modèle peut apprendre des interactions par mois (ex. "septembre + chênes + lames libres" → cèpe).
- L'encodage ordinal début/fin aurait créé une fausse distance linéaire entre mois.

---

## 7. Étape 6 — Habitat

Dictionnaire `HABITATS` avec deux familles de concepts :

**Types de milieu** : `feuillus`, `coniferes`, `foret`, `prairies`, `clairieres`, `lisieres`, `jardins`, `bois`, `bois_morts`

**Essences d'arbres** : `chenes`, `hetres`, `pins`, `bouleaux`, `chataigniers`, `charmes`, `melezes`

Produit des colonnes binaires `habitat_type_{etiquette}` — même mécanisme que pour les couleurs / textures.

---

## 8. Étape 7 — Export

### Colonnes supprimées

Avant l'écriture du CSV final, on supprime :

| Colonne | Raison |
|---|---|
| `url` | Identifiant, pas une feature |
| `image_url` | Géré ailleurs (pipeline image) |
| `categories` | Non utilisée (tags source) |
| `confusion` | **Fuite de label** — liste les espèces proches |
| `synonyme` | **Fuite de label** |
| `nom_scientifique` | **Fuite de label** (1:1 avec `nom`) |

### Colonnes conservées

- **Label** : `nom` (et `statut` pour un modèle alternatif de dangerosité)
- **Texte brut** : `chapeau`, `pores`, `lames`, `pied`, `chair`, `odeur`, `saveur`, `habitat`, `saison` (utiles pour inspection / debug)
- **Features engineered** : toutes les colonnes binaires `{partie}_{dico}_{etiquette}`, les 4 colonnes de taille, les 12 colonnes `saison_mois_*`, les colonnes `habitat_type_*`, et les 5 flags de présence.

### Fichier produit

`data/transform/champignons_clean.csv` — une ligne par champignon, prêt pour l'entraînement.

---

## 9. Recommandations pour la suite (modélisation)

- **Cible** : prédire `statut` (6 classes : mortel, toxique, à rejeter, médiocre, bon, excellent) plutôt que `nom` (trop de classes pour 219 exemples).
- **Split** : stratifié sur le statut, car les classes sont déséquilibrées.
- **Drop avant fit** : supprimer les colonnes texte brutes et `nom` des features.
- **Validation des features** : vérifier la couverture (% de 1 par colonne binaire) — une colonne toujours à 0 ou 1 est inutile.
- **Piste d'amélioration majeure** : combiner ces features tabulaires à un CNN sur l'image (déjà scrapée).

---

## 10. Architecture des fichiers

```
Le-Panier-Sur/
├── data/
│   ├── raw/
│   │   └── champignons_data.csv        ← entrée
│   └── transform/
│       └── champignons_clean.csv       ← sortie
├── etl/
│   └── transform/
│       └── transform.ipynb             ← le notebook
└── docs/
    └── transformation.md               ← ce document
```
