"""Entraînement d'un XGBoost Classifier pour l'identification de 219 espèces
de champignons (projet "Le Panier-Sûr").

- Entraînement sur le dataset synthétique augmenté (~219 000 lignes).
- Évaluation sur le test synthétique ET sur le petit set de données réelles
  pour vérifier le transfert de connaissance.
- Robustesse aux données manquantes (XGBoost gère nativement les NaN ;
  on simule aussi du masquage aléatoire à l'entraînement).
- Fonction `top_x` qui retourne les x espèces les plus crédibles avec leur
  score de confiance en %.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "clean_train_data"
SYNTHETIC_CSV = DATA_DIR / "champignons_augmented.csv"
REAL_CSV = DATA_DIR / "champignons_clean.csv"

MODEL_DIR = PROJECT_ROOT / "model"
MODEL_OUT = MODEL_DIR / "xgb_champignons.json"
ONNX_OUT = MODEL_DIR / "xgb_champignons.onnx"
LABELS_OUT = MODEL_DIR / "xgb_labels.json"
FEATURES_OUT = MODEL_DIR / "xgb_features.json"

RANDOM_STATE = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.10
MISSING_NOISE_RATE = 0.10  # proba de masquer une cellule pour simuler des entrées incomplètes


# ---------------------------------------------------------------------------
# Chargement / préparation des données
# ---------------------------------------------------------------------------
def collapse_size_ranges(X: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Remplace chaque paire `*_taille_min_cm` / `*_taille_max_cm` par une
    unique colonne `*_taille_cm` tirée uniformément dans [min, max].

    On s'aligne ainsi sur le format du dataset augmenté / du formulaire
    utilisateur qui ne donne qu'UNE mesure par partie.
    """
    X = X.copy()
    for col in [c for c in X.columns if c.endswith("_taille_min_cm")]:
        part = col[: -len("_taille_min_cm")]
        max_col = f"{part}_taille_max_cm"
        out_col = f"{part}_taille_cm"
        if max_col in X.columns and out_col not in X.columns:
            vmin = X[col].to_numpy(dtype=float)
            vmax = X[max_col].to_numpy(dtype=float)
            u = rng.uniform(size=len(X))
            X[out_col] = vmin + u * (vmax - vmin)
    drop = [c for c in X.columns if c.endswith("_taille_min_cm") or c.endswith("_taille_max_cm")]
    return X.drop(columns=drop)


def load_dataset(
    path: Path,
    feature_order: list[str] | None = None,
    rng: np.random.Generator | None = None,
):
    """Charge un CSV et renvoie (X, y, feature_names).

    La colonne `nom` sert de cible ; `statut` est exclu des features car
    corrélé à la cible (fuite d'information). Si le CSV contient encore les
    `*_taille_min_cm`/`*_taille_max_cm` (cas du CSV clean), on les collapse
    en une taille unique tirée uniformément.
    """
    df = pd.read_csv(path)
    y = df["nom"].astype(str).str.strip()
    drop_cols = [c for c in ("nom", "statut") if c in df.columns]
    X = df.drop(columns=drop_cols)

    if any(c.endswith("_taille_min_cm") for c in X.columns):
        X = collapse_size_ranges(X, rng or np.random.default_rng(RANDOM_STATE))

    if feature_order is not None:
        # Aligne les colonnes sur l'ordre de référence (colonnes manquantes -> NaN)
        for col in feature_order:
            if col not in X.columns:
                X[col] = np.nan
        X = X[feature_order]

    return X, y, list(X.columns)


