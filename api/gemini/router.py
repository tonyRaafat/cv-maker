from fastapi import APIRouter, Header, HTTPException
from api.gemini.schemas import ChatRequest, ChatResponse
from .service import gemini_chat as gemini_chat_service

router = APIRouter(prefix="/api/gemini")


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
) -> ChatResponse:
    try:
        effective_key = x_gemini_api_key or request.gemini_api_key
        return gemini_chat_service(request, gemini_api_key=effective_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}") from exc
