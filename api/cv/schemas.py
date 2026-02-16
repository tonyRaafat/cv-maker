from pydantic import BaseModel, Field, HttpUrl
from typing import Any


class CvGenerateDataRequest(BaseModel):
    url: HttpUrl | None = Field(default=None, description="Optional LinkedIn job URL")
    job_description: str | None = Field(default=None, description="Optional raw job description")
    company_name: str | None = Field(default=None, description="Optional company name override")
    job_role: str | None = Field(default=None, description="Optional role title override")
    full_name: str = Field(default="Your Name", description="Name shown in generated CV")
    model: str = Field(default="gemini-3-flash-preview", description="Gemini model name")
    prompt: str | None = Field(default=None, description="Optional custom prompt to send to the AI (overrides built-in prompt)")


class CvGenerateDataResponse(BaseModel):
    full_name: str
    company_name: str
    role_title: str
    source: str
    sections: dict[str, Any]


class CvRenderRequest(BaseModel):
    full_name: str
    company_name: str
    role_title: str
    source: str = Field(default="manual-job-description")
    format: str = Field(default="pdf", description="Output format: 'pdf' or 'docx'")
    sections: dict[str, Any]
