from fastapi.responses import Response
from typing import Any

from api.job.schemas import JobExtractRequest, JobPdfRequest, JobDescriptionPdfRequest
from job_extractor import (
    extract_company_name,
    extract_job_description,
    extract_job_title,
    fetch_job_data_with_apify,
)
from resume_pdf_service import create_docx_from_template, create_pdf_from_template, build_resume_sections
from profile_store import get_profile
from utils import render_cv_response
from api.job.schemas import JobExtractRequest as _JobExtractRequest


def extract_job_data(request: JobExtractRequest) -> dict[str, Any]:
    return fetch_job_data_with_apify(str(request.url))


def generate_job_pdf(request: JobPdfRequest) -> Response:
    profile = get_profile()
    if not profile:
        raise ValueError("Profile not found. Please create your profile first using /api/profile.")

    job_data = fetch_job_data_with_apify(str(request.url))
    description = extract_job_description(job_data)
    if not description:
        raise ValueError("Could not extract job description from Apify response.")

    sections = build_resume_sections(
        description,
        model_name=request.model,
        profile_data=profile,
        prompt_override=request.prompt,
        gemini_api_key=request.gemini_api_key,
    )
    role_title = extract_job_title(job_data) or profile.get("title")
    company_name = extract_company_name(job_data) or ""
    full_name = profile.get("full_name") or request.full_name

    return render_cv_response(
        full_name=full_name,
        role_title=role_title,
        company_name=company_name,
        source=str(request.url),
        sections=sections,
        output_format=request.format,
    )


def generate_job_pdf_from_description(request: JobDescriptionPdfRequest) -> Response:
    profile = get_profile()
    if not profile:
        raise ValueError("Profile not found. Please create your profile first using /api/profile.")

    description = request.job_description.strip()
    sections = build_resume_sections(
        description,
        model_name=request.model,
        profile_data=profile,
        prompt_override=request.prompt,
        gemini_api_key=request.gemini_api_key,
    )

    role_title = (request.job_role or "").strip() or profile.get("title") or "Target Role"
    company_name = (request.company_name or "").strip() or ""
    full_name = profile.get("full_name") or request.full_name

    return render_cv_response(
        full_name=full_name,
        role_title=role_title,
        company_name=company_name,
        source="manual-job-description",
        sections=sections,
        output_format=request.format,
    )
