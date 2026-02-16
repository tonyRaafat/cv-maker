from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to send to Gemini")
    model: str = Field(default="gemini-2.0-flash", description="Gemini model name")


class ChatResponse(BaseModel):
    response: str
