import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.langflow_client import LangFlowClient

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, settings: Settings = Depends(get_settings)):
    client = LangFlowClient(settings)
    session = body.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    reply = await client.send_message(body.message, session)
    return ChatResponse(reply=reply, session_id=session)
