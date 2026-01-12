#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Any
import urllib.parse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import docs_batch_update, ensure_access_token, get_doc, load_oauth_client, read_text  # noqa: E402

EXP_BULLET_MARKER = "<<EXP_BULLET>> "
SKILL_BULLET_MARKER = "<<SKILL_BULLET>> "
TECH_PREFIXES = ("tech:", "technologies:")
URL_REGEX = re.compile(r'(?:https?://|www\.|github\.com/|linkedin\.com/|t\.me/)[^\s<>"]+')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'\+\d[\d\(\)\-\. ]{8,18}\d')
CONTACT_EMOJIS = ["✉️", "⚒️", "🌐", "📞", "📖", "💼"]


def strip_markers(value: str) -> str:
    """Removes bullet markers but KEEPS contact prefixes so we can reset them correctly."""
    return value.replace(SKILL_BULLET_MARKER, "").replace(EXP_BULLET_MARKER, "")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, value: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def format_block(lines: list[str]) -> str:
    cleaned = [line.rstrip() for line in lines]
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return "\n".join(cleaned)


def format_summary(data: dict[str, Any]) -> str:
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


def format_experience_block(item: dict[str, Any]) -> str:
    lines: list[str] = []
    company = normalize_text(item.get("company")).strip()
    dates = normalize_text(item.get("dates")).strip()
    duration = normalize_text(item.get("duration")).strip()
    line_parts = [part for part in (company, f"({dates})" if dates else "", duration) if part]
    if line_parts:
        lines.append(" ".join(line_parts))
    company_desc = normalize_text(item.get("company_desc")).strip()
    if company_desc:
        lines.append(company_desc)
    company_url = normalize_text(item.get("company_url")).strip()
    if company_url:
        lines.append(company_url)
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
    bullets = normalize_list(item.get("bullets"))
    for bullet in bullets:
        text = normalize_text(bullet).strip()
        if text:
            lines.append(f"{EXP_BULLET_MARKER}{text}")
    technologies = normalize_text(item.get("technologies")).strip()
    if technologies:
        lines.append(f"Tech: {technologies}")
    return format_block(lines)


def is_entrepreneurship(item: dict[str, Any]) -> bool:
    role = normalize_text(item.get("role")).lower()
    return "co-founder" in role or "founder" in role or "ceo" in role or "cto" in role


def format_experiences(data: dict[str, Any]) -> tuple[str, str]:
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
    # Join blocks with triple newlines to ensure a distinct visual gap and break bullet list inheritance
    return "\n\n\n".join(exp_lines), "\n\n\n".join(ent_lines)


def format_education(data: dict[str, Any]) -> str:
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


def log_line(message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}")


def parse_doc_links(markdown: str) -> dict[str, dict[str, str]]:
    links: dict[str, dict[str, str]] = {}
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        try:
            name, url = line[2:].split(":", 1)
        except ValueError:
            continue
        name = name.strip()
        url = url.strip()
        if not name or not url:
            continue
        doc_id = extract_doc_id_from_url(url)
        links[name] = {"name": name, "url": url, "document_id": doc_id}
    return links


def extract_doc_id_from_url(url: str) -> str | None:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return None
    parts = parsed.path.split("/")
    if "d" not in parts:
        return None
    try:
        idx = parts.index("d")
    except ValueError:
        return None
    if idx + 1 >= len(parts):
        return None
    return parts[idx + 1]


def find_doc_info(links_path: str, doc_name: str) -> tuple[str | None, str | None]:
    try:
        links = parse_doc_links(read_text(links_path))
    except FileNotFoundError:
        return None, None
    info = links.get(doc_name)
    if not info:
        return None, None
    return info.get("url"), info.get("document_id")


