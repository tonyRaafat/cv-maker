from api.profile.schemas import UserProfileCreateRequest
from profile_store import create_profile, get_profile, update_profile


def create_user_profile(request: UserProfileCreateRequest) -> str:
    return create_profile(request.model_dump())


def get_user_profile() -> dict:
    return get_profile()


def edit_user_profile(request: UserProfileCreateRequest) -> bool:
    return update_profile(request.model_dump())
