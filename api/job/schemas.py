from pydantic import BaseModel, Field, HttpUrl


class JobExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="LinkedIn job URL containing currentJobId query parameter")


class JobPdfRequest(BaseModel):
    url: HttpUrl = Field(..., description="LinkedIn job URL containing currentJobId query parameter")
    full_name: str = Field(default="Your Name", description="Name shown in the generated PDF")
    model: str = Field(default="gemini-3-flash-preview", description="Gemini model name")
    format: str = Field(default="pdf", description="Output format: 'pdf' or 'docx'")
    prompt: str | None = Field(default=None, description="Optional custom prompt to send to the AI (overrides built-in prompt)")


class JobDescriptionPdfRequest(BaseModel):
    job_description: str = Field(..., min_length=20, description="Raw job description text")
    company_name: str | None = Field(default=None, description="Optional company name")
    job_role: str | None = Field(default=None, description="Optional role title")
    full_name: str = Field(default="Your Name", description="Name shown in the generated PDF")
    model: str = Field(default="gemini-3-flash-preview", description="Gemini model name")
    format: str = Field(default="pdf", description="Output format: 'pdf' or 'docx'")
    prompt: str | None = Field(default=None, description="Optional custom prompt to send to the AI (overrides built-in prompt)")
