from api.gemini.schemas import ChatRequest, ChatResponse
from gemini_chat import ask_gemini


def gemini_chat(request: ChatRequest, gemini_api_key: str | None = None) -> ChatResponse:
    text = ask_gemini(request.prompt, model_name=request.model, api_key=gemini_api_key)
    return ChatResponse(response=text)
