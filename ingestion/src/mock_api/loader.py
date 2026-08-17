"""
loader.py
=========
Reads JSON fixtures from the repository's /data directory and returns them
parsed but otherwise untouched — no normalisation, no flattening, no models.
The mock's contract is byte-level fidelity to whatever the fixture holds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

# repo_root/src/mock_api/loader.py -> repo_root/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_fixture(filename: str) -> Any:
    """Load /data/<filename> and return the parsed JSON unchanged.

    Raises HTTPException 500 (not 404) for both failure modes: the route ->
    file mapping is hardwired in app.py, so a missing or malformed fixture is
    a server-side problem, and the consumer should see it as one.
    """
    path = DATA_DIR / filename

    if not path.is_file():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Fixture '{filename}' not found in {DATA_DIR}. "
                "Create it (placeholder '{}' is fine) and retry."
            ),
        )

    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Fixture '{filename}' is not valid JSON: {exc.msg} "
                f"(line {exc.lineno}, column {exc.colno})."
            ),
        ) from exc
