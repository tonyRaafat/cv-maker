# Cover Letter Render API

This document describes the new Cover Letter rendering endpoint added under the `/api/cv` namespace. It explains how to obtain a cover letter (via the AI bundle endpoint) and how to render it to a downloadable PDF or DOCX file.

**Endpoint**
- POST /api/cv/render-cover-letter

**Purpose**
- Accept a plain-text cover letter and return a downloadable file (PDF or DOCX).
- Intended to be used after generating a cover letter with the AI bundle endpoint (`/api/cv/generate-data`).

**Authentication & Access**
- The application registers a global dependency `verify_api_access` (see `app.py`). Requests must satisfy the same access checks as other API endpoints.
- The cover-letter rendering endpoint itself does not require an AI key. If you need AI generation, call `/api/cv/generate-data` and pass the `X-Gemini-Api-Key` header or `gemini_api_key` field in that request.

**Request schema** (JSON body)
- `full_name` (string) — Candidate's full name. Used for filename and optional heading.
- `company_name` (string) — Company name for filename/heading.
- `role_title` (string) — Target role for filename/heading.
- `source` (string, optional) — Job URL or job source string. Defaults to `manual-job-description`.
- `format` (string) — Either `pdf` or `docx`. Case-insensitive. Defaults to `pdf`.
- `cover_letter` (string) — The full cover letter body in plain text (may contain paragraphs separated by blank lines).

This matches the `CoverLetterRenderRequest` model in `api/cv/schemas.py`.

**Response**
- Returns a binary attachment (Content-Disposition: attachment). The response `media_type` is:
  - `application/pdf` for PDF
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` for DOCX
- The file name is auto-generated and sanitized as `{Full Name} cover letter | {Company} | {Role}.{ext}` with characters replaced to be filesystem-safe.

**Typical usage flow**
1. Generate a cover letter using the AI bundle endpoint (optional):
   - POST `/api/cv/generate-data` with `generate_cover_letter=true` and other parameters.
   - If you pass an AI key per-request, include header `X-Gemini-Api-Key: <KEY>` or set `gemini_api_key` in the request body.
   - The response `CvGenerateDataResponse.cover_letter` contains the generated plain text cover letter.
2. Render the returned cover letter to file:
   - POST `/api/cv/render-cover-letter` with `cover_letter` set to the text from step 1 and `format` set to `pdf` or `docx`.
   - The response is a file download.

**Example: generate cover letter (curl)**

```bash
curl -X POST "https://<your-host>/api/cv/generate-data" \
  -H "Content-Type: application/json" \
  -H "X-Gemini-Api-Key: <YOUR_KEY>" \
  -d '{
    "job_description": "We are hiring a backend engineer...",
    "full_name": "Jane Doe",
    "company_name": "Acme Inc",
    "job_role": "Backend Engineer",
    "generate_cv": false,
    "generate_cover_letter": true,
    "generate_email_message": false
  }'
```

- Inspect `cover_letter` in the JSON response.

**Example: render cover letter to PDF (curl)**

```bash
curl -X POST "https://<your-host>/api/cv/render-cover-letter" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "company_name": "Acme Inc",
    "role_title": "Backend Engineer",
    "format": "pdf",
    "cover_letter": "Dear Hiring Manager,\n\nI am writing to...\n\nSincerely,\nJane Doe"
  }' --output "jane-doe-cover-letter.pdf"
```

**Example: render cover letter to DOCX (curl)**

```bash
curl -X POST "https://<your-host>/api/cv/render-cover-letter" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "company_name": "Acme Inc",
    "role_title": "Backend Engineer",
    "format": "docx",
    "cover_letter": "Dear Hiring Manager,\n\nI am writing to...\n\nSincerely,\nJane Doe"
  }' --output "jane-doe-cover-letter.docx"
```

**HTTP status codes**
- 200: File returned successfully.
- 400: Bad request (missing required fields or invalid JSON).
- 401/403: Authorization/access denied depending on `verify_api_access` rules.
- 500: Server error if file generation fails.

**Notes & recommendations**
- The endpoint expects the `cover_letter` body to be final plain text. If you want the API to generate the cover letter, use the `generate-data` bundle flow and pass `generate_cover_letter=true`.
- The cover-letter render behavior preserves paragraph boundaries (split on blank lines). Markdown-style bold (`**bold**`) will be stripped in the PDF fallback if necessary.
- Filenames are sanitized using the same logic as CV rendering (`utils._sanitize_filename`).
- If you want to include links in the DOCX/PDF header, pass them in the `source` field and they will be printed as plain text.
- Be mindful of model hallucinations when using the AI to generate cover letters; review generated text before rendering.

**Files changed / new API wiring**
- New route: `POST /api/cv/render-cover-letter` implemented in `api/cv/router.py`.
- Service wrapper: `render_cover_letter(...)` in `api/cv/service.py`.
- Request model: `CoverLetterRenderRequest` in `api/cv/schemas.py`.
- File generation helpers added to `resume_pdf_service.py`: `create_cover_letter_docx` and `create_cover_letter_pdf`.
- Response helper in `utils.py`: `render_cover_letter_response`.

If you'd like, I can:
- Add an example integration test that POSTs a sample cover letter and saves the returned file.
- Add a short note to the main `API_DOCUMENTATION.md` linking to this file.