def apply_block_styles(
    *,
    doc_id: str | None,
    client_path: str,
    token_path: str,
    replacements: dict[str, str] | None = None,
) -> None:
    if not doc_id:
        log_line("⚠️ Cannot style blocks: document ID unknown.")
        return
    client = load_oauth_client(client_path)
    access_token = ensure_access_token(client=client, token_path=token_path)
    doc = get_doc(document_id=doc_id, access_token=access_token)
    content = (doc.get("body") or {}).get("content") or []
    requests: list[dict[str, Any]] = []

    # Find headers and record their ranges for explicit H2 styling
    headers_to_fix = ["Skills", "Experience", "Entrepreneurship", "Summary", "Education", "Publications"]
    for header_text in headers_to_fix:
        for item in content:
            if not item.get("paragraph"): continue
            text = get_paragraph_text(item).lower().strip()
            # ONLY style if the paragraph text EXACTLY matches the header (e.g., "Summary")
            # This avoids styling "Summary Content" or anchors.
            if header_text.lower() == text:
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": item.get("startIndex"), "endIndex": item.get("endIndex")},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                })
                # Also apply font style immediately
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": item.get("startIndex"), "endIndex": item.get("endIndex")},
                        "textStyle": {"bold": True, "fontSize": {"magnitude": 17, "unit": "PT"}},
                        "fields": "bold,fontSize",
                    }
                })
                break


    skills_range = find_section_range(content, "Skills", level=2)
    if not skills_range:
        skills_range = find_section_range(content, "Skills", level=0)
    if skills_range:
        bullets, styles = style_skills_section(doc, *skills_range)
        requests.extend(bullets)
        requests.extend(styles)
    
    exp_range = find_section_range(content, "Experience", level=2)
    if not exp_range:
        exp_range = find_section_range(content, "Experience", level=0)
    if exp_range:
        bullets, styles = style_experience_section(doc, *exp_range, bullet_marker=EXP_BULLET_MARKER)
        requests.extend(bullets)
        requests.extend(styles)
    
    ent_range = find_section_range(content, "Entrepreneurship", level=2)
    if not ent_range:
        ent_range = find_section_range(content, "Entrepreneurship", level=0)
    if ent_range:
        bullets, styles = style_experience_section(doc, *ent_range, bullet_marker=EXP_BULLET_MARKER)
        requests.extend(bullets)
        requests.extend(styles)

    edu_range = find_section_range(content, "Education", level=2)
    if not edu_range:
        edu_range = find_section_range(content, "Education", level=0)
    if edu_range:
        edu_paras = collect_paragraphs(content, *edu_range)
        for para in edu_paras:
            if para["text"]:
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": para["start"], "endIndex": para["end"]},
                        "textStyle": {"italic": True},
                        "fields": "italic",
                    }
                })

    # Reverse lookup for special styling
    inverted = {v: k for k, v in (replacements or {}).items() if v and isinstance(v, str)}
    
    # Auto-linkify URLs and emails in the whole document
    # And fix Heading 2 text styling (bold + 17pt) ONLY for real headers
    for item in iter_all_paragraphs(content):
        text = get_raw_paragraph_text(item)
        para_start = item.get("startIndex") or 0
        para_end = item.get("endIndex")
        
        # 1. Restore field-specific styles and minimize spacing
        anchor = inverted.get(text.strip())
        
        # Anchors that should have zero spacing for a compact header
        tight_anchors = [
            "{{fullname}}", "{{title}}", "{{nickname}}", "{{timezone}}", 
            "{{email}}", "{{github}}", "{{website}}", "{{tags}}", 
            "{{phone}}", "{{available_for}}", "{{legal_entity}}"
        ]

        if anchor in tight_anchors:
            p_style = {
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
                "lineSpacing": 100
            }
            p_fields = "spaceAbove,spaceBelow,lineSpacing"
            
            if anchor == "{{fullname}}":
                p_style["namedStyleType"] = "HEADING_1"
                p_fields += ",namedStyleType"
            elif anchor in ["{{title}}", "{{nickname}}"]:
                p_style["namedStyleType"] = "HEADING_3"
                p_fields += ",namedStyleType"
            
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": para_start, "endIndex": para_end},
                    "paragraphStyle": p_style,
                    "fields": p_fields
                }
            })
            
            # Additional text styles
            if anchor == "{{tags}}":
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": para_start, "endIndex": para_end},
                        "textStyle": {"italic": True},
                        "fields": "italic"
                    }
                })

        # 2. Enforce H2 style: Bold + 17pt ONLY for designated headers
        is_h2 = get_heading_level(item) == 2
        clean_text = text.strip().lower()
        if is_h2 and clean_text in [h.lower() for h in headers_to_fix]:
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": para_start, "endIndex": para_end},
                    "textStyle": {"bold": True, "fontSize": {"magnitude": 17, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            })
        elif is_h2:
            # If it's H2 but not a designated header, revert it to Normal Text if it looks like content
            if "{{" in text or len(text) > 40:
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": para_start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "fields": "namedStyleType",
                    }
                })

        requests.extend(create_link_requests(text, para_start))


    if not requests:
        log_line("ℹ️ No block styling requests generated.")
        return

    # Split requests into two batches: Bullet Creation vs Everything Else
    # This is CRITICAL because creating bullets resets indentation to default (36pt/18pt)
    # So we must create bullets first, THEN apply our custom 0-indent style in a separate batch.
    
    bullet_requests = []
    style_requests = []
    
    for req in requests:
        if "createParagraphBullets" in req:
            bullet_requests.append(req)
        else:
            style_requests.append(req)
            
    applied_count = 0
    
    # Phase 1: Create Bullets
    if bullet_requests:
        docs_batch_update(document_id=doc_id, access_token=access_token, requests=bullet_requests)
        log_line(f"🎨 Applied {len(bullet_requests)} bullet creation requests.")
        import time
        time.sleep(2) # Wait for bullets to register
        
    # Phase 2: Apply Styles (Indentation overrides, Headers, etc.)
    if style_requests:
        log_line(f"📝 Applying {len(style_requests)} style requests...")
        if style_requests:
            import json
            print("SAMPLE REQUEST:", json.dumps(style_requests[0], indent=2))
        docs_batch_update(document_id=doc_id, access_token=access_token, requests=style_requests)
        log_line(f"🎨 Applied {len(style_requests)} styling requests (in separate batches).")

    cleanup_requests = [
        {
            "replaceAllText": {
                "containsText": {"text": SKILL_BULLET_MARKER, "matchCase": True},
                "replaceText": "",
            }
        },
        {
            "replaceAllText": {
                "containsText": {"text": EXP_BULLET_MARKER, "matchCase": True},
                "replaceText": "",
            }
        },
        {
            "replaceAllText": {
                "containsText": {"text": SKILL_BULLET_MARKER.strip(), "matchCase": True},
                "replaceText": "",
            }
        },
        {
            "replaceAllText": {
                "containsText": {"text": EXP_BULLET_MARKER.strip(), "matchCase": True},
                "replaceText": "",
            }
        },
    ]
    docs_batch_update(document_id=doc_id, access_token=access_token, requests=cleanup_requests)
    log_line("🧹 Removed bullet helpers.")


