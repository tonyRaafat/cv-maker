import logging
import os
import re
from urllib.parse import parse_qs, urlparse

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


APIFY_ACTOR = "apimaestro~linkedin-job-detail"
APIFY_BASE_URL = "https://api.apify.com/v2"


def _strip_html(value: str) -> str:
	text = re.sub(r"<[^>]+>", " ", value)
	text = re.sub(r"\s+", " ", text).strip()
	return text


def _pick_first_text(item: dict, keys: list[str]) -> str | None:
	for key in keys:
		value = item.get(key)
		if isinstance(value, str) and value.strip():
			return _strip_html(value)
	return None


def _extract_current_job_id(job_url: str) -> str:
	parsed = urlparse(job_url)
	query_params = parse_qs(parsed.query)
	values = query_params.get("currentJobId")
	if not values or not values[0].strip():
		# Also support URLs like: https://www.linkedin.com/jobs/view/{currentJobId}/
		path_match = re.search(r"/jobs/view/(\d+)(?:/|$)", parsed.path)
		if not path_match:
			raise ValueError(
				"The provided URL does not contain a valid job ID. Supported formats are "
				"...?currentJobId=<id> and /jobs/view/<id>/"
			)
		return path_match.group(1)
	return values[0].strip()


def _require_apify_token() -> str:
	load_dotenv()
	token = os.getenv("APIFY_TOKEN")
	if not token:
		raise RuntimeError("Missing APIFY_TOKEN. Add it to your environment or .env file.")
	return token


def fetch_job_data_with_apify(job_url: str, timeout_seconds: float = 60.0) -> dict:
	current_job_id = _extract_current_job_id(job_url)
	token = _require_apify_token()

	# Use the run-sync-get-dataset-items endpoint to run the actor and directly
	# receive the dataset items in the response (as requested by the user).
	run_sync_url = f"{APIFY_BASE_URL}/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"
	payload = {"job_id": [current_job_id]}

	logger.info("Apify request run_sync_url=%s current_job_id=%s", run_sync_url, current_job_id)
	try:
		with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
			resp = client.post(
				run_sync_url,
				params={"token": token},
				json=payload,
				headers={"Content-Type": "application/json"},
			)

			logger.info("Apify HTTP %s returned status=%d", run_sync_url, resp.status_code)

			if resp.status_code >= 400:
				logger.error("Apify error response: %s", resp.text[:1000])
				raise RuntimeError(f"Apify run-sync request failed: HTTP {resp.status_code} - {resp.text[:500]}")

			items = resp.json()
			logger.info("Apify returned items_count=%d", len(items) if isinstance(items, list) else 0)
	except Exception:
		logger.exception("Apify request failed for job_url=%s", job_url)
		raise
		if not isinstance(items, list):
			# Some actors may return an object with `items` key or similar; handle common cases
			if isinstance(items, dict) and "items" in items and isinstance(items["items"], list):
				items = items["items"]
			else:
				raise RuntimeError("Apify run-sync response format is invalid; expected a list of items.")

	first_item = items[0] if items else None

	return {
		"source_url": job_url,
		"currentJobId": current_job_id,
		"itemCount": len(items),
		"job": first_item,
		"items": items,
	}


def extract_job_description(job_data: dict) -> str | None:
	# The actor may return a wrapper { 'job': {...}, 'items': [...] }
	# or return the first item directly. Normalize to candidate objects to inspect.
	candidates: list[dict] = []

	if isinstance(job_data, dict):
		# If top-level has a 'job' field, prefer that
		top_job = job_data.get("job")
		if isinstance(top_job, dict):
			candidates.append(top_job)

		# If top-level itself looks like an item (contains job_info or description), include it
		if any(k in job_data for k in ("job_info", "description", "jobDescription", "descriptionText", "formattedDescription")):
			candidates.append(job_data)

		# Add items list if present
		items = job_data.get("items")
		if isinstance(items, list):
			for it in items:
				if isinstance(it, dict):
					candidates.append(it)
	else:
		return None

	# Inspect candidates for description
	for job in candidates:
		# Direct fields inside the job item
		text = _pick_first_text(job, ["description", "jobDescription", "job_description", "descriptionText", "formattedDescription", "details"])
		if text:
			return text

		# Nested job_info block used by the actor
		job_info = job.get("job_info")
		if isinstance(job_info, dict):
			text = _pick_first_text(job_info, ["description", "jobDescription", "descriptionText", "formattedDescription"]) 
			if text:
				return text

	return None


def extract_job_title(job_data: dict) -> str | None:
	# Reuse same candidate normalization as description
	candidates: list[dict] = []
	if isinstance(job_data, dict):
		top_job = job_data.get("job")
		if isinstance(top_job, dict):
			candidates.append(top_job)
		if any(k in job_data for k in ("job_info", "title", "jobTitle", "position", "name")):
			candidates.append(job_data)
		items = job_data.get("items")
		if isinstance(items, list):
			for it in items:
				if isinstance(it, dict):
					candidates.append(it)
	else:
		return None

	for job in candidates:
		title = _pick_first_text(job, ["title", "jobTitle", "position", "name"]) 
		if title:
			return title
		job_info = job.get("job_info")
		if isinstance(job_info, dict):
			title = _pick_first_text(job_info, ["title", "jobTitle", "position", "name"]) 
			if title:
				return title

	return None


def extract_company_name(job_data: dict) -> str | None:
	candidates: list[dict] = []
	if isinstance(job_data, dict):
		top_job = job_data.get("job")
		if isinstance(top_job, dict):
			candidates.append(top_job)
		if any(k in job_data for k in ("company", "company_info", "companyName", "company_name")):
			candidates.append(job_data)
		items = job_data.get("items")
		if isinstance(items, list):
			for it in items:
				if isinstance(it, dict):
					candidates.append(it)
	else:
		return None

	for job in candidates:
		company = _pick_first_text(job, ["company", "companyName", "company_name"]) 
		if company:
			return company
		company_info = job.get("company_info")
		if isinstance(company_info, dict):
			company = _pick_first_text(company_info, ["name", "company", "title", "universal_name"]) 
			if company:
				return company
		company_obj = job.get("company")
		if isinstance(company_obj, dict):
			company = _pick_first_text(company_obj, ["name", "title"]) 
			if company:
				return company
		# job_info block
		job_info = job.get("job_info")
		if isinstance(job_info, dict):
			company = _pick_first_text(job_info, ["company", "companyName", "company_name"]) 
			if company:
				return company

	return None
