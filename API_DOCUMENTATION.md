# CV Maker API Documentation

**Overview**
- **Purpose:**: Describe each HTTP endpoint exposed by the FastAPI app in `app.py` and show example requests and responses.
- **Base URL:**: `http://<host>:<port>` (default when running locally with Uvicorn: `http://127.0.0.1:8000`)

**Security (API Key, no login flow)**
- Protected APIs require an API key header on every request.
- Configure using environment variables:
  - `API_KEY`: Long random secret key (required for protected routes).
  - `API_KEY_HEADER`: Header name to read the key from (optional, default: `X-API-Key`).
  - `ALLOWED_IPS`: Optional comma-separated client IP allowlist.
- Public routes: `/health`, `/docs`, `/redoc`, `/openapi.json`.
- Example:

```bash
curl -X POST http://127.0.0.1:8000/api/profile \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your_api_key>" \
  -d '{"full_name":"Tony","title":"Engineer","location":"Cairo","phone":"000","email":"a@b.com","links":{"github":"x","linkedin":"y"},"professional_summary":"...","core_skills":{},"education":{"degree":"BSc","institution":"X","location":"Y","graduation_date":"2020"}}'
```

**Custom Gemini API key (optional per request)**
- You can override the server Gemini key for a single request by sending header `X-Gemini-Api-Key`.
- Supported on AI endpoints: `/api/gemini/chat`, `/api/job/generate-pdf`, `/api/job/generate-pdf-from-description`, `/api/cv/generate-data`.
- Header takes precedence over request-body `gemini_api_key` field when both are provided.

**Endpoints**

**Health Check**
- **Method:**: GET
- **Path:**: `/health`
- **Description:**: Basic liveness check for the service.
- **Request Example:**: No body required.
- **Curl:**:

```bash
curl -X GET http://127.0.0.1:8000/health
```

- **Success Response (200):**

```json
{
  "status": "ok"
}
```


**Chat with Gemini**
- **Method:**: POST
- **Path:**: `/api/gemini/chat`
- **Description:**: Send a prompt to the configured Gemini model via the `ask_gemini` helper. Returns the model text response.
- **Request Body Schema:**
  - `prompt` (string, required): Prompt text to send to Gemini.
  - `model` (string, optional): Gemini model name. Default: `gemini-2.0-flash`.

- **Request Example:**

```json
{
  "prompt": "Summarize the responsibilities of a backend engineer.",
  "model": "gemini-2.0-flash"
}
```

- **Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/gemini/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize the responsibilities of a backend engineer."}'
```

- **Success Response (200):** (response model `ChatResponse`)

```json
{
  "response": "A backend engineer designs and implements server-side logic..."
}
```

- **Errors:**
  - `500` when Gemini request fails. Response shape: `{"detail": "Gemini request failed: <error>"}`


**Extract Job Data**
- **Method:**: POST
- **Path:**: `/api/job/extract`
- **Description:**: Uses Apify helper `fetch_job_data_with_apify` to fetch job data for a given LinkedIn job URL. Returns raw data from Apify.
- **Request Body Schema:**
  - `url` (string, required): A LinkedIn job `HttpUrl` containing the job identifier (e.g., `currentJobId` query param)
   - `url` (string, required): A LinkedIn job `HttpUrl` containing the job identifier. Supports either a `currentJobId` query parameter or a path-based job URL like `/jobs/view/{id}/`.

   - **Accepted URL formats:**
     - `https://www.linkedin.com/jobs/view/{id}/`
     - `https://www.linkedin.com/jobs/view/{id}/?currentJobId={id}`

- **Request Example:**

```json
{
  "url": "https://www.linkedin.com/jobs/view/1234567890/?currentJobId=1234567890"
}
```

- **Curl:**

```bash
curl -X POST http://127.0.0.1:8000/api/job/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.linkedin.com/jobs/view/1234567890/?currentJobId=1234567890"}'
```

