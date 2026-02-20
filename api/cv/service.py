import json
import logging
from fastapi.responses import Response

from api.cv.schemas import (
    CvGenerateDataRequest,
    CvGenerateDataResponse,
    CvRenderRequest,
    EmailMessageResponse,
    CoverLetterRenderRequest,
)
from job_extractor import (
    extract_company_name,
    extract_job_description,
    extract_job_title,
    fetch_job_data_with_apify,
)
from resume_pdf_service import build_resume_sections, build_resume_bundle
from profile_store import get_profile
from utils import render_cv_response, render_cover_letter_response, _clean_optional_text

logger = logging.getLogger(__name__)


def _default_cover_letter_prompt(*, full_name: str, role_title: str, company_name: str, job_description: str, sections: dict) -> str:
    return (
        "Write a professional, ATS-friendly cover letter in plain text.\n"
        f"Candidate Name: {full_name}\n"
        f"Target Role: {role_title}\n"
        f"Company: {company_name}\n"
        "Tone: confident, concise, tailored, human.\n"
        "Length: 3-5 short paragraphs.\n"
        "Include measurable impact where possible, and close with a call to action.\n"
        "Do not include placeholders.\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Candidate CV Data (JSON):\n{json.dumps(sections, ensure_ascii=False)}"
    )


def _default_email_message_prompt(*, full_name: str, role_title: str, company_name: str, job_description: str, sections: dict) -> str:
    return (
        "Write a short, professional job application email.\n"
        f"Candidate Name: {full_name}\n"
        f"Target Role: {role_title}\n"
        f"Company: {company_name}\n"
        "Length: 5-8 lines max.\n"
        "Must include: subject, greeting, 1-2 key strengths, and polite closing.\n"
        "Return ONLY valid JSON in this exact shape:\n"
        '{"subject":"Application for <Target Role>","body":"<email body>"}\n'
        "Do not include placeholders.\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Candidate CV Data (JSON):\n{json.dumps(sections, ensure_ascii=False)}"
    )


def _normalize_email_message(raw_email: object, *, role_title: str) -> EmailMessageResponse:
    if isinstance(raw_email, dict):
        subject = str(raw_email.get("subject") or "").strip()
        body = str(raw_email.get("body") or "").strip()
        return EmailMessageResponse(subject=subject or f"Application for {role_title}", body=body)

    text = str(raw_email or "").strip()
    if not text:
        return EmailMessageResponse(subject=f"Application for {role_title}", body="")

    candidate = text
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()

    try:
        payload = json.loads(candidate)
        if isinstance(payload, dict):
            subject = str(payload.get("subject") or "").strip()
            body = str(payload.get("body") or "").strip()
            if subject or body:
                return EmailMessageResponse(
                    subject=subject or f"Application for {role_title}",
                    body=body,
                )
    except Exception:
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    subject = ""
    body_lines = lines

    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body_lines = lines[1:]
    elif lines:
        first_line = lines[0]
        if len(first_line) <= 120 and not first_line.lower().startswith(("dear ", "hi ", "hello ")):
            subject = first_line
            body_lines = lines[1:]

    body = "\n".join(body_lines).strip() if body_lines else text

    return EmailMessageResponse(
        subject=subject or f"Application for {role_title}",
        body=body,
    )


def generate_cv_data(request: CvGenerateDataRequest) -> CvGenerateDataResponse:
    profile = get_profile()
    if not profile:
        raise ValueError("Profile not found. Please create your profile first using /api/profile.")

    logger.info("generate_cv_data called model=%s generate_cv=%s generate_cover_letter=%s generate_email_message=%s url_provided=%s", request.model, request.generate_cv, request.generate_cover_letter, request.generate_email_message, bool(request.url))

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
    sections = {}
    cover_letter = None
    email_message = None

    if request.generate_cover_letter or request.generate_email_message:
        bundle = build_resume_bundle(
            description,
            model_name=request.model,
            profile_data=profile,
            generate_cv=request.generate_cv,
            generate_cover_letter=request.generate_cover_letter,
            generate_email_message=request.generate_email_message,
            full_name=resolved_full_name,
            role_title=resolved_role,
            company_name=resolved_company,
            prompt_override=request.prompt,
            cover_letter_prompt=request.cover_letter_prompt,
            email_message_prompt=request.email_message_prompt,
            gemini_api_key=request.gemini_api_key,
        )
        logger.info("Received bundle: sections_present=%s cover_letter_present=%s email_message_present=%s", bool(bundle.get("sections")), bool(bundle.get("cover_letter")), bool(bundle.get("email_message")))
        sections = bundle.get("sections") or {}
        cover_letter = bundle.get("cover_letter")
        if request.generate_email_message:
            email_message = _normalize_email_message(bundle.get("email_message"), role_title=resolved_role)
    elif request.generate_cv:
        sections = build_resume_sections(
            description,
            model_name=request.model,
            profile_data=profile,
            prompt_override=request.prompt,
            gemini_api_key=request.gemini_api_key,
        )
        logger.info("Generated sections keys=%s", list(sections.keys()))

    return CvGenerateDataResponse(
        full_name=resolved_full_name,
        company_name=resolved_company,
        role_title=resolved_role,
        source=source,
        sections=sections,
        cover_letter=cover_letter,
        email_message=email_message,
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


def render_cover_letter(request: CoverLetterRenderRequest) -> Response:
    return render_cover_letter_response(
        full_name=request.full_name,
        role_title=request.role_title,
        company_name=request.company_name,
        source=request.source,
        cover_letter=request.cover_letter,
        output_format=request.format,
    )
