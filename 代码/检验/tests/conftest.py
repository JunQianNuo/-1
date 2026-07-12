"""Path setup for standalone validation-package tests."""

from __future__ import annotations

import sys
from pathlib import Path


VALIDATION_DIR = Path(__file__).resolve().parents[1]
for directory in (
    VALIDATION_DIR.parent / "问题二",
    VALIDATION_DIR.parent / "问题三",
    VALIDATION_DIR.parent / "问题四",
):
    value = str(directory)
    if value not in sys.path:
        sys.path.insert(0, value)

validation_value = str(VALIDATION_DIR)
if validation_value in sys.path:
    sys.path.remove(validation_value)
sys.path.insert(0, validation_value)
