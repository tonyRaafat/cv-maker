import hmac
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader


load_dotenv()

API_KEY = os.getenv("API_KEY", "")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
ALLOWED_IPS = {
    ip.strip()
    for ip in os.getenv("ALLOWED_IPS", "").split(",")
    if ip.strip()
}

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def verify_api_access(
    request: Request,
    provided_key: str | None = Security(api_key_header),
) -> None:
    path = request.url.path
    if path in PUBLIC_PATHS:
        return

    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API security is not configured. Set API_KEY environment variable.",
        )

    client_ip = request.client.host if request.client else None
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address.",
        )

    if not provided_key or not hmac.compare_digest(provided_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