def extract_placeholders(text: str) -> set[str]:
    return set(re.findall(r"\{\{[^}]+\}\}", text))


def read_state(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {"docs": {}}
    try:
        data = read_json(path)
    except (json.JSONDecodeError, OSError):
        return {"docs": {}}
    if not isinstance(data, dict):
        return {"docs": {}}
    if "docs" not in data or not isinstance(data["docs"], dict):
        data["docs"] = {}
    return data


def write_state(path: str, state: dict[str, Any]) -> None:
    write_json(path, state)


def update_state(
    *,
    state_path: str,
    doc: str,
    doc_url: str | None,
    doc_id: str | None,
    data_path: str,
    replacements: dict[str, str],
) -> None:
    state = read_state(state_path)
    state["docs"][doc] = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "doc_url": doc_url,
        "doc_id": doc_id,
        "data_path": data_path,
        "replacements": replacements,
        "cleaned_replacements": {k: strip_markers(v) for k, v in replacements.items()},
    }
    write_state(state_path, state)


def invert_replacements(replacements: dict[str, str]) -> tuple[dict[str, str], list[str], int]:
    inverted: dict[str, str] = {}
    collisions: list[str] = []
    skipped = 0
    for key, value in replacements.items():
        if not value:
            skipped += 1
            continue
        if value in inverted and inverted[value] != key:
            collisions.append(value)
            continue
        inverted[value] = key
    return inverted, collisions, skipped


def iter_all_paragraphs(content: list[dict[str, Any]]):
    for item in content:
        if item.get("paragraph"):
            yield item
        elif item.get("table"):
            table = item.get("table")
            for row in table.get("tableRows") or []:
                for cell in row.get("tableCells") or []:
                    yield from iter_all_paragraphs(cell.get("content") or [])


def get_paragraph_text(item: dict[str, Any]) -> str:
    para = item.get("paragraph")
    if not para:
        return ""
    elements = para.get("elements") or []
    text_parts = []
    for elem in elements:
        tr = elem.get("textRun")
        if not tr:
            continue
        text_parts.append(tr.get("content") or "")
    return "".join(text_parts).strip()


def get_raw_paragraph_text(item: dict[str, Any]) -> str:
    para = item.get("paragraph")
    if not para:
        return ""
    elements = para.get("elements") or []
    return "".join(elem.get("text_run", elem.get("textRun", {})).get("content", "") for elem in elements)


def create_link_requests(text: str, start_index: int) -> list[dict[str, Any]]:
    requests = []
    # URLs
    for match in URL_REGEX.finditer(text):
        url = match.group()
        # Clean up trailing punctuation often captured (.,:;)
        while url and url[-1] in '.,:;!?':
            url = url[:-1]
        if not url:
            continue
        full_url = url if url.startswith("http") else "http://" + url
        requests.append({
            "updateTextStyle": {
                "range": {
                    "startIndex": start_index + match.start(),
                    "endIndex": start_index + match.start() + len(url),
                },
                "textStyle": {"link": {"url": full_url}},
                "fields": "link",
            }
        })
    # Emails
    for match in EMAIL_REGEX.finditer(text):
        email = match.group()
        while email and email[-1] in '.,:;!?':
            email = email[:-1]
        if not email:
            continue
        requests.append({
            "updateTextStyle": {
                "range": {
                    "startIndex": start_index + match.start(),
                    "endIndex": start_index + match.start() + len(email),
                },
                "textStyle": {"link": {"url": f"mailto:{email}"}},
                "fields": "link",
            }
        })
    # Phones
    for match in PHONE_REGEX.finditer(text):
        phone = match.group()
        # Clean dialable number (keep only + and digits)
        dial_link = "+" + "".join(c for c in phone if c.isdigit())
        requests.append({
            "updateTextStyle": {
                "range": {
                    "startIndex": start_index + match.start(),
                    "endIndex": start_index + match.start() + len(phone),
                },
                "textStyle": {"link": {"url": f"tel:{dial_link}"}},
                "fields": "link",
            }
        })
    return requests


