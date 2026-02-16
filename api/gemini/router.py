from fastapi import APIRouter, HTTPException
from api.gemini.schemas import ChatRequest, ChatResponse
from .service import gemini_chat as gemini_chat_service

router = APIRouter(prefix="/api/gemini")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return gemini_chat_service(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}") from exc
