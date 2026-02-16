from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import re
from typing import Any

from gemini_chat import ask_gemini
from job_extractor import (
    extract_company_name,
    extract_job_description,
    extract_job_title,
    fetch_job_data_with_apify,
)
from resume_pdf_service import build_resume_sections, create_pdf_from_template, create_docx_from_template
from profile_store import create_profile, get_profile, update_profile


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to send to Gemini")
    model: str = Field(default="gemini-2.0-flash", description="Gemini model name")


class ChatResponse(BaseModel):
    response: str


class JobExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="LinkedIn job URL containing currentJobId query parameter")


class JobPdfRequest(BaseModel):
    url: HttpUrl = Field(..., description="LinkedIn job URL containing currentJobId query parameter")
    full_name: str = Field(default="Your Name", description="Name shown in the generated PDF")
    model: str = Field(default="gemini-2.5-flash-lite", description="Gemini model name")
    format: str = Field(default="pdf", description="Output format: 'pdf' or 'docx'")


class JobDescriptionPdfRequest(BaseModel):
    job_description: str = Field(..., min_length=20, description="Raw job description text")
    company_name: str | None = Field(default=None, description="Optional company name")
    job_role: str | None = Field(default=None, description="Optional role title")
    full_name: str = Field(default="Your Name", description="Name shown in the generated PDF")
    model: str = Field(default="gemini-2.5-flash-lite", description="Gemini model name")
    format: str = Field(default="pdf", description="Output format: 'pdf' or 'docx'")


class CvGenerateDataRequest(BaseModel):
    url: HttpUrl | None = Field(default=None, description="Optional LinkedIn job URL")
    job_description: str | None = Field(default=None, description="Optional raw job description")
    company_name: str | None = Field(default=None, description="Optional company name override")
    job_role: str | None = Field(default=None, description="Optional role title override")
    full_name: str = Field(default="Your Name", description="Name shown in generated CV")
    model: str = Field(default="gemini-2.5-flash-lite", description="Gemini model name")


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


class ProfileLinks(BaseModel):
    github: str
    linkedin: str


class ProfileCoreSkills(BaseModel):
    languages_and_frameworks: list[str] = Field(default_factory=list)
    databases_and_tools: list[str] = Field(default_factory=list)
    testing_and_devops: list[str] = Field(default_factory=list)
    development_practices: list[str] = Field(default_factory=list)


class ProfileExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    description: str


class ProfileEducation(BaseModel):
    degree: str
    institution: str
    location: str
    graduation_date: str


class ProfileTrainingCertification(BaseModel):
    name: str
    provider: str
    duration: str


class UserProfileCreateRequest(BaseModel):
    full_name: str
    title: str
    location: str
    phone: str
    email: str
    links: ProfileLinks
    professional_summary: str
    core_skills: ProfileCoreSkills
    professional_experience: list[ProfileExperienceItem] = Field(default_factory=list)
    education: ProfileEducation
    training_and_certifications: list[ProfileTrainingCertification] = Field(default_factory=list)


class UserProfileCreateResponse(BaseModel):
    id: str
    message: str


class UserProfileUpdateResponse(BaseModel):
    id: str
    message: str


