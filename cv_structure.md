# Anton-Style ATS CV Guide

Use this structure to produce a clean, ATS-friendly, one-page CV matching the provided sample style.

## Required top layout

1. Full Name (largest text)
2. Job Title (e.g., Software Engineer)
3. Single contact line:
   - location | phone | email
4. Single links line:
   - GitHub | LinkedIn

## Required section order

1. Professional Summary
2. Core Skills
3. Professional Experience
4. Personal Projects
5. Education
6. Training & Certifications

## Style rules

- Keep formatting simple and ATS-safe (no tables/icons/columns).
- Use concise, achievement-based bullets.
- Emphasize measurable impact where supported by profile data.
- Tailor content to the target job description.
- Do not invent personal facts not present in profile.

## Section details

### Professional Summary

- 3-5 lines.
- Focus on strongest stack + outcomes + role alignment.

### Core Skills

Use grouped categories exactly:
- Languages & Frameworks
- Databases & Tools
- Testing & DevOps
- Development Practices

### Professional Experience

- Reverse chronological order.
- For each role include: title, company, duration.
- Include 3-6 impact bullets per role.

### Personal Projects

- Include 2-5 most relevant projects from the candidate profile.
- For each project include: project name, tech stack, and 2-4 impact bullets.
- Prefer projects that align with the target job stack and responsibilities.

### Education

- Include degree/certificate, institution, location, date.

### Training & Certifications

- List relevant courses and certifications.

## Output schema (strict JSON)

Return ONLY valid JSON with this schema:

{
  "header": {
    "full_name": "string",
    "job_title": "string",
    "location": "string",
    "phone": "string",
    "email": "string",
    "github": "string",
    "linkedin": "string"
  },
  "professional_summary": "string",
  "core_skills": {
    "languages_frameworks": ["string"],
    "databases_tools": ["string"],
    "testing_devops": ["string"],
    "development_practices": ["string"]
  },
  "professional_experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string",
      "highlights": ["string"]
    }
  ],
  "personal_projects": [
    {
      "name": "string",
      "tech_stack": ["string"],
      "highlights": ["string"]
    }
  ],
  "education": ["string"],
  "training_certifications": ["string"],
  "ats_keywords": ["string"],
  "customization_notes": ["string"]
}
