"""OpenEnv multi-mode entry: callable main() + __main__ guard (required by openenv validate)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

# Repo-root FastAPI app (app.py). Normal import avoids importlib + Pydantic OpenAPI bugs.
from app import app  # noqa: E402

__all__ = ["app", "main"]


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
