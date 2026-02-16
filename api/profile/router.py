from fastapi import APIRouter, HTTPException
from api.profile.schemas import (
    UserProfileCreateRequest,
    UserProfileCreateResponse,
    UserProfileUpdateResponse,
)
from .service import create_user_profile, get_user_profile, edit_user_profile

router = APIRouter(prefix="/api/profile")


@router.post("", response_model=UserProfileCreateResponse)
def create_profile_route(request: UserProfileCreateRequest):
    try:
        profile_id = create_user_profile(request)
        return UserProfileCreateResponse(id=profile_id, message="Profile saved successfully")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {exc}") from exc


@router.get("")
def get_profile_route():
    try:
        profile = get_user_profile()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {exc}") from exc


@router.put("", response_model=UserProfileUpdateResponse)
def update_profile_route(request: UserProfileCreateRequest):
    try:
        is_updated = edit_user_profile(request)
        if not is_updated:
            raise HTTPException(status_code=500, detail="Profile could not be updated")
        profile = get_user_profile()
        if not profile:
            raise HTTPException(status_code=500, detail="Profile could not be loaded after update")
        return UserProfileUpdateResponse(id=profile["id"], message="Profile updated successfully")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {exc}") from exc
