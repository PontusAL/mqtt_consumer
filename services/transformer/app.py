from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Transformer Service")


class TransformRequest(BaseModel):
    payload: Any


class TransformResponse(BaseModel):
    payload: Any


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transform", response_model=TransformResponse)
async def transform(request: TransformRequest) -> TransformResponse:
    # Placeholder transformation hook; prefixes payload to simulate processing.
    message = f"PROCESSED: {request.payload}"
    return TransformResponse(payload=message)
