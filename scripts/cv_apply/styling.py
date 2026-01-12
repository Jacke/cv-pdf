"""Document styling operations for Google Docs."""

import time
from typing import Any

from .constants import (
    SKILL_BULLET_MARKER,
    EXP_BULLET_MARKER,
    TECH_PREFIXES,
    SECTION_HEADERS,
    TIGHT_ANCHORS,
    BLOCK_LANDMARKS,
)
from .document import (
    iter_all_paragraphs,
    get_paragraph_text,
    get_raw_paragraph_text,
    get_heading_level,
    find_section_range,
    collect_paragraphs,
    split_blocks,
    create_link_requests,
)
from .utils import log_line


def style_skills_section(
    doc: dict[str, Any],
    start: int,
    end: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Generate styling requests for the Skills section.

    Returns:
        Tuple of (bullet_requests, style_requests)
    """
    bullet_requests: list[dict[str, Any]] = []
    style_requests: list[dict[str, Any]] = []
    content = (doc.get("body") or {}).get("content") or []
    paragraphs = collect_paragraphs(content, start, end)

    if not paragraphs:
        return [], []

    blocks = split_blocks(paragraphs)
    for block in blocks:
        if not block:
            continue

        # First line is the skill category title
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

        # Collect bullet points
        block_bullets: list[dict[str, Any]] = []
        for para in block[1:]:
            if para["text"].strip().startswith(SKILL_BULLET_MARKER.strip()):
                block_bullets.append(para)

        if block_bullets:
            # Apply bullets first
            bullet_requests.append({
                "createParagraphBullets": {
                    "range": {
                        "startIndex": block_bullets[0]["start"],
                        "endIndex": block_bullets[-1]["end"]
                    },
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })

            # Then override indentation
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


def style_experience_section(
    doc: dict[str, Any],
    start: int,
    end: int,
    bullet_marker: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Generate styling requests for Experience/Entrepreneurship sections.

    Returns:
        Tuple of (bullet_requests, style_requests)
    """
    bullet_requests: list[dict[str, Any]] = []
    style_requests: list[dict[str, Any]] = []
    content = (doc.get("body") or {}).get("content") or []
    paragraphs = collect_paragraphs(content, start, end)

    if not paragraphs:
        return [], []

    blocks = split_blocks(paragraphs)
    for block in blocks:
        if not block:
            continue

        idx = 0
        # First line is company/dates
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

        # Classify remaining paragraphs
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

        # If no role found, use last description line as role
        if role_para is None and description_paras:
            role_para = description_paras.pop()

        # Style description paragraphs as italic
        for para in description_paras:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": para["start"], "endIndex": para["end"]},
                    "textStyle": {"italic": True},
                    "fields": "italic",
                }
            })

        # Style URL paragraph
        if url_para:
            url_text = url_para["text"].strip()
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": url_para["start"], "endIndex": url_para["end"]},
                    "textStyle": {"italic": True, "link": {"url": url_text}},
                    "fields": "italic,link",
                }
            })

        # Style role paragraph as bold
        if role_para:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": role_para["start"], "endIndex": role_para["end"]},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })

        # Style tech paragraph
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
            # Add extra space after tech line
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": tech_para["start"], "endIndex": tech_para["end"]},
                    "paragraphStyle": {"spaceBelow": {"magnitude": 12, "unit": "PT"}},
                    "fields": "spaceBelow",
                }
            })
        elif block:
            # If no tech para, add space to last para of block
            last_para = block[-1]
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": last_para["start"], "endIndex": last_para["end"]},
                    "paragraphStyle": {"spaceBelow": {"magnitude": 12, "unit": "PT"}},
                    "fields": "spaceBelow",
                }
            })

        # Apply bullets
        if block_bullets:
            bullet_requests.append({
                "createParagraphBullets": {
                    "range": {
                        "startIndex": block_bullets[0]["start"],
                        "endIndex": block_bullets[-1]["end"]
                    },
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })

            # Override indentation
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


def apply_block_styles(
    *,
    doc_id: str | None,
    client_path: str,
    token_path: str,
    replacements: dict[str, str] | None = None,
) -> None:
    """
    Apply styling to CV document sections.

    Args:
        doc_id: Google Doc ID
        client_path: Path to OAuth client credentials
        token_path: Path to token cache
        replacements: Placeholder replacements for reverse lookup
    """
    if not doc_id:
        log_line("⚠️ Cannot style blocks: document ID unknown.")
        return

    # Import here to avoid circular dependency
    import sys
    import os
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, ROOT_DIR)
    from gdocs_cli import docs_batch_update, ensure_access_token, get_doc, load_oauth_client

    client = load_oauth_client(client_path)
    access_token = ensure_access_token(client=client, token_path=token_path)
    doc = get_doc(document_id=doc_id, access_token=access_token)
    content = (doc.get("body") or {}).get("content") or []
    requests: list[dict[str, Any]] = []

    # Style section headers as H2
    for header_text in SECTION_HEADERS:
        for item in content:
            if not item.get("paragraph"):
                continue
            text = get_paragraph_text(item).lower().strip()
            if header_text.lower() == text:
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": item.get("startIndex"), "endIndex": item.get("endIndex")},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                })
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": item.get("startIndex"), "endIndex": item.get("endIndex")},
                        "textStyle": {"bold": True, "fontSize": {"magnitude": 17, "unit": "PT"}},
                        "fields": "bold,fontSize",
                    }
                })
                break

    # Style Skills section
    skills_range = find_section_range(content, "Skills", level=2) or find_section_range(content, "Skills", level=0)
    if skills_range:
        bullets, styles = style_skills_section(doc, *skills_range)
        requests.extend(bullets)
        requests.extend(styles)

    # Style Experience section
    exp_range = find_section_range(content, "Experience", level=2) or find_section_range(content, "Experience", level=0)
    if exp_range:
        bullets, styles = style_experience_section(doc, *exp_range, bullet_marker=EXP_BULLET_MARKER)
        requests.extend(bullets)
        requests.extend(styles)

    # Style Entrepreneurship section
    ent_range = find_section_range(content, "Entrepreneurship", level=2) or find_section_range(content, "Entrepreneurship", level=0)
    if ent_range:
        bullets, styles = style_experience_section(doc, *ent_range, bullet_marker=EXP_BULLET_MARKER)
        requests.extend(bullets)
        requests.extend(styles)

    # Style Education section
    edu_range = find_section_range(content, "Education", level=2) or find_section_range(content, "Education", level=0)
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

    # Auto-linkify and fix heading styles
    for item in iter_all_paragraphs(content):
        text = get_raw_paragraph_text(item)
        para_start = item.get("startIndex") or 0
        para_end = item.get("endIndex")

        # Restore field-specific styles
        anchor = inverted.get(text.strip())

        if anchor in TIGHT_ANCHORS:
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

        # Enforce H2 style for designated headers
        is_h2 = get_heading_level(item) == 2
        clean_text = text.strip().lower()
        if is_h2 and clean_text in [h.lower() for h in SECTION_HEADERS]:
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": para_start, "endIndex": para_end},
                    "textStyle": {"bold": True, "fontSize": {"magnitude": 17, "unit": "PT"}},
                    "fields": "bold,fontSize",
                }
            })
        elif is_h2 and ("{{" in text or len(text) > 40):
            # Revert non-header H2 back to Normal Text
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

    # Split into bullet creation and style requests
    bullet_requests = [req for req in requests if "createParagraphBullets" in req]
    style_requests = [req for req in requests if "createParagraphBullets" not in req]

    # Phase 1: Create bullets
    if bullet_requests:
        docs_batch_update(document_id=doc_id, access_token=access_token, requests=bullet_requests)
        log_line(f"🎨 Applied {len(bullet_requests)} bullet creation requests.")
        time.sleep(2)  # Wait for bullets to register

    # Phase 2: Apply styles
    if style_requests:
        log_line(f"📝 Applying {len(style_requests)} style requests...")
        docs_batch_update(document_id=doc_id, access_token=access_token, requests=style_requests)
        log_line(f"🎨 Applied {len(style_requests)} styling requests.")

    # Cleanup: Remove bullet markers
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
