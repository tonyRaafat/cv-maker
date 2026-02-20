from fastapi import APIRouter, Header, HTTPException
from api.cv.schemas import CvGenerateDataRequest, CvRenderRequest, CvGenerateDataResponse, CoverLetterRenderRequest
from .service import generate_cv_data, render_cv, render_cover_letter

router = APIRouter(prefix="/api/cv")


@router.post("/generate-data", response_model=CvGenerateDataResponse)
def generate_data_route(
    request: CvGenerateDataRequest,
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
):
    try:
        effective_key = x_gemini_api_key or request.gemini_api_key
        request_with_key = request.model_copy(update={"gemini_api_key": effective_key})
        return generate_cv_data(request_with_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate CV data: {exc}") from exc


@router.post("/render")
def render_route(request: CvRenderRequest):
    try:
        return render_cv(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to render CV: {exc}") from exc


@router.post("/render-cover-letter")
def render_cover_letter_route(request: CoverLetterRenderRequest):
    try:
        return render_cover_letter(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to render cover letter: {exc}") from exc
