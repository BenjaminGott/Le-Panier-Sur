"""Fixtures partagées entre les suites de tests."""

import sys
from pathlib import Path

# Rendre les modules model/ importables depuis n'importe quel test
MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))
