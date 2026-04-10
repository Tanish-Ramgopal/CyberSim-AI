from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from cybersim.environment.core import SimulationEnvironment
from cybersim.models import Action
from cybersim.tasks.registry import available_tasks, load_task

app = FastAPI(title="CyberSim AI API", version="0.2.0")

_CURRENT_ENV: Optional[SimulationEnvironment] = None
_CURRENT_TASK: Optional[str] = None
_CURRENT_SEED: int = 42


class ResetRequest(BaseModel):
    task: str = Field(default="brute_force")
    seed: int = Field(default=42)


class StepRequest(BaseModel):
    action_type: str
    target: str = "none"
    metadata: dict[str, Any] = Field(default_factory=dict)


def _browser_prefers_html(request: Request) -> bool:
    """Embedded browsers (e.g. Cursor) often send Accept: */* without text/html; real browsers include Mozilla/Chrome in UA."""
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" in accept:
        return True
    if "application/json" in accept and "text/html" not in accept:
        return False
    ua = (request.headers.get("user-agent") or "").lower()
    if any(t in ua for t in ("curl", "python", "httpx", "wget", "go-http", "java/", "powershell")):
        return False
    return any(t in ua for t in ("mozilla", "chrome", "edg/", "safari", "applewebkit"))


def _root_landing_html(
    *,
    title: str,
    version: str,
    status: str,
    health: str,
    tasks_path: str,
    flow: list[str],
) -> str:
    """Self-contained demo landing page (no external assets); API remains the real product."""
    flow_rows = "".join(
        f"""
        <li class="flow-step">
          <span class="flow-idx">{i}</span>
          <code class="flow-endpoint">{h}</code>
        </li>"""
        for i, h in enumerate(flow, start=1)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{title}</title>
  <style>
    :root {{
      --bg0: #0b0e14;
      --bg1: #12161f;
      --card: #161c28;
      --border: rgba(255,255,255,.08);
      --text: #e8ecf4;
      --muted: #8b95a8;
      --accent: #5b8cff;
      --accent2: #2dd4bf;
      --radius: 14px;
      --font: ui-sans-serif, system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font);
      color: var(--text);
      background:
        radial-gradient(1200px 600px at 80% -10%, rgba(91,140,255,.18), transparent 55%),
        radial-gradient(800px 400px at 10% 100%, rgba(45,212,191,.12), transparent 50%),
        var(--bg0);
    }}
    .wrap {{
      max-width: 920px;
      margin: 0 auto;
      padding: 3rem 1.25rem 4rem;
    }}
    .hero {{
      padding: 2rem 1.75rem;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      background: linear-gradient(145deg, var(--bg1), var(--card));
      box-shadow: 0 24px 80px rgba(0,0,0,.45);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: .5rem;
      font-size: .75rem;
      letter-spacing: .06em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 1rem;
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent2);
      box-shadow: 0 0 12px var(--accent2);
    }}
    h1 {{
      margin: 0 0 .5rem;
      font-size: clamp(1.75rem, 4vw, 2.25rem);
      font-weight: 700;
      letter-spacing: -.02em;
    }}
    .sub {{
      margin: 0 0 1.5rem;
      font-size: 1.05rem;
      line-height: 1.55;
      color: var(--muted);
      max-width: 52ch;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: .5rem;
      padding: .35rem .75rem;
      border-radius: 999px;
      font-size: .85rem;
      font-weight: 600;
      border: 1px solid var(--border);
      background: rgba(45,212,191,.08);
      color: var(--accent2);
    }}
    .grid {{
      display: grid;
      gap: 1rem;
      margin-top: 1.75rem;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .card {{
      padding: 1.1rem 1.25rem;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(18,22,31,.65);
    }}
    .card h2 {{
      margin: 0 0 .75rem;
      font-size: .8rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--muted);
      font-weight: 600;
    }}
    .links {{
      display: flex;
      flex-direction: column;
      gap: .5rem;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 500;
    }}
    a:hover {{ text-decoration: underline; }}
    .links code {{
      font-size: .85rem;
      color: var(--text);
    }}
    ol.flow {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: .6rem;
    }}
    .flow-step {{
      display: flex;
      align-items: center;
      gap: .75rem;
      padding: .55rem .65rem;
      border-radius: 8px;
      background: rgba(0,0,0,.25);
      border: 1px solid var(--border);
    }}
    .flow-idx {{
      flex-shrink: 0;
      width: 1.5rem;
      height: 1.5rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      font-size: .75rem;
      font-weight: 700;
      background: rgba(91,140,255,.2);
      color: var(--accent);
    }}
    .flow-endpoint {{
      font-size: .88rem;
    }}
    .foot {{
      margin-top: 2rem;
      font-size: .8rem;
      color: var(--muted);
      line-height: 1.6;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="badge"><span class="dot"></span> OpenEnv-style HTTP API</div>
      <h1>{title}</h1>
      <p class="sub">
        Cyber defense simulation environment for agents: reset, step with actions, read state, grade outcomes.
        The API is the product; this page is for humans checking the deployment.
      </p>
      <span class="status">● {status}</span>

      <div class="grid">
        <div class="card">
          <h2>Explore</h2>
          <div class="links">
            <a href="{health}"><code>GET {health}</code> — liveness</a>
            <a href="{tasks_path}"><code>GET {tasks_path}</code> — task ids</a>
            <a href="/docs"><code>GET /docs</code> — interactive Swagger</a>
            <a href="/redoc"><code>GET /redoc</code> — ReDoc</a>
          </div>
        </div>
        <div class="card">
          <h2>Agent loop</h2>
          <ol class="flow">{flow_rows}</ol>
        </div>
      </div>

      <p class="foot">
        Version <strong>{version}</strong> · JSON for programmatic clients is unchanged at <code>GET /</code>
        when using curl, Python, or <code>Accept: application/json</code>.
      </p>
    </div>
  </div>
</body>
</html>"""


@app.get("/", response_model=None)
def root(request: Request) -> Dict[str, Any] | HTMLResponse:
    """JSON for API clients; HTML for browsers (including Cursor) to avoid raw JSON + Pretty-print UI."""
    payload = {
        "name": "CyberSim AI API",
        "status": "running",
        "health": "/health",
        "tasks": "/tasks",
        "flow": ["POST /reset", "POST /step", "GET /state", "POST /close"],
    }
    if _browser_prefers_html(request):
        body = _root_landing_html(
            title=payload["name"],
            version=app.version,
            status=payload["status"],
            health=payload["health"],
            tasks_path=payload["tasks"],
            flow=payload["flow"],
        )
        return HTMLResponse(content=body)
    return payload


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def tasks() -> Dict[str, list[str]]:
    return {"tasks": available_tasks()}


@app.post("/reset")
def reset(body: ResetRequest) -> Dict[str, Any]:
    global _CURRENT_ENV, _CURRENT_TASK, _CURRENT_SEED

    if body.task not in available_tasks():
        raise HTTPException(status_code=400, detail=f"Unknown task '{body.task}'")

    task_cfg = load_task(body.task)
    _CURRENT_ENV = SimulationEnvironment(task_cfg, seed=body.seed)
    _CURRENT_TASK = body.task
    _CURRENT_SEED = body.seed
    obs = _CURRENT_ENV.reset()
    return {"task": _CURRENT_TASK, "seed": _CURRENT_SEED, "observation": obs.model_dump(), "done": False}


@app.post("/step")
def step(body: StepRequest) -> Dict[str, Any]:
    if _CURRENT_ENV is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    action = Action(action_type=body.action_type, target=body.target, metadata=body.metadata)
    obs, reward, done, info = _CURRENT_ENV.step(action)
    return {
        "task": _CURRENT_TASK,
        "seed": _CURRENT_SEED,
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state() -> Dict[str, Any]:
    if _CURRENT_ENV is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return {"task": _CURRENT_TASK, "seed": _CURRENT_SEED, "state": _CURRENT_ENV.state()}


@app.post("/close")
def close() -> Dict[str, bool]:
    global _CURRENT_ENV, _CURRENT_TASK
    if _CURRENT_ENV is not None:
        _CURRENT_ENV.close()
    _CURRENT_ENV = None
    _CURRENT_TASK = None
    return {"closed": True}

