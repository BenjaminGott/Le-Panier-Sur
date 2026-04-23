# Augmentation des données — Le Panier-Sûr

Documentation du pipeline de génération de données synthétiques pour équilibrer et enrichir le dataset avant entraînement.

- **Entrée** : `data/transform/champignons_clean.csv` (sortie de la transformation)
- **Sortie** : `data/augmented/champignons_augmented.csv`
- **Notebook** : `etl/add_data/augment.ipynb`

---

## 1. Vue d'ensemble du pipeline

```
champignons_clean.csv (217 espèces × 174 colonnes)
    │
    ├─ 1. Identification des colonnes par type
    │      → tailles, saison, binaires, labels
    │      ↳ Drop des colonnes texte brutes (non reproductibles)
    │
    ├─ 2. Pour chaque espèce (217 boucles)
    │      ├─ Labels     → recopiés N fois à l'identique
    │      ├─ Tailles    → échantillonnage gaussien tronqué dans [min, max]
    │      ├─ Binaires   → réplication avec dropout optionnel sur les 1
    │      └─ Saison     → tirage d'un seul mois parmi les mois actifs
    │
    └─ 3. Assemblage + export
           → champignons_augmented.csv (217 000 lignes × 165 colonnes)
```

Librairies utilisées : `numpy`, `pandas`.

---

## 2. Pourquoi augmenter ?

Le dataset nettoyé contient **217 espèces — une ligne par espèce**. Un modèle de classification par espèce ne peut pas être entraîné sur des singletons : pas de généralisation, pas d'évaluation possible.

L'augmentation produit **N observations synthétiques par espèce** (par défaut N = 1 000) :
- Chaque observation simule une **collecte partielle** dans la nature (un mois donné, une taille observée dans la plage connue).
- Le modèle apprend à reconnaître une espèce **même si toutes ses caractéristiques ne sont pas visibles** lors de l'observation.

> **Ce que l'augmentation apporte** : robustesse face à une observation partielle.
>
> **Ce qu'elle n'apporte pas** : de vraie diversité d'espèces. 217 espèces × 1 000 = 217 000 lignes, mais toujours 217 classes.

---

## 3. Paramètres configurables

| Paramètre | Défaut | Rôle |
|---|---|---|
| `N_SAMPLES` | `1000` | Nombre d'observations synthétiques par espèce |
| `SIZE_SIGMA_RATIO` | `0.25` | Écart-type de la gaussienne sur les tailles, exprimé en fraction de l'intervalle [min, max]. `0.25` → ~95 % des tirages dans [min, max] |
| `BINARY_DROPOUT` | `0.00` | Probabilité qu'un 1 binaire soit flippé à 0 (simule une observation incomplète). `0.0` = désactivé |
| `SEED` | `42` | Graine NumPy pour la reproductibilité |

---

## 4. Catégorisation des colonnes

Avant la boucle d'augmentation, chaque colonne du CSV nettoyé est classée dans l'une de ces quatre catégories :

| Catégorie | Colonnes concernées | Traitement |
|---|---|---|
| **Labels** | `nom`, `statut` | Recopiés N fois à l'identique |
| **Tailles** | `*_taille_min_cm`, `*_taille_max_cm` | Échantillonnage gaussien tronqué |
| **Saison** | `saison_mois_01` … `saison_mois_12` | Un seul mois actif tiré parmi les mois réels |
| **Binaires** | Tout le reste (couleurs, textures, odeurs…) | Réplication avec dropout optionnel |

Les colonnes **texte brutes** (`chapeau`, `pores`, `lames`, `pied`, `chair`, `odeur`, `saveur`, `habitat`, `saison`) sont exclues du CSV augmenté — elles ne peuvent pas être générées de manière réaliste et ne sont pas utilisées par le modèle.

---

## 5. Fonctions d'augmentation

### `sample_size(vmin, vmax, n, rng)`

Génère `n` tirages gaussiens tronqués dans `[vmin, vmax]` pour simuler une taille observée sur le terrain.

```
μ = (vmin + vmax) / 2          → centre de l'intervalle connu
σ = (vmax - vmin) × SIZE_SIGMA_RATIO
tirage = clip(N(μ, σ), vmin, vmax)
```

Pour une paire de colonnes `(min, max)` : deux tirages indépendants sont effectués, puis réordonnés pour garantir `min ≤ max`.

### `dropout_binary(values, n, rng)`

