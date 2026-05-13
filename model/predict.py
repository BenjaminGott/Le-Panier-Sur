"""Inférence avec le modèle XGBoost entraîné (projet "Le Panier-Sûr").

Utilisation :
    # 1) Prédire sur le CSV des données réelles
    python model/predict.py --csv data/clean_train_data/champignons_clean.csv --top 3

    # 2) Prédire à partir d'un JSON (formulaire utilisateur, champs partiels autorisés)
    python model/predict.py --json model/sample_input.json --top 5

    # 3) Sans argument : démo rapide sur quelques lignes réelles
    python model/predict.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "model"
MODEL_PATH = MODEL_DIR / "xgb_champignons.json"
LABELS_PATH = MODEL_DIR / "xgb_labels.json"
FEATURES_PATH = MODEL_DIR / "xgb_features.json"
DEMO_CSV = PROJECT_ROOT / "data" / "clean_train_data" / "champignons_clean.csv"


# ---------------------------------------------------------------------------
# Chargement des artefacts
# ---------------------------------------------------------------------------
def load_artifacts() -> tuple[XGBClassifier, list[str], list[str]]:
    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))
    classes = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
    return model, classes, features


def collapse_size_ranges(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Si l'entrée contient des paires `*_taille_min_cm`/`*_taille_max_cm`
    (cas du CSV clean ou d'un formulaire qui fournirait min+max), les collapse
    en une unique colonne `*_taille_cm` tirée uniformément dans [min, max]."""
    df = df.copy()
    for col in [c for c in df.columns if c.endswith("_taille_min_cm")]:
        part = col[: -len("_taille_min_cm")]
        max_col = f"{part}_taille_max_cm"
        out_col = f"{part}_taille_cm"
        if max_col in df.columns and out_col not in df.columns:
            vmin = df[col].to_numpy(dtype=float)
            vmax = df[max_col].to_numpy(dtype=float)
            u = rng.uniform(size=len(df))
            df[out_col] = vmin + u * (vmax - vmin)
    drop = [c for c in df.columns if c.endswith("_taille_min_cm") or c.endswith("_taille_max_cm")]
    return df.drop(columns=drop)


UNKNOWN_MARKER = 3  # convention : 0=non, 1=oui, 3=inconnu -> NaN en interne


def align_features(df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
    """Garantit que les colonnes sont dans le bon ordre ; colonnes manquantes
    remplies par NaN (XGBoost sait les gérer).

    Convention d'entrée pour les features binaires : 0 = non, 1 = oui,
    3 = information inconnue. Les `3` sont traduits en NaN pour qu'XGBoost
    les traite comme des valeurs manquantes.
    """
    rng = np.random.default_rng(42)
    if any(c.endswith("_taille_min_cm") for c in df.columns):
        df = collapse_size_ranges(df, rng)
    for col in feature_names:
        if col not in df.columns:
            df[col] = np.nan
    df = df[feature_names].astype(float)
    # Traduit la valeur sentinelle "inconnu" en NaN sur les features binaires
    bin_cols = [c for c in feature_names if not c.endswith("_cm")]
    if bin_cols:
        df[bin_cols] = df[bin_cols].mask(df[bin_cols] == UNKNOWN_MARKER)
    return df


# ---------------------------------------------------------------------------
# Top-x (identique à celui de train_xgboost)
# ---------------------------------------------------------------------------
def top_x(proba: np.ndarray, classes: list[str], x: int = 3) -> list[list[dict]]:
    proba = np.atleast_2d(proba)
    x = max(1, min(x, proba.shape[1]))
    top_idx = np.argpartition(-proba, kth=x - 1, axis=1)[:, :x]
    out = []
    for row, idx_row in zip(proba, top_idx):
        sorted_idx = idx_row[np.argsort(-row[idx_row])]
        out.append(
            [
                {"espece": classes[i], "confiance_%": round(float(row[i] * 100), 2)}
                for i in sorted_idx
            ]
        )
    return out


def predict_from_dataframe(
    df: pd.DataFrame,
    model: XGBClassifier,
    classes: list[str],
    features: list[str],
    top: int = 3,
) -> list[list[dict]]:
    X = align_features(df.copy(), features)
    proba = model.predict_proba(X)
    return top_x(proba, classes, x=top)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Inférence XGBoost champignons")
    parser.add_argument("--csv", type=str, help="CSV avec les mêmes colonnes que l'entraînement")
    parser.add_argument(
        "--json",
        type=str,
        help="JSON : un dict (1 échantillon) ou une liste de dicts. Champs manquants autorisés.",
    )
    parser.add_argument("--top", type=int, default=3, help="Nombre d'espèces à retourner (défaut 3)")
    parser.add_argument("--n", type=int, default=5, help="Nombre de lignes à afficher si --csv")
    args = parser.parse_args()

    model, classes, features = load_artifacts()
    print(f"Modèle chargé : {len(classes)} classes, {len(features)} features.")

    # --- cas 1 : CSV
    if args.csv:
        df = pd.read_csv(args.csv)
        truths = df["nom"].tolist() if "nom" in df.columns else [None] * len(df)
        df_in = df.drop(columns=[c for c in ("nom", "statut") if c in df.columns])
        preds = predict_from_dataframe(df_in.head(args.n), model, classes, features, top=args.top)
        for truth, p in zip(truths[: args.n], preds):
            print(f"  vrai={truth!s:35s} -> {p}")
        return

    # --- cas 2 : JSON
    if args.json:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = [payload]
        df_in = pd.DataFrame(payload)
        preds = predict_from_dataframe(df_in, model, classes, features, top=args.top)
        for i, p in enumerate(preds):
            print(f"  sample {i} -> {p}")
        return

    # --- cas 3 : démo
    if DEMO_CSV.exists():
        df = pd.read_csv(DEMO_CSV)
        truths = df["nom"].tolist()
        df_in = df.drop(columns=[c for c in ("nom", "statut") if c in df.columns])
        preds = predict_from_dataframe(df_in.head(args.n), model, classes, features, top=args.top)
        print(f"\nDémo top-{args.top} sur {args.n} échantillons de {DEMO_CSV.name} :")
        for truth, p in zip(truths[: args.n], preds):
            print(f"  vrai={truth!s:35s} -> {p}")
    else:
        print("Aucune entrée fournie et pas de CSV démo trouvé. Utilise --csv ou --json.")


if __name__ == "__main__":
    main()
