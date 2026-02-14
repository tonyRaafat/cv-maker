import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient


_client: MongoClient | None = None
PROFILE_KEY = "my_profile"


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        _client = MongoClient(mongo_uri)
    return _client


def _get_collection():
    load_dotenv()
    db_name = os.getenv("MONGODB_DB", "my_info")
    collection_name = os.getenv("MONGODB_COLLECTION", "profiles")
    return _get_client()[db_name][collection_name]


def create_profile(profile_data: dict) -> str:
    payload = dict(profile_data)
    payload["profile_key"] = PROFILE_KEY
    payload["created_at"] = datetime.now(timezone.utc)
    payload["updated_at"] = datetime.now(timezone.utc)

    result = _get_collection().find_one_and_update(
        {"profile_key": PROFILE_KEY},
        {
            "$set": payload,
            "$setOnInsert": {"created_at": payload["created_at"]},
        },
        upsert=True,
        return_document=True,
    )
    if result and "_id" in result:
        return str(result["_id"])

    inserted = _get_collection().find_one({"profile_key": PROFILE_KEY})
    return str(inserted["_id"]) if inserted and "_id" in inserted else ""


def get_profile() -> dict | None:
    doc = _get_collection().find_one({"profile_key": PROFILE_KEY})
    if not doc:
        return None

    doc["id"] = str(doc.pop("_id"))
    doc.pop("profile_key", None)
    if "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc


def update_profile(profile_data: dict) -> bool:
    payload = dict(profile_data)
    payload["profile_key"] = PROFILE_KEY
    payload["updated_at"] = datetime.now(timezone.utc)

    result = _get_collection().update_one(
        {"profile_key": PROFILE_KEY},
        {"$set": payload},
        upsert=True,
    )
    return result.matched_count > 0 or result.upserted_id is not None
