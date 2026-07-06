"""Verifie le surentrainement du XGBoost existant.

Constat : les 217000 lignes "augmentees" ne contiennent que 217 empreintes
binaires distinctes (une par espece, recopiee 1000x). Le modele memorise donc
ces empreintes exactes : parfait quand l'entree correspond pile, mais il
s'effondre des qu'un utilisateur se trompe d'observation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from train_xgboost import load_dataset

ROOT = Path(__file__).resolve().parents[1]
AUG = ROOT / "data" / "clean_train_data" / "champignons_augmented.csv"
CLEAN = ROOT / "data" / "clean_train_data" / "champignons_clean.csv"


def diversite():
    df = pd.read_csv(AUG)
    bincols = [c for c in df.columns
               if not c.startswith("saison_mois_") and df[c].dropna().isin([0, 1]).all()]
    print("Diversite du dataset augmente :")
    print(f"  lignes                       : {len(df)}")
    print(f"  especes                      : {df['nom'].nunique()}")
    print(f"  empreintes binaires distinctes: {df[bincols].drop_duplicates().shape[0]}")
    print("  => 217 empreintes recopiees 1000x : rien a generaliser.\n")


def robustesse():
    feats = json.loads((ROOT / "model" / "xgb_features.json").read_text(encoding="utf-8"))
    labels = json.loads((ROOT / "model" / "xgb_labels.json").read_text(encoding="utf-8"))
    lab2i = {l: i for i, l in enumerate(labels)}

    model = XGBClassifier()
    model.load_model(str(ROOT / "model" / "xgb_champignons.json"))

    rng = np.random.default_rng(0)
    X, y, _ = load_dataset(CLEAN, feature_order=feats, rng=rng)
    keep = y.isin(lab2i).values
    X, y = X.loc[keep].reset_index(drop=True), y[keep].reset_index(drop=True)
    yi = y.map(lab2i).values
    bincols = [c for c in X.columns if set(pd.unique(X[c].dropna())) <= {0, 1}]

    def acc(A):
        return round(float((np.argmax(model.predict_proba(A), axis=1) == yi).mean()) * 100, 1)

    print("Robustesse du XGBoost sur les vraies donnees :")
    print(f"  entree exacte                : {acc(X)} %")
    for rate in (0.05, 0.10, 0.20):
        A = X.copy()
        arr = A[bincols].to_numpy(float)
        arr[rng.random(arr.shape) < rate] = np.nan
        A[bincols] = arr
        print(f"  {int(rate*100):>2}% oublies (NaN)         : {acc(A)} %")
    for rate in (0.05, 0.10, 0.20):
        A = X.copy()
        arr = A[bincols].to_numpy(float)
        m = rng.random(arr.shape) < rate
        arr[m] = 1 - arr[m]
        A[bincols] = arr
        print(f"  {int(rate*100):>2}% mal observes (flip)   : {acc(A)} %")


if __name__ == "__main__":
    diversite()
    robustesse()
