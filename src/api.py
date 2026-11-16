"""Web API for Tanya CS.  Run from the TanyaCS folder:  uvicorn src.api:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.answer import ask, _load

log = logging.getLogger("tanya")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load()  # load the embedding model and database once at startup, not on the first request
    yield


app = FastAPI(title="Tanya CS - BorneoNet", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    handoff: bool
    best_distance: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Pertanyaan tidak boleh kosong.")
    try:
        return ask(question)
    except Exception:
        log.exception("ask() failed")
        raise HTTPException(status_code=503, detail="Layanan sedang sibuk, coba lagi sebentar ya.")