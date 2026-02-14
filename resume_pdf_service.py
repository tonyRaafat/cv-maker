import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

from gemini_chat import ask_gemini


def _load_cv_structure_markdown() -> str:
    template_path = Path(__file__).with_name("cv_structure.md")
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "Use an ATS-friendly one-page CV structure."


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("AI response did not contain valid JSON.")
        snippet = text[start : end + 1]
        return json.loads(snippet)


def _safe_text(value: str) -> str:
    text = value
    replacements = {
        "•": "-",
        "●": "-",
        "◦": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "\u00a0": " ",
        "\u200b": "",
        "Â": "",
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "Â·": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove malformed markdown emphasis markers that can leak as visible asterisks
    text = re.sub(r"\*{3,}", "", text)
    text = re.sub(r"(?<!\*)\*{1}(?!\*)", "", text)

    text = text.encode("latin-1", errors="ignore").decode("latin-1")
    text = re.sub(r"\s+", " ", text).strip()
    # FPDF can fail when a single token is wider than the printable area.
    # Break very long non-space tokens into smaller chunks.
    parts = text.split()
    normalized: list[str] = []
    for part in parts:
        if len(part) <= 45:
            normalized.append(part)
            continue
        chunks = [part[i : i + 45] for i in range(0, len(part), 45)]
        normalized.append(" ".join(chunks))
    return " ".join(normalized)


def build_resume_sections(job_description: str, model_name: str, profile_data: dict[str, Any]) -> dict:
    cv_structure = _load_cv_structure_markdown()
    profile_json = json.dumps(profile_data, ensure_ascii=False)
    prompt = (
        "You are an expert resume writer. Create CV content using BOTH the candidate profile data and job description. "
        "Follow the CV structure and ATS instructions exactly. "
        "Do not invent candidate facts that are not present in profile data. "
        "For professional experience and personal projects, write concise impact-focused bullets using action verbs. "
        "Prioritize keywords and responsibilities from the target job description. "
        "If profile projects exist, include the strongest and most relevant ones in personal_projects. "
        "For each project, include name, tech_stack, and measurable or concrete outcomes when possible. "
        "Return ONLY valid JSON with the schema defined in the markdown instructions. "
        "Do not include markdown fences. "
        f"CV structure instructions (markdown):\n{cv_structure}\n\n"
        f"Candidate profile data (JSON):\n{profile_json}\n\n"
        f"Job description:\n{job_description}"
    )

    raw = ask_gemini(prompt, model_name=model_name)
    data = _extract_json(raw)

    for required_key in [
        "header",
        "professional_summary",
        "core_skills",
        "professional_experience",
        "personal_projects",
        "education",
        "training_certifications",
    ]:
        if required_key not in data:
            raise ValueError(f"AI response missing key: {required_key}")

    return data


def _normalize_lines(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip() for line in re.split(r"\n+", value) if line.strip()]
    return []


def _remove_years_claims(text: str) -> str:
    # Avoid overstating experience duration if the model hallucinates year counts.
    cleaned = re.sub(
        r"\b\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience\b",
        "hands-on experience",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _strip_markdown_asterisks(text: str) -> str:
    return re.sub(r"\*+", "", text)


def _emphasize_keywords(text: str, keywords: list[str]) -> str:
    emphasized = _strip_markdown_asterisks(text)
    cleaned_keywords = sorted({k.strip() for k in keywords if isinstance(k, str) and k.strip()}, key=len, reverse=True)
    for keyword in cleaned_keywords:
        pattern = re.compile(rf"(?<!\w)({re.escape(keyword)})(?!\w)", re.IGNORECASE)
        emphasized = pattern.sub(lambda m: f"**{m.group(1)}**", emphasized)
    emphasized = re.sub(r"(~?\d+%?)", r"**\1**", emphasized)
    return emphasized


def create_pdf_from_template(
    output_path: Path | None,
    full_name: str,
    role_title: str,
    company_name: str,
    job_url: str,
    sections: dict,
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    header = sections.get("header", {}) if isinstance(sections.get("header", {}), dict) else {}

    core_skills = sections.get("core_skills", {}) if isinstance(sections.get("core_skills", {}), dict) else {}
    emphasis_keywords = []
    for group_key in [
        "languages_frameworks",
        "databases_tools",
        "testing_devops",
        "development_practices",
    ]:
        emphasis_keywords.extend(_normalize_lines(core_skills.get(group_key)))

    def draw_divider() -> None:
        y = pdf.get_y() + 1
        pdf.set_draw_color(160, 160, 160)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(4)

    def write_line(text: str, h: float = 6, bold: bool = False) -> None:
        pdf.set_x(pdf.l_margin)
        if bold:
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, h, _safe_text(text))
            return
        try:
            pdf.multi_cell(0, h, _safe_text(text), markdown=True)
        except TypeError:
            pdf.multi_cell(0, h, _safe_text(text.replace("**", "")))

    def normalize_url(raw: str) -> str:
        value = raw.strip()
        if not value:
            return value
        if value.lower().startswith(("http://", "https://", "mailto:")):
            return value
        return f"https://{value}"

    def write_clickable_line(label: str, url_text: str, link: str, h: float = 6) -> None:
        if not url_text.strip() or not link.strip():
            return
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        label_text = _safe_text(label)
        if label_text:
            pdf.write(h, label_text)

        pdf.set_font("Helvetica", "U", 10)
        pdf.set_text_color(0, 64, 160)
        pdf.write(h, _safe_text(url_text), link=link)
        pdf.ln(h)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

    display_name = str(header.get("full_name") or full_name).strip()
    display_title = str(header.get("job_title") or role_title).strip()
    display_location = str(header.get("location") or "").strip()
    display_phone = str(header.get("phone") or "").strip()
    display_email = str(header.get("email") or "").strip()
    display_github = str(header.get("github") or "").strip()
    display_linkedin = str(header.get("linkedin") or "").strip()

    pdf.set_font("Helvetica", "B", 18)
    write_line(display_name, h=10, bold=True)

    if display_title:
        pdf.set_font("Helvetica", "", 12)
        write_line(display_title, h=7)

    contact_parts = [part for part in [display_location, display_phone] if part]
    if contact_parts:
        pdf.set_font("Helvetica", "", 10)
        write_line(" | ".join(contact_parts), h=6)

    if display_email:
        write_clickable_line("", display_email, f"mailto:{display_email}", h=6)

    if display_github:
        write_clickable_line("GitHub: ", display_github, normalize_url(display_github), h=6)
    if display_linkedin:
        write_clickable_line("LinkedIn: ", display_linkedin, normalize_url(display_linkedin), h=6)

    draw_divider()

    def section(title: str, lines: list[str]) -> None:
        if not lines:
            return
        pdf.set_font("Helvetica", "B", 12)
        write_line(title, h=8, bold=True)
        pdf.set_font("Helvetica", "", 11)
        for line in lines:
            emphasized = _emphasize_keywords(line, emphasis_keywords)
            write_line(f"- {emphasized}", h=6)
        draw_divider()

    summary = str(sections.get("professional_summary", "")).strip()
    if summary:
        summary = _remove_years_claims(summary)
        pdf.set_font("Helvetica", "B", 12)
        write_line("Professional Summary", h=8, bold=True)
        pdf.set_font("Helvetica", "", 11)
        write_line(_emphasize_keywords(summary, emphasis_keywords), h=6)
        draw_divider()

    if core_skills:
        pdf.set_font("Helvetica", "B", 12)
        write_line("Core Skills", h=8, bold=True)
        pdf.set_font("Helvetica", "", 11)

        skill_groups = [
            ("Languages & Frameworks", _normalize_lines(core_skills.get("languages_frameworks"))),
            ("Databases & Tools", _normalize_lines(core_skills.get("databases_tools"))),
            ("Testing & DevOps", _normalize_lines(core_skills.get("testing_devops"))),
            ("Development Practices", _normalize_lines(core_skills.get("development_practices"))),
        ]
        for label, values in skill_groups:
            if not values:
                continue
            line = f"**{label}:** {', '.join(values)}"
            write_line(line, h=6)
        draw_divider()

    experiences = sections.get("professional_experience")
    if isinstance(experiences, list) and experiences:
        pdf.set_font("Helvetica", "B", 12)
        write_line("Professional Experience", h=8, bold=True)
        for exp in experiences:
            if not isinstance(exp, dict):
                continue
            title = str(exp.get("title") or "").strip()
            company = str(exp.get("company") or "").strip()
            duration = str(exp.get("duration") or "").strip()

            heading = " ".join(part for part in [title, f"at {company}" if company else ""] if part).strip()
            if heading:
                pdf.set_font("Helvetica", "B", 11)
                write_line(heading, h=6, bold=True)
            if duration:
                pdf.set_font("Helvetica", "", 10)
                write_line(duration, h=5)

            pdf.set_font("Helvetica", "", 11)
            for line in _normalize_lines(exp.get("highlights")):
                emphasized = _emphasize_keywords(line, emphasis_keywords)
                write_line(f"- {emphasized}", h=6)
            pdf.ln(1)
        draw_divider()

    projects = sections.get("personal_projects")
    if isinstance(projects, list) and projects:
        pdf.set_font("Helvetica", "B", 12)
        write_line("Personal Projects", h=8, bold=True)
        for project in projects:
            if not isinstance(project, dict):
                continue
            name = str(project.get("name") or "").strip()
            tech_stack = _normalize_lines(project.get("tech_stack"))
            highlights = _normalize_lines(project.get("highlights"))

            if name:
                pdf.set_font("Helvetica", "B", 11)
                write_line(name, h=6, bold=True)
            if tech_stack:
                pdf.set_font("Helvetica", "", 10)
                write_line(f"Tech Stack: {', '.join(tech_stack)}", h=5)

            pdf.set_font("Helvetica", "", 11)
            for line in highlights:
                emphasized = _emphasize_keywords(line, emphasis_keywords + tech_stack)
                write_line(f"- {emphasized}", h=6)
            pdf.ln(1)
        draw_divider()

    section("Education", _normalize_lines(sections.get("education")))
    section("Training & Certifications", _normalize_lines(sections.get("training_certifications")))

    pdf_bytes = bytes(pdf.output())

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)

    return pdf_bytes