app = FastAPI(title="Gemini API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],              # keep empty when using regex
    allow_origin_regex=".*",       # matches any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _sanitize_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "cv"


def _clean_optional_text(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = value.strip()
    if cleaned.lower() in {"", "string", "none", "null", "n/a", "na"}:
        return ""
    return cleaned


def _render_cv_response(
    *,
    full_name: str,
    role_title: str,
    company_name: str,
    source: str,
    sections: dict[str, Any],
    output_format: str,
) -> Response:
    title_like = f"{full_name} cv/resume | {company_name} | {role_title}"

    if output_format.lower() == "docx":
        file_name = f"{_sanitize_filename(title_like)}.docx"
        docx_bytes = create_docx_from_template(
            output_path=None,
            full_name=full_name,
            role_title=role_title,
            company_name=company_name,
            job_url=source,
            sections=sections,
        )
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )

    file_name = f"{_sanitize_filename(title_like)}.pdf"
    pdf_bytes = create_pdf_from_template(
        output_path=None,
        full_name=full_name,
        role_title=role_title,
        company_name=company_name,
        job_url=source,
        sections=sections,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/gemini/chat", response_model=ChatResponse)
def gemini_chat(request: ChatRequest) -> ChatResponse:
    try:
        text = ask_gemini(request.prompt, model_name=request.model)
        return ChatResponse(response=text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}") from exc


@app.post("/api/job/extract")
def extract_job_data(request: JobExtractRequest) -> dict:
    try:
        return fetch_job_data_with_apify(str(request.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Job extraction failed: {exc}") from exc


@app.post("/api/job/generate-pdf")
def generate_job_pdf(request: JobPdfRequest) -> Response:
    try:
        profile = get_profile()
        if not profile:
            raise ValueError("Profile not found. Please create your profile first using /api/profile.")

        job_data = fetch_job_data_with_apify(str(request.url))
        description = extract_job_description(job_data)
        if not description:
            raise ValueError("Could not extract job description from Apify response.")

        sections = build_resume_sections(description, model_name=request.model, profile_data=profile)
        role_title = extract_job_title(job_data) or profile.get("title") 
        company_name = extract_company_name(job_data) or ""
        full_name = profile.get("full_name") or request.full_name
        title_like = f"{full_name} cv/resume | {company_name} | {role_title}"

        if request.format.lower() == "docx":
            docx_bytes = create_docx_from_template(
                output_path=None,
                full_name=full_name,
                role_title=role_title,
                company_name=company_name,
                job_url=str(request.url),
                sections=sections,
            )
            file_name = f"{_sanitize_filename(title_like)}.docx"
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
            )

        file_name = f"{_sanitize_filename(title_like)}.pdf"
        pdf_bytes = create_pdf_from_template(
            output_path=None,
            full_name=full_name,
            role_title=role_title,
            company_name=company_name,
            job_url=str(request.url),
            sections=sections,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc


@app.post("/api/job/generate-pdf-from-description")
def generate_job_pdf_from_description(request: JobDescriptionPdfRequest) -> Response:
    try:
        profile = get_profile()
        if not profile:
            raise ValueError("Profile not found. Please create your profile first using /api/profile.")

        description = request.job_description.strip()
        sections = build_resume_sections(description, model_name=request.model, profile_data=profile)

        role_title = (request.job_role or "").strip() or profile.get("title") or "Target Role"
        company_name = (request.company_name or "").strip() or ""
        full_name = profile.get("full_name") or request.full_name

        title_like = f"{full_name} cv/resume | {company_name} | {role_title}"
        if request.format.lower() == "docx":
            file_name = f"{_sanitize_filename(title_like)}.docx"
            docx_bytes = create_docx_from_template(
                output_path=None,
                full_name=full_name,
                role_title=role_title,
                company_name=company_name,
                job_url="manual-job-description",
                sections=sections,
            )
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
            )

        file_name = f"{_sanitize_filename(title_like)}.pdf"
        pdf_bytes = create_pdf_from_template(
            output_path=None,
            full_name=full_name,
            role_title=role_title,
            company_name=company_name,
            job_url="manual-job-description",
            sections=sections,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc


@app.post("/api/cv/generate-data", response_model=CvGenerateDataResponse)
def generate_cv_data(request: CvGenerateDataRequest) -> CvGenerateDataResponse:
    try:
        profile = get_profile()
        if not profile:
            raise ValueError("Profile not found. Please create your profile first using /api/profile.")

        has_url = bool(request.url)
        has_description = bool(request.job_description and request.job_description.strip())
        if not has_url and not has_description:
            raise ValueError("Provide either 'url' or 'job_description'.")

        source = "manual-job-description"
        description = ""
        resolved_role = _clean_optional_text(request.job_role)
        resolved_company = _clean_optional_text(request.company_name)

        if has_url:
            source = str(request.url)
            job_data = fetch_job_data_with_apify(source)
            extracted = extract_job_description(job_data)
            if not extracted:
                raise ValueError("Could not extract job description from Apify response.")
            description = extracted
            if not resolved_role:
                resolved_role = extract_job_title(job_data) or ""
            if not resolved_company:
                resolved_company = extract_company_name(job_data) or ""
        else:
            description = (request.job_description or "").strip()

        if not resolved_role:
            resolved_role = profile.get("title") or "Target Role"
        if not resolved_company:
            resolved_company = "Target Company"

        resolved_full_name = profile.get("full_name") or request.full_name
        sections = build_resume_sections(description, model_name=request.model, profile_data=profile)

        return CvGenerateDataResponse(
            full_name=resolved_full_name,
            company_name=resolved_company,
            role_title=resolved_role,
            source=source,
            sections=sections,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate CV data: {exc}") from exc


@app.post("/api/cv/render")
def render_cv(request: CvRenderRequest) -> Response:
    try:
        return _render_cv_response(
            full_name=request.full_name,
            role_title=request.role_title,
            company_name=request.company_name,
            source=request.source,
            sections=request.sections,
            output_format=request.format,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to render CV: {exc}") from exc


@app.post("/api/profile", response_model=UserProfileCreateResponse)
def create_user_profile(request: UserProfileCreateRequest) -> UserProfileCreateResponse:
    try:
        profile_id = create_profile(request.model_dump())
        return UserProfileCreateResponse(id=profile_id, message="Profile saved successfully")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {exc}") from exc


@app.get("/api/profile")
def get_user_profile() -> dict:
    try:
        profile = get_profile()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {exc}") from exc


@app.put("/api/profile", response_model=UserProfileUpdateResponse)
def edit_user_profile(request: UserProfileCreateRequest) -> UserProfileUpdateResponse:
    try:
        is_updated = update_profile(request.model_dump())
        if not is_updated:
            raise HTTPException(status_code=500, detail="Profile could not be updated")
        profile = get_profile()
        if not profile:
            raise HTTPException(status_code=500, detail="Profile could not be loaded after update")
        return UserProfileUpdateResponse(id=profile["id"], message="Profile updated successfully")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {exc}") from exc
