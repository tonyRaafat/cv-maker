from typing import Any
from fastapi.responses import Response

from api.cv.schemas import CvGenerateDataRequest, CvGenerateDataResponse, CvRenderRequest
from job_extractor import (
    extract_company_name,
    extract_job_description,
    extract_job_title,
    fetch_job_data_with_apify,
)
from resume_pdf_service import build_resume_sections
from profile_store import get_profile
from utils import render_cv_response, _clean_optional_text


def generate_cv_data(request: CvGenerateDataRequest) -> CvGenerateDataResponse:
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
    sections = build_resume_sections(
        description, model_name=request.model, profile_data=profile, prompt_override=request.prompt
    )

    return CvGenerateDataResponse(
        full_name=resolved_full_name,
        company_name=resolved_company,
        role_title=resolved_role,
        source=source,
        sections=sections,
    )


def render_cv(request: CvRenderRequest) -> Response:
    return render_cv_response(
        full_name=request.full_name,
        role_title=request.role_title,
        company_name=request.company_name,
        source=request.source,
        sections=request.sections,
        output_format=request.format,
    )
