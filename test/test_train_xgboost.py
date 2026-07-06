"""Tests unitaires pour model/train_xgboost.py.

Couvre :
  - collapse_size_ranges  : fusion des colonnes min/max en une seule valeur
  - inject_missing        : injection aléatoire de NaN
  - top_x                 : extraction et tri des k meilleures prédictions
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import LabelEncoder

import train_xgboost as tx


# ---------------------------------------------------------------------------
# collapse_size_ranges
# ---------------------------------------------------------------------------
class TestCollapseSizeRanges:
    def test_colonnes_min_max_remplacees(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0, 3.0],
            "chapeau_taille_max_cm": [10.0, 7.0],
            "autre_col": [1, 2],
        })
        result = tx.collapse_size_ranges(df, rng)

        assert "chapeau_taille_cm" in result.columns
        assert "chapeau_taille_min_cm" not in result.columns
        assert "chapeau_taille_max_cm" not in result.columns
        assert "autre_col" in result.columns

    def test_valeurs_dans_intervalle(self):
        rng = np.random.default_rng(42)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0] * 200,
            "chapeau_taille_max_cm": [10.0] * 200,
        })
        result = tx.collapse_size_ranges(df, rng)

        assert (result["chapeau_taille_cm"] >= 5.0).all()
        assert (result["chapeau_taille_cm"] <= 10.0).all()

    def test_sans_colonnes_size_retourne_intact(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({"col_a": [1, 2], "col_b": [3, 4]})
        result = tx.collapse_size_ranges(df, rng)

        pd.testing.assert_frame_equal(result, df)

    def test_ne_modifie_pas_original(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0],
            "chapeau_taille_max_cm": [10.0],
        })
        colonnes_avant = list(df.columns)
        tx.collapse_size_ranges(df, rng)

        assert list(df.columns) == colonnes_avant

    def test_plusieurs_parties_collapsees(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "chapeau_taille_min_cm": [5.0],
            "chapeau_taille_max_cm": [10.0],
            "pied_taille_min_cm": [2.0],
            "pied_taille_max_cm": [4.0],
        })
        result = tx.collapse_size_ranges(df, rng)

        assert "chapeau_taille_cm" in result.columns
        assert "pied_taille_cm" in result.columns
        assert len(result.columns) == 2

    def test_min_egal_max_valeur_fixe(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "pied_taille_min_cm": [7.0] * 50,
            "pied_taille_max_cm": [7.0] * 50,
        })
        result = tx.collapse_size_ranges(df, rng)

        np.testing.assert_array_almost_equal(result["pied_taille_cm"].values, 7.0)


# ---------------------------------------------------------------------------
# inject_missing
# ---------------------------------------------------------------------------
class TestInjectMissing:
    def test_rate_zero_aucun_nan(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame(np.ones((20, 10)))
        result = tx.inject_missing(df, 0.0, rng)

        assert not result.isna().any().any()

    def test_rate_un_tout_nan(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame(np.ones((20, 10)))
        result = tx.inject_missing(df, 1.0, rng)

        assert result.isna().all().all()

    def test_taux_observe_proche_du_taux_demande(self):
        rng = np.random.default_rng(42)
        n_rows, n_cols = 2000, 50
        df = pd.DataFrame(np.ones((n_rows, n_cols)))
        rate = 0.15
        result = tx.inject_missing(df, rate, rng)

        taux_reel = result.isna().sum().sum() / (n_rows * n_cols)
        assert abs(taux_reel - rate) < 0.02

    def test_ne_modifie_pas_original(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame(np.ones((10, 5)))
        valeurs_avant = df.values.copy()
        tx.inject_missing(df, 0.5, rng)

        np.testing.assert_array_equal(df.values, valeurs_avant)

    def test_retourne_meme_shape(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame(np.ones((7, 13)))
        result = tx.inject_missing(df, 0.3, rng)

        assert result.shape == df.shape

    def test_colonnes_et_index_preserves(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame(np.ones((5, 3)), columns=["a", "b", "c"])
        result = tx.inject_missing(df, 0.2, rng)

        assert list(result.columns) == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# top_x
# ---------------------------------------------------------------------------
class TestTopX:
    def test_retourne_x_meilleures_especes(self):
        proba = np.array([[0.1, 0.5, 0.3, 0.05, 0.05]])
        classes = np.array(["A", "B", "C", "D", "E"])
        result = tx.top_x(proba, classes, x=3)

        assert len(result) == 1
        assert len(result[0]) == 3
        assert result[0][0]["espece"] == "B"
        assert result[0][1]["espece"] == "C"
        assert result[0][2]["espece"] == "A"

    def test_confiance_en_pourcentage(self):
        proba = np.array([[0.0, 1.0, 0.0]])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=1)

        assert result[0][0]["confiance_%"] == pytest.approx(100.0)

    def test_x_plafonne_a_n_classes(self):
        proba = np.array([[0.5, 0.3, 0.2]])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=10)

        assert len(result[0]) == 3

    def test_plusieurs_echantillons(self):
        proba = np.array([
            [0.9, 0.05, 0.05],
            [0.1, 0.8, 0.1],
        ])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=1)

        assert len(result) == 2
        assert result[0][0]["espece"] == "A"
        assert result[1][0]["espece"] == "B"

    def test_tri_decroissant(self):
        proba = np.array([[0.1, 0.6, 0.3]])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=3)

        confiances = [r["confiance_%"] for r in result[0]]
        assert confiances == sorted(confiances, reverse=True)

    def test_x_minimum_est_1(self):
        proba = np.array([[0.5, 0.3, 0.2]])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=0)

        assert len(result[0]) == 1

    def test_vecteur_1d_promeut(self):
        proba = np.array([0.2, 0.7, 0.1])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=1)

        assert result[0][0]["espece"] == "B"

    def test_confiance_arrondie_2_decimales(self):
        proba = np.array([[1 / 3, 1 / 3, 1 / 3]])
        classes = np.array(["A", "B", "C"])
        result = tx.top_x(proba, classes, x=1)

        conf = result[0][0]["confiance_%"]
        assert conf == round(conf, 2)

    def test_structure_des_dicts(self):
        proba = np.array([[0.6, 0.4]])
        classes = np.array(["Cèpe", "Amanite"])
        result = tx.top_x(proba, classes, x=2)

        for item in result[0]:
            assert "espece" in item
            assert "confiance_%" in item
            assert isinstance(item["espece"], str)
            assert isinstance(item["confiance_%"], float)


# ---------------------------------------------------------------------------
# predict_top_x (intégration légère : nécessite un modèle XGBoost minimal)
# ---------------------------------------------------------------------------
class TestPredictTopX:
    @pytest.fixture
    def mini_model(self):
        """Entraîne un XGBoost minimaliste sur 3 classes fictives."""
        from xgboost import XGBClassifier

        rng = np.random.default_rng(0)
        X = pd.DataFrame(rng.random((60, 5)), columns=[f"f{i}" for i in range(5)])
        y_raw = np.array(["A"] * 20 + ["B"] * 20 + ["C"] * 20)

        le = LabelEncoder()
        y = le.fit_transform(y_raw)

        model = XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=10,
            random_state=0,
        )
        model.fit(X, y)
        return model, le

    def test_retourne_liste_de_predictions(self, mini_model):
        model, le = mini_model
        rng = np.random.default_rng(0)
        X = pd.DataFrame(rng.random((3, 5)), columns=[f"f{i}" for i in range(5)])
        result = tx.predict_top_x(model, X, le, x=2)

        assert len(result) == 3
        for preds in result:
            assert len(preds) == 2
            assert all("espece" in p and "confiance_%" in p for p in preds)

    def test_somme_probas_proche_de_100(self, mini_model):
        model, le = mini_model
        X = pd.DataFrame(np.ones((1, 5)), columns=[f"f{i}" for i in range(5)])
        result = tx.predict_top_x(model, X, le, x=3)

        total = sum(p["confiance_%"] for p in result[0])
        assert abs(total - 100.0) < 0.1
