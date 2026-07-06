"""Deux modeles robustes entraines sur les vraies donnees scrapees, avec bruit
d'observation (flips + oublis) pour ne PAS memoriser les empreintes exactes.

- Arbre de decision : accepte les donnees inconnues (NaN) et s'abstient
  ("Inconnu") quand la confiance est trop faible.
- Foret aleatoire : ensemble, mieux adapte aux vraies observations.

Sortie : deux fichiers JSON evalues directement dans le front (routage des NaN
fidele a sklearn), sans passer par ONNX.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "clean_train_data" / "champignons_clean.csv"
FEATURES_JSON = ROOT / "model" / "xgb_features.json"

FRONT_MODELS = ROOT / "web" / "frontend" / "static" / "models"
TREE_OUT = FRONT_MODELS / "tree_champignons.json"
FOREST_OUT = FRONT_MODELS / "forest_champignons.json"

SEED = 42
N_PER_CLASS = 300
FLIP_RATE = 0.10
DROP_RATE = 0.15
SIZE_JITTER = 0.15
ABSTAIN_THRESHOLD = 0.30
LEAF_MIN_PROB = 0.03


def collapse_sizes(df):
    df = df.copy()
    for col in [c for c in df.columns if c.endswith("_taille_min_cm")]:
        part = col[: -len("_taille_min_cm")]
        max_col = f"{part}_taille_max_cm"
        out = f"{part}_taille_cm"
        if max_col in df.columns:
            df[out] = (df[col].astype(float) + df[max_col].astype(float)) / 2
    drop = [c for c in df.columns if c.endswith("_taille_min_cm") or c.endswith("_taille_max_cm")]
    return df.drop(columns=drop)


def build_real(features):
    df = pd.read_csv(CLEAN_CSV)
    y = df["nom"].astype(str).str.strip()
    df = collapse_sizes(df.drop(columns=[c for c in ("nom", "statut") if c in df.columns]))
    for col in features:
        if col not in df.columns:
            df[col] = np.nan
    return df[features], y


def augment(X, y, features, rng):
    size_cols = [c for c in features if c.endswith("_taille_cm")]
    season_cols = [c for c in features if c.startswith("saison_mois_")]
    bin_cols = [c for c in features if c not in size_cols and c not in season_cols]
    size_i = [features.index(c) for c in size_cols]
    season_i = [features.index(c) for c in season_cols]
    bin_i = [features.index(c) for c in bin_cols]

    base = X.to_numpy(dtype=float)
    rows, labels = [], []
    for r in range(len(base)):
        proto = base[r]
        block = np.repeat(proto[None, :], N_PER_CLASS, axis=0)

        b = block[:, bin_i]
        flip = rng.random(b.shape) < FLIP_RATE
        b = np.where(flip, 1 - b, b)
        drop = rng.random(b.shape) < DROP_RATE
        b[drop] = np.nan
        block[:, bin_i] = b

        s = block[:, size_i]
        s = s * (1 + rng.uniform(-SIZE_JITTER, SIZE_JITTER, s.shape))
        sdrop = rng.random(s.shape) < DROP_RATE
        s[sdrop] = np.nan
        block[:, size_i] = s

        active = [j for j in season_i if proto[j] == 1]
        block[:, season_i] = 0
        if active:
            picks = rng.choice(active, size=N_PER_CLASS)
            block[np.arange(N_PER_CLASS), picks] = 1

        rows.append(block)
        labels += [y.iloc[r]] * N_PER_CLASS
    return np.vstack(rows), np.array(labels)


def perturb(base, features, rng, flip=0.0, drop=0.0):
    bin_i = [i for i, c in enumerate(features)
             if not c.endswith("_taille_cm") and not c.startswith("saison_mois_")]
    X = base.to_numpy(dtype=float).copy()
    sub = X[:, bin_i]
    if flip:
        m = rng.random(sub.shape) < flip
        sub = np.where(m, 1 - sub, sub)
    if drop:
        m = rng.random(sub.shape) < drop
        sub[m] = np.nan
    X[:, bin_i] = sub
    return X


def robust_report(name, model, Xreal, yi, features, rng):
    print(f"\n[{name}] robustesse sur les vraies donnees perturbees")
    print("  exact          :", round((model.predict(Xreal.to_numpy(float)) == yi).mean() * 100, 1), "%")
    for f in (0.05, 0.10, 0.20):
        Xp = perturb(Xreal, features, rng, flip=f)
        print(f"  flip {int(f*100):>2}%       :", round((model.predict(Xp) == yi).mean() * 100, 1), "%")
    for d in (0.10, 0.20):
        Xp = perturb(Xreal, features, rng, drop=d)
        print(f"  oubli {int(d*100):>2}%      :", round((model.predict(Xp) == yi).mean() * 100, 1), "%")


def export_tree(t, le):
    tr = t.tree_
    proba = tr.value / tr.value.sum(axis=2, keepdims=True)
    nodes = []
    for i in range(tr.node_count):
        if tr.children_left[i] == -1:
            dist = proba[i, 0]
            nz = np.nonzero(dist >= LEAF_MIN_PROB)[0]
            if len(nz) == 0:
                nz = [int(np.argmax(dist))]
            leaf = [[int(k), round(float(dist[k]), 3)] for k in nz]
            nodes.append({"leaf": leaf})
        else:
            thr = float(tr.threshold[i])
            if not np.isfinite(thr):
                thr = 1e38 if thr > 0 else -1e38
            nodes.append({
                "f": int(tr.feature[i]),
                "t": round(thr, 4),
                "l": int(tr.children_left[i]),
                "r": int(tr.children_right[i]),
                "m": int(tr.missing_go_to_left[i]),
            })
    return nodes


def main():
    rng = np.random.default_rng(SEED)
    features = json.loads(FEATURES_JSON.read_text(encoding="utf-8"))
    Xreal, y = build_real(features)

    le = LabelEncoder().fit(y)
    yi = le.transform(y)

    print(f"[1/4] Augmentation bruitee : {len(Xreal)} especes x {N_PER_CLASS} "
          f"(flip {FLIP_RATE:.0%}, oubli {DROP_RATE:.0%})")
    Xaug, yaug = augment(Xreal, y, features, rng)
    yaug_i = le.transform(yaug)

    print("[2/4] Arbre de decision...")
    tree = DecisionTreeClassifier(
        max_depth=18, min_samples_leaf=8, random_state=SEED,
    ).fit(Xaug, yaug_i)
    robust_report("arbre", tree, Xreal, yi, features, rng)

    print("\n[3/4] Foret aleatoire...")
    forest = RandomForestClassifier(
        n_estimators=25, max_depth=16, min_samples_leaf=12,
        max_features="sqrt", n_jobs=-1, random_state=SEED,
    ).fit(Xaug, yaug_i)
    robust_report("foret", forest, Xreal, yi, features, rng)

    print("\n[4/4] Export JSON pour le front...")
    FRONT_MODELS.mkdir(parents=True, exist_ok=True)
    labels = list(le.classes_)

    TREE_OUT.write_text(json.dumps({
        "kind": "tree",
        "labels": labels,
        "features": features,
        "abstain_threshold": ABSTAIN_THRESHOLD,
        "nodes": export_tree(tree, le),
    }, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    FOREST_OUT.write_text(json.dumps({
        "kind": "forest",
        "labels": labels,
        "features": features,
        "abstain_threshold": ABSTAIN_THRESHOLD,
        "trees": [export_tree(e, le) for e in forest.estimators_],
    }, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    print(f"  -> {TREE_OUT}  ({TREE_OUT.stat().st_size // 1024} Ko)")
    print(f"  -> {FOREST_OUT}  ({FOREST_OUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
