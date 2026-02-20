import logging
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.gemini import router as gemini_router
from api.job import router as job_router
from api.cv import router as cv_router
from api.profile import router as profile_router
from api.health import router as health_router
from api.security import verify_api_access


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="CV Maker API",
    version="1.0.0",
    dependencies=[Depends(verify_api_access)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],              # keep empty when using regex
    allow_origin_regex=".*",       # matches any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(gemini_router)
app.include_router(job_router)
app.include_router(cv_router)
app.include_router(profile_router)
