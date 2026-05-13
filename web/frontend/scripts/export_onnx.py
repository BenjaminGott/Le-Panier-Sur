"""Convert the trained XGBoost model to ONNX for use with onnxruntime-web.

Run from web/frontend/ :
    python scripts/export_onnx.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]
MODEL_DIR = PROJECT_ROOT / "model"
SRC_MODEL = MODEL_DIR / "xgb_champignons.json"
SRC_FEATURES = MODEL_DIR / "xgb_features.json"
SRC_LABELS = MODEL_DIR / "xgb_labels.json"
OUT_DIR = ROOT / "static" / "models"


def main() -> int:
    if not SRC_MODEL.exists():
        print(f"[!] model not found: {SRC_MODEL}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from xgboost import XGBClassifier
        from onnxmltools.convert import convert_xgboost
        from onnxmltools.convert.common.data_types import FloatTensorType
    except ImportError as exc:
        print(
            "[!] missing deps. Install with:\n"
            "    pip install xgboost onnxmltools onnxconverter-common skl2onnx onnxruntime",
            file=sys.stderr,
        )
        print(f"    error: {exc}", file=sys.stderr)
        return 1

    features = json.loads(SRC_FEATURES.read_text(encoding="utf-8"))
    n_features = len(features)

    model = XGBClassifier()
    model.load_model(str(SRC_MODEL))

    # onnxmltools veut des noms 'f0', 'f1', ... — on rebaptise le booster.
    # L'ordre est conservé (xgb_features.json garde la correspondance).
    booster = model.get_booster()
    booster.feature_names = [f"f{i}" for i in range(n_features)]

    initial_types = [("input", FloatTensorType([None, n_features]))]
    onnx_model = convert_xgboost(model, initial_types=initial_types, target_opset=15)

    out_path = OUT_DIR / "xgb_champignons.onnx"
    out_path.write_bytes(onnx_model.SerializeToString())

    shutil.copy2(SRC_FEATURES, OUT_DIR / "xgb_features.json")
    shutil.copy2(SRC_LABELS, OUT_DIR / "xgb_labels.json")

    print(f"[ok] {n_features} features, {len(json.loads(SRC_LABELS.read_text(encoding='utf-8')))} classes")
    print(f"[ok] -> {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
