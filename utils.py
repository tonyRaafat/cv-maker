import re
from typing import Any
from fastapi.responses import Response

from resume_pdf_service import create_docx_from_template, create_pdf_from_template


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


def render_cv_response(
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
