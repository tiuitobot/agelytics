"""FastAPI server for the scouting overlay."""

from pathlib import Path
import time
from pydantic import BaseModel
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .scouting import scout_player
from .civ_kb import get_matchup, get_civ_info, list_civs

# Current match context (set by game_watcher)
_match_context: Optional[dict] = None

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Agelytics Scouting Overlay", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.1.0"}


@app.get("/api/scout/{player_name}")
def api_scout(player_name: str):
    """Full scouting report for a player."""
    report = scout_player(player_name)
    if not report.get("available", False) and "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@app.get("/api/matchup/{civ1}/{civ2}")
def api_matchup(civ1: str, civ2: str):
    """Matchup data between two civs."""
    return get_matchup(civ1, civ2)


@app.get("/api/civ/{civ_name}")
def api_civ(civ_name: str):
    """Get civ info."""
    name = civ_name.strip().title()
    info = get_civ_info(name)
    if not info:
        return {"civ": name, "pros": [], "cons": [], "unique_units": [], "bonuses": "No detailed data yet."}
    return {"civ": name, **info}


@app.get("/api/civs")
def api_civs():
    """List all civs in knowledge base."""
    return {"civs": list_civs()}


class MatchContext(BaseModel):
    opponent_name: str
    opponent_civ: str
    self_civ: str
    opponent_rating: int | None = None
    opponent_profile_id: int | None = None
    opponent_country: str | None = None
    map: str | None = None
    match_id: int | None = None
    updated_at: float | None = None


@app.post("/api/match-context")
def set_match_context(ctx: MatchContext):
    """Set current match context (called by game_watcher)."""
    global _match_context
    payload = ctx.model_dump()
    payload["active"] = True
    payload["updated_at"] = payload.get("updated_at") or time.time()
    _match_context = payload
    return {"status": "ok", "context": _match_context}


@app.get("/api/match-context")
def get_match_context():
    """Get current match context."""
    return _match_context or {"active": False, "updated_at": None}


@app.get("/overlay")
def overlay():
    """Serve the overlay HTML page."""
    html_path = STATIC_DIR / "overlay.html"
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="Overlay HTML not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# Mount static files last
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5555)


if __name__ == "__main__":
    main()
