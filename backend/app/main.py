"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Odin Task Review API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe, used to confirm the dev server is wired up correctly."""
    return {"status": "ok"}