def get_heading_level(item: dict[str, Any]) -> int | None:
    para = item.get("paragraph")
    if not para:
        return None
    named = (para.get("paragraphStyle") or {}).get("namedStyleType") or ""
    named = named.upper()
    if named == "HEADING_1":
        return 1
    if named == "HEADING_2":
        return 2
    if named == "HEADING_3":
        return 3
    if named.startswith("HEADING_"):
        try:
            level = int(named.split("_", 1)[1])
            return max(1, min(6, level))
        except ValueError:
            return None
    return None


def is_blank_paragraph(item: dict[str, Any]) -> bool:
    text = get_paragraph_text(item)
    return not text


def find_section_range(content: list[dict[str, Any]], heading_text: str, level: int = 2) -> tuple[int, int] | None:
    section_start_index = None
    for item in content:
        if not item.get("paragraph"):
            continue
        h_level = get_heading_level(item) or 0
        text = get_paragraph_text(item)
        
        # Match by level if specified, or by any non-zero level if level=0 (flexible search)
        match = False
        if level > 0:
            match = (h_level == level and heading_text.lower() in text.lower())
        else:
            # Flexible search: look for the text in any paragraph, preferring headers or just matching text
            match = (heading_text.lower() == text.lower().strip())
            
        if match:
            section_start_index = item.get("endIndex")
            continue
            
        if section_start_index is not None and h_level > 0 and h_level <= (level if level > 0 else 2):
            return section_start_index, item.get("startIndex")
            
    if section_start_index is not None:
        return section_start_index, content[-1].get("endIndex") or 0
    return None


def collect_paragraphs(content: list[dict[str, Any]], start: int, end: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in content:
        if not item.get("paragraph"):
            continue
        item_start = item.get("startIndex") or 0
        item_end = item.get("endIndex") or 0
        if item_start < start or item_end > end:
            continue
        out.append({"item": item, "start": item_start, "end": item_end, "text": get_paragraph_text(item)})
    return out


def split_blocks(paragraphs: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for para in paragraphs:
        if not para["text"]:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(para)
    if current:
        blocks.append(current)
    return blocks


def collect_list_ids(content: list[dict[str, Any]], start: int, end: int) -> set[str]:
    list_ids: set[str] = set()
    for item in content:
        if not item.get("paragraph"):
            continue
        item_start = item.get("startIndex") or 0
        item_end = item.get("endIndex") or 0
        if item_start < start or item_end > end:
            continue
        bullet = item["paragraph"].get("bullet") or {}
        list_id = bullet.get("listId")
        if list_id:
            list_ids.add(list_id)
    return list_ids


def style_skills_section(doc: dict[str, Any], start: int, end: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bullet_requests: list[dict[str, Any]] = []
    style_requests: list[dict[str, Any]] = []
    content = (doc.get("body") or {}).get("content") or []
    paragraphs = collect_paragraphs(content, start, end)
    paragraphs = collect_paragraphs(content, start, end)
    if not paragraphs:
        return [], []
    bullet_paragraphs: list[dict[str, Any]] = []
    blocks = split_blocks(paragraphs)
    for block in blocks:
        if not block:
            continue
        title = block[0]
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": title["start"], "endIndex": title["end"]},
                "paragraphStyle": {
                    "namedStyleType": "HEADING_3",
                    "spaceAbove": {"magnitude": 6, "unit": "PT"},
                    "spaceBelow": {"magnitude": 2, "unit": "PT"},
                },
                "fields": "namedStyleType,spaceAbove,spaceBelow",
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": title["start"], "endIndex": title["end"]},
                "textStyle": {"bold": True},
                "fields": "bold",
            }
        })
        
        # Collect consecutive bullets in this block
        block_bullets: list[dict[str, Any]] = []
        for para in block[1:]:
            # Be more flexible with marker matching (allow spaces)
            if para["text"].strip().startswith(SKILL_BULLET_MARKER.strip()):
                bullet_paragraphs.append(para)
                block_bullets.append(para)
            elif block_bullets: # If we already hit a non-bullet line, process what we have
                pass 
                
        if block_bullets:
            # Group consecutive bullets for styling
            # Apply bullets FIRST to establish the list
            bullet_requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": block_bullets[0]["start"], "endIndex": block_bullets[-1]["end"]},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })

            # THEN override indentation
            for para in block_bullets:
                style_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": para["start"], "endIndex": para["end"]},
                    "paragraphStyle": {
                        "indentStart": {"magnitude": 20, "unit": "PT"},
                        "indentFirstLine": {"magnitude": 0, "unit": "PT"},
                        "spaceAbove": {"magnitude": 2, "unit": "PT"},
                        "spaceBelow": {"magnitude": 2, "unit": "PT"},
                    },
                    "fields": "indentStart,indentFirstLine,spaceAbove,spaceBelow",
                }
            })
    return bullet_requests, style_requests


