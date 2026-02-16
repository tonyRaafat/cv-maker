from fastapi import APIRouter, HTTPException
from api.cv.schemas import CvGenerateDataRequest, CvRenderRequest, CvGenerateDataResponse
from .service import generate_cv_data, render_cv

router = APIRouter(prefix="/api/cv")


@router.post("/generate-data", response_model=CvGenerateDataResponse)
def generate_data_route(request: CvGenerateDataRequest):
    try:
        return generate_cv_data(request)
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
