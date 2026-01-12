"""Data formatting functions for CV sections."""

from typing import Any

from .constants import SKILL_BULLET_MARKER, EXP_BULLET_MARKER
from .utils import normalize_text, normalize_list, format_block


def format_summary(data: dict[str, Any]) -> str:
    """Format summary section from CV data."""
    summary = data.get("summary")
    if isinstance(summary, str):
        return summary.strip()
    summary = summary or {}
    parts = []
    paragraph = normalize_text(summary.get("paragraph")).strip()
    about = normalize_text(summary.get("about")).strip()
    if paragraph:
        parts.append(paragraph)
    if about:
        parts.append(about)
    return "\n".join(parts)


def format_skills(data: dict[str, Any]) -> str:
    """Format skills section from CV data."""
    skills = data.get("skills") or []
    if isinstance(skills, dict):
        skills = [skills]
    lines: list[str] = []
    for skill in skills:
        title = normalize_text(skill.get("title")).strip()
        if title:
            lines.append(title)
        bullets = normalize_list(skill.get("bullets"))
        for bullet in bullets:
            text = normalize_text(bullet).strip()
            if text:
                lines.append(f"{SKILL_BULLET_MARKER}{text}")
    return format_block(lines)


def is_entrepreneurship(item: dict[str, Any]) -> bool:
    """Check if experience item is entrepreneurship-related."""
    role = normalize_text(item.get("role")).lower()
    return any(keyword in role for keyword in ["co-founder", "founder", "ceo", "cto"])


def format_experience_block(item: dict[str, Any]) -> str:
    """Format a single experience block."""
    lines: list[str] = []

    # Company and dates
    company = normalize_text(item.get("company")).strip()
    dates = normalize_text(item.get("dates")).strip()
    duration = normalize_text(item.get("duration")).strip()
    line_parts = [part for part in (company, f"({dates})" if dates else "", duration) if part]
    if line_parts:
        lines.append(" ".join(line_parts))

    # Company description and URL
    company_desc = normalize_text(item.get("company_desc")).strip()
    if company_desc:
        lines.append(company_desc)
    company_url = normalize_text(item.get("company_url")).strip()
    if company_url:
        lines.append(company_url)

    # Role and employment type
    role = normalize_text(item.get("role")).strip()
    employment = normalize_text(item.get("employment")).strip()
    role_line = ""
    if role and employment:
        role_line = f"{role} / {employment}"
    elif role:
        role_line = role
    elif employment:
        role_line = employment
    if role_line:
        lines.append(role_line)

    # Bullet points
    bullets = normalize_list(item.get("bullets"))
    for bullet in bullets:
        text = normalize_text(bullet).strip()
        if text:
            lines.append(f"{EXP_BULLET_MARKER}{text}")

    # Technologies
    technologies = normalize_text(item.get("technologies")).strip()
    if technologies:
        lines.append(f"Tech: {technologies}")

    return format_block(lines)


def format_experiences(data: dict[str, Any]) -> tuple[str, str]:
    """
    Format experience section, separating main experience and entrepreneurship.

    Returns:
        Tuple of (main_experience, entrepreneurship)
    """
    experience = data.get("experience") or []
    if isinstance(experience, dict):
        experience = [experience]

    main_items: list[dict[str, Any]] = []
    entrepreneurship_items: list[dict[str, Any]] = []

    for item in experience:
        if is_entrepreneurship(item):
            entrepreneurship_items.append(item)
        else:
            main_items.append(item)

    exp_lines: list[str] = []
    for item in main_items:
        block = format_experience_block(item)
        if block:
            exp_lines.append(block)

    ent_lines: list[str] = []
    for item in entrepreneurship_items:
        block = format_experience_block(item)
        if block:
            ent_lines.append(block)

    # Join blocks with triple newlines to ensure distinct visual gap
    return "\n\n\n".join(exp_lines), "\n\n\n".join(ent_lines)


def format_education(data: dict[str, Any]) -> str:
    """Format education section from CV data."""
    education = data.get("education") or {}

    if isinstance(education, list):
        lines: list[str] = []
        for item in education:
            if not isinstance(item, dict):
                text = normalize_text(item).strip()
                if text:
                    lines.append(text)
                continue
            dates = normalize_text(item.get("dates")).strip()
            school = normalize_text(item.get("school")).strip()
            degree = normalize_text(item.get("degree")).strip()
            parts = [part for part in (dates, school, degree) if part]
            if parts:
                lines.append(" - ".join(parts))
        return format_block(lines)

    dates = normalize_text(education.get("dates")).strip()
    school = normalize_text(education.get("school")).strip()
    degree = normalize_text(education.get("degree")).strip()
    parts = [part for part in (dates, school, degree) if part]
    return " - ".join(parts)


def format_publications(data: dict[str, Any]) -> str:
    """Format publications section from CV data."""
    publications = data.get("publications")
    if not publications:
        return ""
    if isinstance(publications, str):
        return publications.strip()
    lines: list[str] = []
    for item in normalize_list(publications):
        text = normalize_text(item).strip()
        if text:
            lines.append(f"- {text}")
    return format_block(lines)


def build_replacements(data: dict[str, Any]) -> dict[str, str]:
    """
    Build all placeholder replacements from CV data.

    Args:
        data: Structured CV data dictionary

    Returns:
        Dictionary mapping placeholder keys to replacement values
    """
    summary = format_summary(data)
    skills = format_skills(data)
    exps, entrepreneurship = format_experiences(data)
    education = format_education(data)
    publications = format_publications(data)

    header = data.get("header") or {}
    contact = header.get("contact") or {}

    header_replacements = {
        "{{fullname}}": normalize_text(header.get("full_name")),
        "{{title}}": normalize_text(header.get("role_title")),
        "{{nickname}}": normalize_text(header.get("nickname")),
        "{{timezone}}": normalize_text(contact.get("timezone")),
        "{{email}}": f"✉️ Email: {normalize_text(contact.get('email'))}".strip(),
        "{{github}}": f"⚒️ Github: {normalize_text(contact.get('github'))}".strip(),
        "{{website}}": normalize_text(contact.get('website')),
        "{{tags}}": normalize_text(header.get("tags")),
        "{{phone}}": f"📞 Phone: {normalize_text(contact.get('phone'))}".strip(),
        "{{available_for}}": f"📖 Availability: {normalize_text(contact.get('availability'))}".strip(),
        "{{legal_entity}}": f"💼 Legal entity: {normalize_text(contact.get('legal_entity'))}".strip(),
    }

    return {
        **header_replacements,
        "{{SUMMARY}}": summary,
        "{{skills}}": skills,
        "{{exps}}": exps,
        "{{education}}": education,
        "{{entrepreneurship}}": entrepreneurship,
        "{{publications}}": publications,
    }