def style_experience_section(doc: dict[str, Any], start: int, end: int, bullet_marker: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bullet_requests: list[dict[str, Any]] = []
    style_requests: list[dict[str, Any]] = []
    content = (doc.get("body") or {}).get("content") or []
    paragraphs = collect_paragraphs(content, start, end)
    if not paragraphs:
        return [], []
    bullet_paragraphs: list[dict[str, Any]] = []
    blocks = split_blocks(paragraphs)
    for block in blocks:
        if not block:
            continue
        idx = 0
        title = block[0]
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": title["start"], "endIndex": title["end"]},
                "paragraphStyle": {
                    "namedStyleType": "HEADING_3",
                    "spaceAbove": {"magnitude": 14, "unit": "PT"},
                    "spaceBelow": {"magnitude": 2, "unit": "PT"},
                },
                "fields": "namedStyleType,spaceAbove,spaceBelow",
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": title["start"], "endIndex": title["end"]},
                "textStyle": {"bold": True},
                "fields": "bold",
            }
        })
        idx += 1
        description_paras = []
        url_para = None
        role_para = None
        tech_para = None
        block_bullets: list[dict[str, Any]] = []
        while idx < len(block):
            para = block[idx]
            next_para = block[idx + 1] if (idx + 1) < len(block) else None
            text_strip = para["text"].strip()
            text_lower = text_strip.lower()
            
            if text_strip.startswith(bullet_marker.strip()):
                block_bullets.append(para)
            elif text_strip.startswith("http"):
                url_para = para
            elif any(text_lower.startswith(prefix) for prefix in TECH_PREFIXES):
                tech_para = para
            else:
                next_is_bullet = next_para and next_para["text"].strip().startswith(bullet_marker.strip())
                if role_para is None and next_is_bullet:
                    role_para = para
                else:
                    description_paras.append(para)
            idx += 1
            
        if role_para is None and description_paras:
            role_para = description_paras.pop()
            
        for para in description_paras:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": para["start"], "endIndex": para["end"]},
                    "textStyle": {"italic": True},
                    "fields": "italic",
                }
            })
            
        if url_para:
            url_text = url_para["text"].strip()
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": url_para["start"], "endIndex": url_para["end"]},
                    "textStyle": {"italic": True, "link": {"url": url_text}},
                    "fields": "italic,link",
                }
            })
            
        if role_para:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": role_para["start"], "endIndex": role_para["end"]},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })
            
        if tech_para:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": tech_para["start"], "endIndex": tech_para["end"]},
                    "textStyle": {
                        "italic": True,
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}},
                    },
                    "fields": "italic,foregroundColor",
                }
            })
            # Add extra space after tech line to separate blocks
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": tech_para["start"], "endIndex": tech_para["end"]},
                    "paragraphStyle": {"spaceBelow": {"magnitude": 12, "unit": "PT"}},
                    "fields": "spaceBelow",
                }
            })
        elif block:
            # If no tech para, add space to the last para of the block
            last_para = block[-1]
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": last_para["start"], "endIndex": last_para["end"]},
                    "paragraphStyle": {"spaceBelow": {"magnitude": 12, "unit": "PT"}},
                    "fields": "spaceBelow",
                }
            })
        
        if block_bullets:
            # Apply bullets FIRST
            bullet_requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": block_bullets[0]["start"], "endIndex": block_bullets[-1]["end"]},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })

            # THEN override indentation
            for para in block_bullets:
                style_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": para["start"], "endIndex": para["end"]},
                    "paragraphStyle": {
                        "indentStart": {"magnitude": 20, "unit": "PT"},
                        "indentFirstLine": {"magnitude": 0, "unit": "PT"},
                        "spaceAbove": {"magnitude": 2, "unit": "PT"},
                        "spaceBelow": {"magnitude": 2, "unit": "PT"},
                    },
                    "fields": "indentStart,indentFirstLine,spaceAbove,spaceBelow",
                }
            })
    return bullet_requests, style_requests


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def needs_reauth(output: str) -> bool:
    return "invalid_grant" in output or "Token has been expired or revoked" in output


