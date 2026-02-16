from api.gemini.schemas import ChatRequest, ChatResponse
from gemini_chat import ask_gemini


def gemini_chat(request: ChatRequest) -> ChatResponse:
    text = ask_gemini(request.prompt, model_name=request.model)
    return ChatResponse(response=text)
