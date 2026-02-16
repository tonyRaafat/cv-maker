from fastapi import APIRouter, HTTPException
from api.job.schemas import JobExtractRequest, JobPdfRequest, JobDescriptionPdfRequest
from .service import extract_job_data, generate_job_pdf, generate_job_pdf_from_description

router = APIRouter(prefix="/api/job")


@router.post("/extract")
def extract_route(request: JobExtractRequest):
    try:
        return extract_job_data(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Job extraction failed: {exc}") from exc


@router.post("/generate-pdf")
def generate_pdf_route(request: JobPdfRequest):
    try:
        return generate_job_pdf(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc


@router.post("/generate-pdf-from-description")
def generate_pdf_from_description_route(request: JobDescriptionPdfRequest):
    try:
        return generate_job_pdf_from_description(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
