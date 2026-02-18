from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to send to Gemini")
    model: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    gemini_api_key: str | None = Field(default=None, description="Optional per-request Gemini API key override")


class ChatResponse(BaseModel):
    response: str