def inject_missing(X: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Masque aléatoirement `rate`% des cellules en NaN pour rendre le modèle
    robuste à des formulaires utilisateur partiellement remplis."""
    if rate <= 0:
        return X
    arr = X.to_numpy(dtype=float, copy=True)
    mask = rng.random(arr.shape) < rate
    arr[mask] = np.nan
    return pd.DataFrame(arr, index=X.index, columns=X.columns)


# ---------------------------------------------------------------------------
# Entraînement
# ---------------------------------------------------------------------------
def train_model(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    n_classes: int,
) -> XGBClassifier:
    model = XGBClassifier(
        objective="multi:softprob",
        num_class=n_classes,
        tree_method="hist",
        n_estimators=600,
        learning_rate=0.1,
        max_depth=8,
        min_child_weight=2,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        eval_metric=["mlogloss", "merror"],
        early_stopping_rounds=30,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=50,
    )
    return model


# ---------------------------------------------------------------------------
# Prédiction Top-x
# ---------------------------------------------------------------------------
def top_x(
    proba: np.ndarray,
    classes: np.ndarray,
    x: int = 3,
) -> list[list[dict]]:
    """À partir d'une matrice de probabilités (n_samples, n_classes), renvoie
    pour chaque échantillon la liste des `x` espèces les plus crédibles avec
    leur score de confiance en %.

    Exemple de sortie pour un échantillon :
        [{"espece": "CEPE DE BORDEAUX", "confiance_%": 87.42}, ...]
    """
    proba = np.atleast_2d(proba)
    x = max(1, min(x, proba.shape[1]))
    # argpartition pour récupérer les top-x sans tout trier, puis tri décroissant
    top_idx_unsorted = np.argpartition(-proba, kth=x - 1, axis=1)[:, :x]
    results: list[list[dict]] = []
    for row, idx_row in zip(proba, top_idx_unsorted):
        sorted_idx = idx_row[np.argsort(-row[idx_row])]
        results.append(
            [
                {"espece": str(classes[i]), "confiance_%": round(float(row[i] * 100), 2)}
                for i in sorted_idx
            ]
        )
    return results


def predict_top_x(
    model: XGBClassifier,
    X: pd.DataFrame,
    label_encoder: LabelEncoder,
    x: int = 3,
) -> list[list[dict]]:
    proba = model.predict_proba(X)
    return top_x(proba, label_encoder.classes_, x=x)


# ---------------------------------------------------------------------------
# Évaluation
# ---------------------------------------------------------------------------
def evaluate(
    model: XGBClassifier,
    X: pd.DataFrame,
    y_true: np.ndarray,
    label_encoder: LabelEncoder,
    tag: str,
) -> dict:
    proba = model.predict_proba(X)
    y_pred = np.argmax(proba, axis=1)

    # top-k accuracy avec les labels réellement présents (XGBoost renvoie
    # les probas sur TOUTES les classes vues à l'entraînement)
    labels = np.arange(len(label_encoder.classes_))
    metrics = {
        "dataset": tag,
        "n_samples": int(len(y_true)),
        "top1_accuracy": float(accuracy_score(y_true, y_pred)),
        "top3_accuracy": float(top_k_accuracy_score(y_true, proba, k=3, labels=labels)),
        "top5_accuracy": float(top_k_accuracy_score(y_true, proba, k=5, labels=labels)),
    }
    print(f"\n=== Évaluation [{tag}] ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Rapport détaillé (concis pour 219 classes : on n'affiche que l'accuracy globale)
    if tag == "real":
        present = np.unique(np.concatenate([y_true, y_pred]))
        print(
            classification_report(
                y_true,
                y_pred,
                labels=present,
                target_names=label_encoder.inverse_transform(present),
                zero_division=0,
                digits=3,
            )
        )
    return metrics


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(RANDOM_STATE)

    print("[1/5] Chargement du dataset synthétique...")
    X_synth, y_synth, feature_names = load_dataset(SYNTHETIC_CSV, rng=rng)
    print(f"  -> {X_synth.shape[0]} lignes, {X_synth.shape[1]} features")

    # Encodage des 219 espèces en entiers
    label_encoder = LabelEncoder()
    y_synth_enc = label_encoder.fit_transform(y_synth)
    n_classes = len(label_encoder.classes_)
    print(f"  -> {n_classes} classes distinctes")

    print("[2/5] Split train / val / test (stratifié)...")
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X_synth, y_synth_enc,
        test_size=TEST_SIZE, stratify=y_synth_enc, random_state=RANDOM_STATE,
    )
    val_rel = VAL_SIZE / (1.0 - TEST_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp,
        test_size=val_rel, stratify=y_tmp, random_state=RANDOM_STATE,
    )

    # Simulation de formulaires incomplets côté entraînement uniquement
    X_train_noisy = inject_missing(X_train, MISSING_NOISE_RATE, rng)
    print(f"  train={len(X_train)}  val={len(X_val)}  test={len(X_test)}  "
          f"(masquage NaN sur {MISSING_NOISE_RATE:.0%} des cellules d'entraînement)")

    print("[3/5] Entraînement XGBoost (tree_method=hist, early_stopping=30)...")
    model = train_model(X_train_noisy, y_train, X_val, y_val, n_classes=n_classes)
    best_iter = getattr(model, "best_iteration", None)
    print(f"  -> best_iteration = {best_iter}")

    print("[4/5] Évaluation...")
    evaluate(model, X_test, y_test, label_encoder, tag="synthetic_test")

    # Transfer check : petit dataset de données réelles (champignons_clean.csv)
    try:
        X_real, y_real, _ = load_dataset(REAL_CSV, feature_order=feature_names, rng=rng)
        # On ne garde que les espèces vues à l'entraînement
        known = np.isin(y_real, label_encoder.classes_)
        if known.sum() == 0:
            print("  ! Aucune espèce du set réel ne matche les classes entraînées.")
        else:
            X_real = X_real.loc[known].reset_index(drop=True)
            y_real_enc = label_encoder.transform(y_real[known])
            evaluate(model, X_real, y_real_enc, label_encoder, tag="real")
    except FileNotFoundError:
        print(f"  ! {REAL_CSV} introuvable, étape transfert ignorée.")

    print("[5/5] Sauvegarde du modèle et des artefacts...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_OUT))
    LABELS_OUT.write_text(
        json.dumps(list(label_encoder.classes_), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    FEATURES_OUT.write_text(
        json.dumps(feature_names, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> {MODEL_OUT}")
    print(f"  -> {LABELS_OUT}")
    print(f"  -> {FEATURES_OUT}")

    model.save_model(str(ONNX_OUT))
    print(f"  -> {ONNX_OUT}")

    # Démo rapide du top-x sur quelques échantillons réels
    if REAL_CSV.exists():
        demo_X, demo_y, _ = load_dataset(REAL_CSV, feature_order=feature_names, rng=rng)
        demo_preds = predict_top_x(model, demo_X.head(5), label_encoder, x=3)
        print("\nDémo top-3 sur 5 échantillons réels :")
        for truth, preds in zip(demo_y.head(5), demo_preds):
            print(f"  vrai={truth!s:35s} -> {preds}")


if __name__ == "__main__":
    main()