def apply_with_auto_auth(
    *,
    doc: str,
    data_path: str,
    gdocs_cli: str,
    match_case: bool,
    dry_run: bool,
    auto_auth: bool,
    client: str | None,
    token: str | None,
) -> None:
    cmd = [sys.executable, gdocs_cli, "apply", "--doc", doc, "--data", data_path]
    if match_case:
        cmd.append("--match-case")
    if dry_run:
        cmd.append("--dry-run")

    first = run_cmd(cmd)
    if first.stdout:
        sys.stdout.write(first.stdout)
    if first.stderr:
        sys.stderr.write(first.stderr)
    if first.returncode == 0:
        return

    combined = (first.stdout or "") + (first.stderr or "")
    if not auto_auth or not needs_reauth(combined):
        raise SystemExit(f"gdocs_cli apply failed with exit code {first.returncode}")

    auth_cmd = [
        sys.executable,
        gdocs_cli,
        "auth",
        "--scopes",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    if client:
        auth_cmd.extend(["--client", client])
    if token:
        auth_cmd.extend(["--token", token])
    auth = run_cmd(auth_cmd)
    if auth.stdout:
        sys.stdout.write(auth.stdout)
    if auth.stderr:
        sys.stderr.write(auth.stderr)
    if auth.returncode != 0:
        raise SystemExit(f"gdocs_cli auth failed with exit code {auth.returncode}")

    retry = run_cmd(cmd)
    if retry.stdout:
        sys.stdout.write(retry.stdout)
    if retry.stderr:
        sys.stderr.write(retry.stderr)
    if retry.returncode != 0:
        raise SystemExit(f"gdocs_cli apply failed after auth (exit code {retry.returncode})")


def get_doc_text(
    *,
    doc: str,
    gdocs_cli: str,
    auto_auth: bool,
) -> str:
    cmd = [sys.executable, gdocs_cli, "print", "--doc", doc, "--format", "plain"]
    first = run_cmd(cmd)
    if first.stderr:
        sys.stderr.write(first.stderr)
    if first.returncode == 0:
        return (first.stdout or "")

    combined = (first.stdout or "") + (first.stderr or "")
    if not auto_auth or not needs_reauth(combined):
        raise SystemExit(f"gdocs_cli print failed with exit code {first.returncode}")

    auth_cmd = [
        sys.executable,
        gdocs_cli,
        "auth",
        "--scopes",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    auth = run_cmd(auth_cmd)
    if auth.stdout:
        sys.stdout.write(auth.stdout)
    if auth.stderr:
        sys.stderr.write(auth.stderr)
    if auth.returncode != 0:
        raise SystemExit(f"gdocs_cli auth failed with exit code {auth.returncode}")

    retry = run_cmd(cmd)
    if retry.returncode != 0:
        if retry.stderr:
            sys.stderr.write(retry.stderr)
        raise SystemExit(f"gdocs_cli print failed after auth (exit code {retry.returncode})")
    return (retry.stdout or "")


def strip_print_header(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("====="):
            continue
        lines.append(line)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Apply structured CV JSON to template placeholders.")
    parser.add_argument("--data", help="Path to structured CV JSON")
    parser.add_argument("--out", help="Where to write replacements JSON (optional)")
    parser.add_argument("--doc", help="Google Doc name to update (optional)")
    parser.add_argument(
        "--gdocs-cli",
        default=os.path.join(ROOT_DIR, "scripts", "gdocs_cli.py"),
        help="Path to gdocs_cli.py",
    )
    parser.add_argument(
        "--links-file",
        default=os.path.join(ROOT_DIR, "docs", "resources", "GOOGLE_DOCS_LINKS.md"),
        help="Path to Google Docs links file",
    )
    parser.add_argument(
        "--client",
        default=os.environ.get("GDOCS_OAUTH_CLIENT", ".secrets/google-oauth-client.json"),
        help="OAuth client JSON (default: .secrets/google-oauth-client.json or $GDOCS_OAUTH_CLIENT)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GDOCS_TOKEN", ".secrets/google-token.json"),
        help="Path to token cache (default: .secrets/google-token.json or $GDOCS_TOKEN)",
    )
    parser.add_argument("--match-case", action="store_true", help="Match case when replacing placeholders")
    parser.add_argument("--dry-run", action="store_true", help="Print requests JSON without changing the document")
    parser.add_argument("--reset", action="store_true", help="Reset document back to last applied anchors")
    parser.add_argument("--state-file", default=".cv_apply_state.json", help="Path to apply state JSON")
    parser.add_argument(
        "--auto-auth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Re-run OAuth auth if the token is expired or revoked (default: true)",
    )
    args = parser.parse_args(argv)

    if args.reset:
        if not args.doc:
            raise SystemExit("--reset requires --doc")
        state = read_state(args.state_file)
        doc_state = (state.get("docs") or {}).get(args.doc)
        if not doc_state:
            raise SystemExit(f"No saved state for doc {args.doc!r} in {args.state_file}")
        stored_replacements = doc_state.get("cleaned_replacements") or doc_state.get("replacements")
        if not isinstance(stored_replacements, dict):
            raise SystemExit(f"Invalid stored replacements for doc {args.doc!r}")
        inverted, collisions, skipped = invert_replacements(stored_replacements)
        if not inverted:
            raise SystemExit("No stored text to reset.")

        log_line("♻️ Reset mode enabled")
        log_line(f"📄 Target doc: {args.doc}")
        saved_doc_url = doc_state.get("doc_url")
        saved_doc_id = doc_state.get("doc_id")
        link_url, link_id = (None, None)
        if not saved_doc_url or not saved_doc_id:
            link_url, link_id = find_doc_info(args.links_file, args.doc)
        doc_url = saved_doc_url or link_url
        doc_id = saved_doc_id or link_id
        if doc_url:
            log_line(f"🔗 Target link: {doc_url}")
        if doc_id:
            log_line(f"🆔 Document ID: {doc_id}")
        if skipped:
            log_line(f"⚠️ Skipped empty blocks (cannot reset): {skipped}")
        if collisions:
            log_line("⚠️ Reset collisions (duplicate content strings):")
            for value in collisions:
                log_line(f"  - {value}")

        access_token = ensure_access_token(client=load_oauth_client(args.client), token_path=args.token)
        log_line("🚀 Scanning document for reset...")
        doc = get_doc(document_id=doc_id, access_token=access_token)
        
        # Segment-aware processing (Body + Headers + Footers)
        segments = [ (doc.get("body", {}).get("content", []), None) ]
        for hid, h in doc.get("headers", {}).items():
            segments.append((h.get("content", []), hid))
        for fid, f in doc.get("footers", {}).items():
            segments.append((f.get("content", []), fid))

        segment_terminal_indices = {} # seg_id -> set of terminal indices
        all_matches = []
        processed_anchors = set()
        
        # Landmarks for major blocks
        block_landmarks = {
            "{{SUMMARY}}": "Summary",
            "{{skills}}": "Skills",
            "{{exps}}": "Experience",
            "{{entrepreneurship}}": "Entrepreneurship",
            "{{education}}": "Education",
            "{{publications}}": "Publications",
        }
        
        for seg_content, seg_id in segments:
            term_idx = seg_content[-1].get("endIndex") or 0 if seg_content else 0
            segment_terminal_indices[seg_id] = term_idx
            
            # 1. Landmark-based reset for major blocks
            for anchor, header in block_landmarks.items():
                if anchor in processed_anchors: continue
                if anchor not in stored_replacements: continue
                
                r = find_section_range(seg_content, header, level=2)
                if not r:
                    r = find_section_range(seg_content, header, level=0)
                if r:
                    all_matches.append((r[0], r[1], anchor, seg_id))
                    processed_anchors.add(anchor)
                    log_line(f"📍 Found block landmark for {anchor} in {'Body' if not seg_id else seg_id}")

        # 2. Regex for remaining fields
        remaining_inverted = {v: k for k, v in stored_replacements.items() if k not in processed_anchors and v and isinstance(v, str)}
        
        if remaining_inverted:
            for seg_content, seg_id in segments:
                doc_text = ""
                index_map = []
                for item in iter_all_paragraphs(seg_content):
                    for element in item.get("paragraph", {}).get("elements", []):
                        tr = element.get("textRun", {})
                        if tr:
                            start = element.get("startIndex") or 0
                            run_text = tr.get("content", "")
                            for i, char in enumerate(run_text):
                                doc_text += char
                                index_map.append(start + i)
                
                if not doc_text: continue
                
                for text_to_find, anchor in sorted(remaining_inverted.items(), key=lambda x: len(x[0]), reverse=True):
                    if not text_to_find.strip(): continue
                    
                    use_boundaries = len(text_to_find) < 10 and ' ' not in text_to_find
                    regex_text = re.escape(text_to_find)
                    if use_boundaries:
                        regex_text = rf"\b{regex_text}\b"
                    
                    for m in re.finditer(regex_text, doc_text):
                        g_start = index_map[m.start()]
                        if m.end() < len(index_map):
                            g_end = index_map[m.end()]
                        else:
                            g_end = index_map[m.end()-1] + 1
                        all_matches.append((g_start, g_end, anchor, seg_id))

        if not all_matches:
            log_line("ℹ️ No content found to reset.")
            return 0

        # Sort matches by startIndex DESCENDING (within segments) to avoid indices shifting
        all_matches.sort(key=lambda x: (x[1], -x[0]), reverse=True)
        
        requests = []
        applied_count = 0
        pushed_ranges = {} # seg_id -> list of (s, e)
        
        for s, e, anchor, seg_id in all_matches:
            if s >= e: continue
            
            # Check terminal newline restriction: GDocs doesn't allow deleting the very last newline of a segment
            term_idx = segment_terminal_indices.get(seg_id)
            if term_idx is not None and e >= term_idx:
                e = term_idx - 1
            if s >= e: continue
            
            # Check overlap
            if seg_id not in pushed_ranges: pushed_ranges[seg_id] = []
            overlap = False
            for ps, pe in pushed_ranges[seg_id]:
                if (s < pe and e > ps):
                    overlap = True
                    break
            if overlap: continue

            # Clear Paragraph Style (Normal Text) and character overrides ONLY for block landmarks
            # This prevents destroying H1/H3 styles of header fields during reset.
            if anchor in block_landmarks:
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": s, "endIndex": e, "segmentId": seg_id},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "fields": "namedStyleType"
                    }
                })
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": s, "endIndex": e, "segmentId": seg_id},
                        "textStyle": {"bold": False, "italic": False, "fontSize": {"magnitude": 11, "unit": "PT"}},
                        "fields": "bold,italic,fontSize"
                    }
                })
            
            requests.append({
                "deleteContentRange": {
                    "range": {"startIndex": s, "endIndex": e, "segmentId": seg_id}
                }
            })
            
            text_to_insert = anchor
            if anchor in block_landmarks:
                text_to_insert += "\n"
                
            requests.append({
                "insertText": {
                    "location": {"index": s, "segmentId": seg_id},
                    "text": text_to_insert
                }
            })
            
            # Ensure the inserted anchor ITSELF is Normal Text
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": s, "endIndex": s + len(text_to_insert), "segmentId": seg_id},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType"
                }
            })
            
            pushed_ranges[seg_id].append((s, e))
            applied_count += 1
                
        if requests:
            docs_batch_update(document_id=doc_id, access_token=access_token, requests=requests)
            log_line(f"✅ Reset complete. Reverted {applied_count} anchors.")
        else:
            log_line("ℹ️ Nothing to reset.")
        return 0

    if not args.data:
        raise SystemExit("--data is required unless --reset is set")

    data = read_json(args.data)
    if not isinstance(data, dict):
        raise SystemExit("Structured CV data must be a JSON object.")

    replacements = build_replacements(data)
    payload = {"replacements": replacements}

    should_log = bool(args.out or args.doc)

    if should_log:
        log_line("🧾 Loaded structured data")
        log_line(f"📦 Data file: {args.data}")
        log_line(f"🧩 Total placeholders: {len(replacements)}")

    tmp_path = None
    out_path = args.out
    if out_path:
        write_json(out_path, payload)
        if should_log:
            log_line(f"📝 Replacements JSON written: {out_path}")
    elif args.doc:
        fd, tmp_path = tempfile.mkstemp(prefix="cv_replacements_", suffix=".json")
        os.close(fd)
        write_json(tmp_path, payload)
        out_path = tmp_path
        if should_log:
            log_line(f"📝 Replacements JSON (temp): {out_path}")
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.doc:
        doc_url, doc_id = find_doc_info(args.links_file, args.doc)
        log_line(f"📄 Target doc: {args.doc}")
        if doc_url:
            log_line(f"🔗 Target link: {doc_url}")
        else:
            log_line(f"🔗 Target link: not found in {args.links_file}")
        if doc_id:
            log_line(f"🆔 Document ID: {doc_id}")
        else:
            log_line("🆔 Document ID: unknown")

        raw_text = get_doc_text(doc=args.doc, gdocs_cli=args.gdocs_cli, auto_auth=args.auto_auth)
        doc_text = strip_print_header(raw_text)
        doc_placeholders = extract_placeholders(doc_text)
        repl_keys = set(replacements.keys())
        applied = sorted(repl_keys & doc_placeholders)
        missing = sorted(repl_keys - doc_placeholders)
        extras = sorted(doc_placeholders - repl_keys)

        log_line(f"🧷 Placeholders in doc: {len(doc_placeholders)}")
        log_line(f"✅ Will apply: {len(applied)}")
        if applied:
            log_line("✅ Applied anchors list:")
            for key in applied:
                log_line(f"  - {key}")
        if missing:
            log_line("⚠️ Missing in document (no match):")
            for key in missing:
                log_line(f"  - {key}")
        if extras:
            log_line("ℹ️ Present in document but not provided:")
            for key in extras:
                log_line(f"  - {key}")

        log_line("🚀 Applying replacements...")
        apply_with_auto_auth(
            doc=args.doc,
            data_path=out_path,
            gdocs_cli=args.gdocs_cli,
            match_case=args.match_case,
            dry_run=args.dry_run,
            auto_auth=args.auto_auth,
            client=args.client,
            token=args.token,
        )
        if not args.dry_run and not args.reset:
            apply_block_styles(doc_id=doc_id, client_path=args.client, token_path=args.token, replacements=replacements)
        update_state(
            state_path=args.state_file,
            doc=args.doc,
            doc_url=doc_url,
            doc_id=doc_id,
            data_path=args.data,
            replacements=replacements,
        )
        log_line(f"💾 State saved: {args.state_file}")
        log_line("✅ Done.")

    if tmp_path:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