- **Success Response (200):**
- Returns a JSON object produced by `fetch_job_data_with_apify`. Example (fields vary by Apify result):

```json
{
  "title": "Senior Backend Engineer",
  "company": "ExampleCorp",
  "location": "Remote",
  "description": "We are looking for...",
  "rawApify": {...}
}
```

- **Errors:**
  - `400` if the URL is invalid or extraction fails with a known input error. Response: `{"detail": "<error message>"}`
  - `500` for unexpected failures: `{"detail":"Job extraction failed: <error>"}`


**Generate Resume PDF from Job URL**
- **Method:**: POST
- **Path:**: `/api/job/generate-pdf`
- **Description:**: Fetches job data via Apify, extracts job description and title, builds resume sections using `build_resume_sections`, merges with stored user profile (must exist), and returns a generated PDF as a binary file attachment.
- **Request Body Schema:**
  - `url` (HttpUrl, required): LinkedIn job URL.
  - `full_name` (string, optional): Name to show in generated PDF. Falls back to profile's `full_name`.
  - `model` (string, optional): Gemini model used for building sections. Default: `gemini-3-flash-preview`.

- **Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/job/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.linkedin.com/jobs/view/1234567890/?currentJobId=1234567890"}' \
  --output resume.pdf
```

- **Success Response (200):**
  - Binary PDF content with header `Content-Disposition: attachment; filename="<sanitized>.pdf"`

- **Errors:**
  - `400` if profile not found or job description cannot be extracted. Example: `{"detail":"Profile not found. Please create your profile first using /api/profile."}`
  - `500` for other failures: `{"detail":"PDF generation failed: <error>"}`

- **Notes:**
  - Ensure a profile exists via `/api/profile` before calling this endpoint.
  - The PDF filename is generated from the profile name, company and role, sanitized to avoid invalid characters.


**Generate Resume PDF from Job Description**
- **Method:**: POST
- **Path:**: `/api/job/generate-pdf-from-description`
- **Description:**: Builds resume sections directly from a supplied raw job description string, merges with stored profile data, and returns a PDF attachment.
- **Request Body Schema:**
  - `job_description` (string, required, min length 20): Raw job description text.
  - `company_name` (string, optional)
  - `job_role` (string, optional)
  - `full_name` (string, optional)
  - `model` (string, optional)

- **Request Example:**

```json
{
  "job_description": "We are seeking a senior engineer responsible for backend services...",
  "company_name": "ExampleCorp",
  "job_role": "Senior Backend Engineer"
}
```

- **Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/job/generate-pdf-from-description \
  -H "Content-Type: application/json" \
  -d '{"job_description":"We are seeking a senior engineer responsible for backend services...","company_name":"ExampleCorp","job_role":"Senior Backend Engineer"}' \
  --output resume.pdf
```

- **Success Response (200):** Binary PDF as attachment.
- **Errors:**
  - `400` if profile missing or job_description invalid.
  - `500` for other errors.


**Two-step CV generation (new APIs)**

**Generate CV Data (AI-only)**
- **Method:**: POST
- **Path:**: `/api/cv/generate-data`
- **Description:**: Sends a job description (or a LinkedIn job `url`) to the AI to generate structured, editable CV data (sections, bullets, summaries) without rendering a file. Use this to preview or edit the AI output before creating a PDF/DOCX to reduce token usage and allow manual edits.
- **Request Body (one of):**
  - `url` (HttpUrl, optional): LinkedIn job URL. If provided, the server will fetch the job description via Apify.
  - `job_description` (string, optional): Raw job description text.
  - `company_name` (string, optional)
  - `job_role` (string, optional)
  - `full_name` (string, optional)
  - `model` (string, optional): Gemini model to use.
  - `generate_cv` (boolean, optional, default: `true`): Whether to generate CV sections.
  - `generate_email_message` (boolean, optional): When `true`, includes `email_message` in response.

