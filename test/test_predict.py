"""Tests unitaires pour model/predict.py.

Couvre :
  - collapse_size_ranges  : fusion des colonnes min/max en une seule valeur
  - align_features        : réordonnancement, valeurs manquantes, marqueur UNKNOWN
  - top_x                 : extraction et tri des k meilleures prédictions
  - predict_from_dataframe: intégration légère avec un modèle minimal
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from xgboost import XGBClassifier

import predict as pr


# ---------------------------------------------------------------------------
# collapse_size_ranges (predict.py)
# ---------------------------------------------------------------------------
class TestCollapseSizeRangesPredict:
    def test_collapse_basique(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0],
            "chapeau_taille_max_cm": [10.0],
        })
        result = pr.collapse_size_ranges(df, rng)

        assert "chapeau_taille_cm" in result.columns
        assert "chapeau_taille_min_cm" not in result.columns
        assert "chapeau_taille_max_cm" not in result.columns

    def test_valeurs_dans_intervalle(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "pied_taille_min_cm": [2.0] * 100,
            "pied_taille_max_cm": [6.0] * 100,
        })
        result = pr.collapse_size_ranges(df, rng)

        assert (result["pied_taille_cm"] >= 2.0).all()
        assert (result["pied_taille_cm"] <= 6.0).all()

    def test_ne_modifie_pas_original(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0],
            "chapeau_taille_max_cm": [10.0],
        })
        nb_cols_avant = len(df.columns)
        pr.collapse_size_ranges(df, rng)

        assert len(df.columns) == nb_cols_avant

    def test_sans_colonnes_size_retourne_intact(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({"a": [1.0], "b": [2.0]})
        result = pr.collapse_size_ranges(df, rng)

        pd.testing.assert_frame_equal(result, df)


# ---------------------------------------------------------------------------
# align_features
# ---------------------------------------------------------------------------
class TestAlignFeatures:
    def test_reordonnancement_colonnes(self):
        df = pd.DataFrame({"b": [1.0], "a": [2.0]})
        result = pr.align_features(df, ["a", "b"])

        assert list(result.columns) == ["a", "b"]
        assert result["a"].iloc[0] == pytest.approx(2.0)
        assert result["b"].iloc[0] == pytest.approx(1.0)

    def test_features_absentes_remplies_nan(self):
        df = pd.DataFrame({"a": [1.0]})
        result = pr.align_features(df, ["a", "b", "c"])

        assert np.isnan(result["b"].iloc[0])
        assert np.isnan(result["c"].iloc[0])

    def test_marqueur_inconnu_devient_nan(self):
        """La valeur sentinelle 3 (UNKNOWN_MARKER) → NaN sur les features binaires."""
        df = pd.DataFrame({
            "has_ring": [3.0],
            "is_edible": [1.0],
        })
        result = pr.align_features(df, ["has_ring", "is_edible"])

        assert np.isnan(result["has_ring"].iloc[0])
        assert result["is_edible"].iloc[0] == pytest.approx(1.0)

    def test_taille_cm_non_convertie(self):
        """*_taille_cm avec valeur 3 ne doit PAS être transformée en NaN."""
        df = pd.DataFrame({"chapeau_taille_cm": [3.0]})
        result = pr.align_features(df, ["chapeau_taille_cm"])

        assert result["chapeau_taille_cm"].iloc[0] == pytest.approx(3.0)

    def test_collapse_declenche_si_min_max(self):
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [4.0],
            "chapeau_taille_max_cm": [8.0],
        })
        result = pr.align_features(df, ["chapeau_taille_cm"])

        assert "chapeau_taille_cm" in result.columns
        assert 4.0 <= result["chapeau_taille_cm"].iloc[0] <= 8.0

    def test_sortie_est_float(self):
        df = pd.DataFrame({"a": [1], "b": [0]})
        result = pr.align_features(df, ["a", "b"])

        assert result["a"].dtype == float
        assert result["b"].dtype == float

    def test_colonnes_extras_ignorees(self):
        df = pd.DataFrame({"a": [1.0], "b": [2.0], "extra": [99.0]})
        result = pr.align_features(df, ["a", "b"])

        assert "extra" not in result.columns
        assert list(result.columns) == ["a", "b"]

    def test_zero_et_un_preserves(self):
        """Les valeurs 0 et 1 (binaire) ne doivent pas être altérées."""
        df = pd.DataFrame({"f1": [0.0], "f2": [1.0]})
        result = pr.align_features(df, ["f1", "f2"])

        assert result["f1"].iloc[0] == pytest.approx(0.0)
        assert result["f2"].iloc[0] == pytest.approx(1.0)

    def test_dataframe_vide_retourne_bon_schema(self):
        df = pd.DataFrame(columns=["a"])
        result = pr.align_features(df, ["a", "b"])

        assert list(result.columns) == ["a", "b"]
        assert len(result) == 0


# ---------------------------------------------------------------------------
# top_x (predict.py — signature légèrement différente de train_xgboost)
# ---------------------------------------------------------------------------
class TestTopXPredict:
    def test_tri_decroissant(self):
        proba = np.array([[0.2, 0.7, 0.1]])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=3)

        scores = [r["confiance_%"] for r in result[0]]
        assert scores == sorted(scores, reverse=True)

    def test_meilleure_classe(self):
        proba = np.array([[0.05, 0.05, 0.9]])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=1)

        assert result[0][0]["espece"] == "C"
        assert result[0][0]["confiance_%"] == pytest.approx(90.0, abs=0.01)

    def test_x_1_retourne_un_seul(self):
        proba = np.array([[0.3, 0.5, 0.2]])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=1)

        assert len(result[0]) == 1

    def test_plusieurs_echantillons(self):
        proba = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=1)

        assert len(result) == 2
        assert result[0][0]["espece"] == "A"
        assert result[1][0]["espece"] == "C"

    def test_confiance_arrondie(self):
        proba = np.array([[1 / 3, 1 / 3, 1 / 3]])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=1)

        conf = result[0][0]["confiance_%"]
        assert conf == round(conf, 2)

    def test_x_plafonne_a_n_classes(self):
        proba = np.array([[0.4, 0.35, 0.25]])
        classes = ["A", "B", "C"]
        result = pr.top_x(proba, classes, x=100)

        assert len(result[0]) == 3


# ---------------------------------------------------------------------------
# predict_from_dataframe (intégration légère)
# ---------------------------------------------------------------------------
class TestPredictFromDataframe:
    @pytest.fixture
    def artefacts(self):
        """XGBoost entraîné sur 3 classes fictives + liste de features."""
        rng = np.random.default_rng(0)
        features = [f"f{i}" for i in range(5)]
        classes = ["Cèpe", "Amanite", "Girolle"]

        X = pd.DataFrame(rng.random((60, 5)), columns=features)
        y = np.array([0] * 20 + [1] * 20 + [2] * 20)

        model = XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=10,
            random_state=0,
        )
        model.fit(X, y)
        return model, classes, features

    def test_nombre_resultats_egal_nb_lignes(self, artefacts):
        model, classes, features = artefacts
        rng = np.random.default_rng(1)
        df = pd.DataFrame(rng.random((4, 5)), columns=features)
        result = pr.predict_from_dataframe(df, model, classes, features, top=2)

        assert len(result) == 4

    def test_nombre_predictions_par_echantillon(self, artefacts):
        model, classes, features = artefacts
        df = pd.DataFrame(np.ones((2, 5)), columns=features)
        result = pr.predict_from_dataframe(df, model, classes, features, top=2)

        for preds in result:
            assert len(preds) == 2

    def test_espece_dans_liste_des_classes(self, artefacts):
        model, classes, features = artefacts
        df = pd.DataFrame(np.ones((1, 5)), columns=features)
        result = pr.predict_from_dataframe(df, model, classes, features, top=3)

        for pred in result[0]:
            assert pred["espece"] in classes

    def test_features_manquantes_acceptees(self, artefacts):
        """Un DataFrame avec des features absentes (→ NaN) ne doit pas planter."""
        model, classes, features = artefacts
        df = pd.DataFrame({"f0": [1.0], "f1": [0.5]})
        result = pr.predict_from_dataframe(df, model, classes, features, top=1)

        assert len(result) == 1
        assert len(result[0]) == 1

    def test_top_1_retourne_prediction_unique(self, artefacts):
        model, classes, features = artefacts
        df = pd.DataFrame(np.ones((3, 5)), columns=features)
        result = pr.predict_from_dataframe(df, model, classes, features, top=1)

        for preds in result:
            assert len(preds) == 1


# ---------------------------------------------------------------------------
# load_artifacts (smoke test — nécessite les fichiers modèle)
# ---------------------------------------------------------------------------
class TestLoadArtifacts:
    def test_charge_avec_fichiers_factices(self, tmp_path):
        """Vérifie que load_artifacts lit correctement le JSON des labels et features."""
        labels = ["Cèpe", "Amanite"]
        feats = ["f0", "f1", "f2"]

        labels_file = tmp_path / "xgb_labels.json"
        feats_file = tmp_path / "xgb_features.json"
        labels_file.write_text(json.dumps(labels), encoding="utf-8")
        feats_file.write_text(json.dumps(feats), encoding="utf-8")

        # On remplace les chemins globaux dans le module pour ce test
        with (
            patch.object(pr, "LABELS_PATH", labels_file),
            patch.object(pr, "FEATURES_PATH", feats_file),
            patch.object(pr, "MODEL_PATH", tmp_path / "xgb_champignons.json"),
        ):
            mock_model = MagicMock(spec=XGBClassifier)
            with patch("predict.XGBClassifier", return_value=mock_model):
                model, classes_loaded, features_loaded = pr.load_artifacts()

        assert classes_loaded == labels
        assert features_loaded == feats