Réplique le vecteur binaire de l'espèce `n` fois. Si `BINARY_DROPOUT > 0`, chaque `1` a une probabilité `BINARY_DROPOUT` d'être flippé à `0` — les `0` ne changent jamais (on n'invente pas de features absentes).

```
out = tile(values, n)
flip = random() < BINARY_DROPOUT   # uniquement sur les 1
out[flip] = 0
```

### `sample_season_month(active_months, n, rng)`

Tire `n` mois uniformément parmi les mois actifs de l'espèce. Produit une matrice `(n, 12)` avec exactement **un seul `1` par ligne** (mois observé).

Rationale : dans la réalité, on rencontre un champignon à une date précise — pas sur toute sa saison. Encoder un seul mois rend les observations plus réalistes.

---

## 6. Boucle d'augmentation

```python
for _, row in df.iterrows():          # Une itération par espèce (217)
    # 1. Labels
    base = {col: [row[col]] * N_SAMPLES for col in label_cols}

    # 2. Tailles
    for part in {"chapeau", "pied"}:
        lo, hi = sample_size(min, max, N_SAMPLES, rng)  # 2 tirages réordonnés

    # 3. Binaires (avec dropout)
    bin_aug = dropout_binary(row[binary_cols], N_SAMPLES, rng)

    # 4. Saison (un mois)
    season_aug = sample_season_month(active_months, N_SAMPLES, rng)

    chunk = pd.DataFrame(...)  # Assemblage de 1000 lignes
    augmented_rows.append(chunk)

df_aug = pd.concat(augmented_rows)[ordered_cols]
```

Le résultat est conservé **groupé par espèce** (sans shuffle). Le shuffle se fait au moment du `train_test_split` lors de la modélisation.

---

## 7. Sanity checks intégrés

Quatre vérifications automatiques sont exécutées après la génération :

| Check | Attendu | Ce qu'il détecte |
|---|---|---|
| Lignes par espèce | min = max = N_SAMPLES | Bug de la boucle (espèce ignorée ou doublée) |
| Variance des tailles | std > 0 au sein d'une espèce | σ nul → toutes les lignes identiques |
| Unicité du mois | Somme saison ∈ {0, 1} par ligne | Bug du tirage (mois multipliés) |
| Taux de 1 avant/après | Stable (si dropout = 0) | Drift binaire non intentionnel |

---

## 8. Format de sortie

`data/augmented/champignons_augmented.csv` — **217 000 lignes × 165 colonnes**.

Ordre des colonnes :
1. Labels : `nom`, `statut`
2. Tailles : `chapeau_taille_min_cm`, `chapeau_taille_max_cm`, `pied_taille_min_cm`, `pied_taille_max_cm`
3. Binaires : toutes les features 0/1 (présences, couleurs, textures, odeurs, saveurs, morpho, consistance, habitat)
4. Saison : `saison_mois_01` … `saison_mois_12`

Chaque espèce occupe des lignes consécutives (N_SAMPLES lignes par bloc).

---

## 9. Recommandations pour la modélisation

- **Split stratifié** : faire le `train_test_split` **après** augmentation, stratifié par `nom`. Chaque espèce doit apparaître dans le train ET le test.
- **Pas de fuite** : vérifier que les lignes du même champignon d'origine ne sont pas réparties entre train et test (le grouping par espèce est préservé → utiliser `GroupShuffleSplit` ou stratifier strictement).
- **Dropout** : si la performance sur le test réel est inférieure à celle sur le test augmenté, augmenter `BINARY_DROPOUT` à 0.05–0.10 pour forcer la robustesse.
- **Tailles aberrantes** : les boxplots du notebook `visualisation_augmented.ipynb` montrent que les tailles restent dans les plages biologiques — aucun filtre post-génération n'est nécessaire.

---

## 10. Relancer l'augmentation

```bash
# Depuis etl/add_data/
jupyter nbconvert --to notebook --execute augment.ipynb
# ou ouvrir augment.ipynb dans VS Code et exécuter toutes les cellules
```

Le CSV est écrit dans `data/augmented/` — le fichier existant est écrasé.

---

## 11. Architecture des fichiers

```
Le-Panier-Sur/
├── data/
│   ├── transform/
│   │   └── champignons_clean.csv        ← entrée
│   └── augmented/
│       └── champignons_augmented.csv    ← sortie
├── etl/
│   └── add_data/
│       └── augment.ipynb                ← le notebook
└── docs/
    ├── add_data.md                      ← ce document
    ├── transformation.md                ← pipeline amont
    └── data_visualisation.md            ← pipeline aval (EDA)
```