- **Behavior:**
  - If `url` is provided the endpoint runs the Apify extraction and uses the extracted description as input to the AI.
  - If `job_description` is provided it will be used directly.
  - Optional overrides (`company_name`, `job_role`, `full_name`) will be respected when provided and non-placeholder.
  - When `generate_cv`, `generate_cover_letter`, and/or `generate_email_message` are enabled together, the server performs a single AI request and returns all requested artifacts from one JSON response.

- **Success Response (200):** JSON object with the generated CV data (sections, bullets, suggested `filename`, and metadata). Example (simplified):

```json
{
  "filename": "Jane_Doe_ExampleCorp_Senior_Backend_Engineer.pdf",
  "sections": [
    {"title":"Professional Summary","content":"..."},
    {"title":"Experience","items":[...]} 
  ],
  "metadata": {"company_name":"ExampleCorp","job_role":"Senior Backend Engineer"},
  "email_message": {
    "subject": "Application for NodeJs Developer",
    "body": "Dear Hiring Manager,\n..."
  }
}
```

- **Errors:**
  - `400` if neither `url` nor `job_description` is provided or inputs are invalid.
  - `500` for AI or extraction failures.


**Render CV (from generated data)**
- **Method:**: POST
- **Path:**: `/api/cv/render`
- **Description:**: Accepts the structured CV data produced by `/api/cv/generate-data` (or manually authored data) and renders it to a binary document (PDF or DOCX).
- **Request Body Schema:**
  - `data` (object, required): The generated CV object returned by `/api/cv/generate-data`.
  - `format` (string, optional): `pdf` (default) or `docx`.
  - `filename` (string, optional): Override for the output filename (extension will be applied according to `format`).

- **Success Response (200):** Binary file attachment with appropriate `Content-Type` and `Content-Disposition` headers. Example header: `Content-Disposition: attachment; filename="<sanitized>.(pdf|docx)"`.

- **Errors:**
  - `400` if `data` is missing or malformed.
  - `500` for rendering failures.


**Notes on using the two-step flow**
- Use `/api/cv/generate-data` to get editable, structured AI output and edit it locally or via client UI. Then call `/api/cv/render` to create the final document. This reduces repeated AI calls when making small edits.


**Generate Resume PDF from Job URL (unified flow — server-side two-step)**
- **Method:**: POST
- **Path:**: `/api/job/generate-pdf`
- **Description:**: Convenience endpoint that implements the full two-step flow on the server: it fetches job data (when given a LinkedIn `url`), calls the same AI generation used by `/api/cv/generate-data` to produce structured CV data, and then renders that data to a PDF (equivalent to `/api/cv/generate-data` + `/api/cv/render` performed sequentially). Use this if you want a single request that returns a PDF. For finer control or to save tokens, prefer the two-step endpoints.
- **Request Body Schema:**
  - `url` (HttpUrl, required when using a LinkedIn link): LinkedIn job URL.
  - `job_description` (string, optional): If supplied, used directly instead of fetching from Apify.
  - `company_name` (string, optional)
  - `job_role` (string, optional)
  - `full_name` (string, optional)
  - `model` (string, optional)

- **Curl Example:** (same as before — this endpoint returns a PDF)

```bash
curl -X POST http://127.0.0.1:8000/api/job/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.linkedin.com/jobs/view/1234567890/"}' \
  --output resume.pdf
```

- **Success Response (200):** Binary PDF content with header `Content-Disposition: attachment; filename="<sanitized>.pdf"`.

- **Errors:**
  - `400` if profile not found or job description cannot be extracted.
  - `500` for other failures.


