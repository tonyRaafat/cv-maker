from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.gemini import router as gemini_router
from api.job import router as job_router
from api.cv import router as cv_router
from api.profile import router as profile_router
from api.health import router as health_router


app = FastAPI(title="CV Maker API", version="1.0.0")

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
