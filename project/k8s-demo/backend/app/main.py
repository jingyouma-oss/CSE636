"""FastAPI backend for the k8s-demo three-tier app."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import db

app = FastAPI(title="k8s-demo backend")


class ItemIn(BaseModel):
    name: str


@app.get("/api/health")
def health():
    """Liveness: process is up. Deliberately does NOT touch the DB."""
    return {"status": "ok"}


@app.get("/api/ready")
def ready():
    """Readiness: only ready once Postgres is reachable (gates traffic)."""
    try:
        db.ping()
    except Exception as exc:  # noqa: BLE001 - surface any driver/connection error
        raise HTTPException(status_code=503, detail=f"db unavailable: {exc}")
    return {"status": "ready", "db": "reachable"}


@app.get("/api/items")
def get_items():
    return {"items": db.list_items()}


@app.post("/api/items", status_code=201)
def create_item(item: ItemIn):
    name = item.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name must not be empty")
    return db.add_item(name)