**Create User Profile**
- **Method:**: POST
- **Path:**: `/api/profile`
- **Description:**: Save the user's profile data to the profile store via `create_profile`.
- **Request Body Schema (UserProfileCreateRequest):**
  - `full_name` (string)
  - `title` (string)
  - `location` (string)
  - `phone` (string)
  - `email` (string)
  - `links` (object): `{ "github": "...", "linkedin": "..." }`
  - `professional_summary` (string)
  - `core_skills` (object): lists for categories like `languages_and_frameworks`, `databases_and_tools`, etc.
  - `professional_experience` (array): list of experience items with `title`, `company`, `duration`, `description`.
  - `education` (object): `degree`, `institution`, `location`, `graduation_date`.
  - `training_and_certifications` (array)

- **Request Example:**

```json
{
  "full_name":"Jane Doe",
  "title":"Senior Backend Engineer",
  "location":"Remote",
  "phone":"+1-555-555-5555",
  "email":"jane@example.com",
  "links": {"github":"https://github.com/janedoe","linkedin":"https://linkedin.com/in/janedoe"},
  "professional_summary":"Experienced backend engineer...",
  "core_skills":{
    "languages_and_frameworks":["Python","FastAPI"],
    "databases_and_tools":["PostgreSQL","Redis"],
    "testing_and_devops":["PyTest","Docker"],
    "development_practices":["TDD","CI/CD"]
  },
  "professional_experience":[
    {"title":"Backend Engineer","company":"ExampleCorp","duration":"2019-2024","description":"Worked on APIs"}
  ],
  "education": {"degree":"BSc Computer Science","institution":"University","location":"City","graduation_date":"2018"},
  "training_and_certifications":[]
}
```

- **Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/profile \
  -H "Content-Type: application/json" \
  -d @profile.json
```

- **Success Response (201/200):** (response model `UserProfileCreateResponse`)

```json
{
  "id": "<profile-id>",
  "message": "Profile saved successfully"
}
```

- **Errors:**
  - `500` if saving fails. Response: `{"detail":"Failed to save profile: <error>"}`


**Get User Profile**
- **Method:**: GET
- **Path:**: `/api/profile`
- **Description:**: Returns the currently stored user profile.
- **Curl Example:**

```bash
curl -X GET http://127.0.0.1:8000/api/profile
```

- **Success Response (200):**
- Returns the full profile object previously saved. Example:

```json
{
  "id": "<profile-id>",
  "full_name": "Jane Doe",
  "title": "Senior Backend Engineer",
  "location": "Remote",
  "phone": "+1-555-555-5555",
  "email": "jane@example.com",
  "links": {"github":"...","linkedin":"..."},
  "professional_summary":"...",
  "core_skills":{...},
  "professional_experience":[...],
  "education":{...},
  "training_and_certifications":[...]
}
```

- **Errors:**
  - `404` when no profile exists: `{"detail":"Profile not found"}`
  - `500` for other failures.


**Update User Profile**
- **Method:**: PUT
- **Path:**: `/api/profile`
- **Description:**: Replace/update the stored profile with the provided object. Returns confirmation with the profile id.
- **Request Body:**: Same as `UserProfileCreateRequest`.
- **Curl Example:**

```bash
curl -X PUT http://127.0.0.1:8000/api/profile \
  -H "Content-Type: application/json" \
  -d @profile.json
```

- **Success Response (200):** (response model `UserProfileUpdateResponse`)

```json
{
  "id": "<profile-id>",
  "message": "Profile updated successfully"
}
```

- **Errors:**
  - `500` if update fails or profile cannot be loaded after update.


**Common Error Response Shape**
- FastAPI returns error bodies in the shape:

```json
{
  "detail": "<message>"
}
```


**Running Locally**
- Install dependencies from `requirements.txt`.
- Start the app with Uvicorn:

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

**Notes & Recommendations**
- Ensure any external services required by `ask_gemini`, `fetch_job_data_with_apify`, and PDF generation (Apify, Gemini credentials, templates) are configured before calling those endpoints.
- The PDF endpoints depend on an existing profile stored by `/api/profile`.

---

_Last updated: generated by Copilot based on `app.py` implementation._
