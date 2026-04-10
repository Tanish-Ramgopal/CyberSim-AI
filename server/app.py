"""OpenEnv multi-mode entry: callable main() + __main__ guard (required by openenv validate)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _load_root_app():
    """Load repo-root app.py without shadowing this module (also named app.py)."""
    path = _ROOT / "app.py"
    spec = importlib.util.spec_from_file_location("cybersim_root_app", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load API module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


app = _load_root_app()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
