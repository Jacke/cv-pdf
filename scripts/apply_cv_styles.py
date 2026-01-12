#!/usr/bin/env python3
"""
Применение профессиональных стилей к CV в Google Docs через API.

Использует Google Docs API batchUpdate для прямого форматирования:
- updateParagraphStyle: фоны, рамки, отступы
- updateTextStyle: bold, italic, цвета, размер шрифта

Стилизуемые секции:
- Skills: серый фон + синяя левая рамка
- Experience: верхняя рамка-разделитель
- Education: светлый фон
"""
from __future__ import annotations

import argparse
import sys
import os
from typing import Any

# Add parent directory to path to import gdocs_cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gdocs_cli import (
    ensure_access_token,
    load_oauth_client,
    get_doc,
    docs_batch_update,
    parse_doc_links,
    read_text,
)


# === ЦВЕТОВАЯ ПАЛИТРА ===
COLORS = {
    "accent_blue": (0.290, 0.565, 0.886),    # #4A90E2
    "text_dark": (0.102, 0.102, 0.102),      # #1A1A1A
    "text_gray": (0.400, 0.400, 0.400),      # #666666
    "text_light_gray": (0.533, 0.533, 0.533),# #888888
    "border_gray": (0.878, 0.878, 0.878),    # #E0E0E0
    "bg_gray_1": (0.973, 0.976, 0.980),      # #F8F9FA (Skills)
    "bg_gray_2": (0.961, 0.961, 0.961),      # #F5F5F5 (Education)
}


# === HELPER FUNCTIONS ===

def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    """Создать RgbColor объект для Google Docs API."""
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}


def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    """Создать Dimension объект."""
    return {"magnitude": magnitude, "unit": unit}


def border(color_rgb: tuple[float, float, float], width: float = 2.0,
           padding: float = 8.0, dash_style: str = "SOLID") -> dict[str, Any]:
    """Создать ParagraphBorder объект."""
    return {
        "color": rgb_color(*color_rgb),
        "width": dimension(width),
        "padding": dimension(padding),
        "dashStyle": dash_style,
    }


# === DOCUMENT PARSING ===

def get_paragraph_text(para: dict[str, Any]) -> str:
    """Получить весь текст из параграфа."""
    elements = para.get("paragraph", {}).get("elements", [])
    text_parts = []
    for elem in elements:
        text_run = elem.get("textRun")
        if text_run:
            text_parts.append(text_run.get("content", ""))
    return "".join(text_parts)


def get_heading_level(para: dict[str, Any]) -> int | None:
    """Получить уровень заголовка (1-6) или None."""
    style = para.get("paragraph", {}).get("paragraphStyle", {})
    named_style = style.get("namedStyleType", "")

    if named_style == "HEADING_1":
        return 1
    elif named_style == "HEADING_2":
        return 2
    elif named_style == "HEADING_3":
        return 3
    elif named_style == "HEADING_4":
        return 4
    elif named_style == "HEADING_5":
        return 5
    elif named_style == "HEADING_6":
        return 6

    return None


def is_bullet_paragraph(para: dict[str, Any]) -> bool:
    """Проверить, является ли параграф bullet list item."""
    return para.get("paragraph", {}).get("bullet") is not None


def find_section_by_heading(content: list[dict[str, Any]], heading_text: str,
                            level: int = 2) -> tuple[int, int] | None:
    """
    Найти секцию по заголовку.

    Возвращает (start_index, end_index) секции или None.
    Секция начинается с заголовка и заканчивается перед следующим заголовком того же или выше уровня.
    """
    section_start_idx = None
    section_start = None

    for idx, item in enumerate(content):
        if item.get("paragraph"):
            h_level = get_heading_level(item)
            text = get_paragraph_text(item).strip()

            # Нашли искомый заголовок
            if h_level == level and heading_text.lower() in text.lower():
                section_start_idx = idx
                section_start = item.get("startIndex")
                continue

            # Нашли конец секции (следующий заголовок того же или выше уровня)
            if section_start_idx is not None and h_level is not None and h_level <= level:
                section_end = item.get("startIndex")
                return (section_start, section_end)

    # Секция идёт до конца документа
    if section_start_idx is not None:
        last_item = content[-1]
        section_end = last_item.get("endIndex")
        return (section_start, section_end)

    return None


# === СТИЛИЗАЦИЯ СЕКЦИЙ ===

def style_skills_blocks(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Найти и стилизовать блоки Skills (параграфы с bullet'ами под tech заголовками).

    Применяет:
    - Серый фон (#F8F9FA)
    - Синяя левая рамка (#4A90E2, 2pt)
    - Отступ слева 12pt
    - Spacing 4pt до/после

    Возвращает список updateParagraphStyle запросов.
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    # Найти секцию Skills
    skills_range = find_section_by_heading(content, "Skills", level=2)
    if not skills_range:
        print("  [SKIP] Skills section not found")
        return requests

    skills_start, skills_end = skills_range
    print(f"  [FOUND] Skills section: {skills_start} - {skills_end}")

    # Найти все bullet параграфы в Skills секции
    bullet_count = 0
    for item in content:
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            # Проверяем, что параграф в пределах Skills секции
            if start >= skills_start and end <= skills_end:
                if is_bullet_paragraph(item):
                    bullet_count += 1
                    requests.append({
                        "updateParagraphStyle": {
                            "paragraphStyle": {
                                "shading": {"backgroundColor": rgb_color(*COLORS["bg_gray_1"])},
                                "borderLeft": border(COLORS["accent_blue"], width=2.0),
                                "indentStart": dimension(12.0),
                                "spaceAbove": dimension(4.0),
                                "spaceBelow": dimension(4.0),
                            },
                            "range": {"startIndex": start, "endIndex": end},
                            "fields": "shading.backgroundColor,borderLeft,indentStart,spaceAbove,spaceBelow",
                        }
                    })

    print(f"  [OK] Found {bullet_count} skill bullet items to style")
    return requests


def style_experience_blocks(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Стилизовать блоки Experience (верхняя рамка, spacing).

    Применяет к H3 заголовкам компаний:
    - Верхняя рамка #E0E0E0, 0.5pt
    - Spacing: 10pt до, 6pt после
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    # Найти секцию Experience
    exp_range = find_section_by_heading(content, "Experience", level=2)
    if not exp_range:
        print("  [SKIP] Experience section not found")
        return requests

    exp_start, exp_end = exp_range
    print(f"  [FOUND] Experience section: {exp_start} - {exp_end}")

    # Найти все H3 в Experience секции (компании)
    company_count = 0
    for item in content:
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            if start >= exp_start and end <= exp_end:
                if get_heading_level(item) == 3:
                    company_count += 1
                    company_name = get_paragraph_text(item).strip()
                    print(f"    [COMPANY] {company_name[:50]}...")

                    requests.append({
                        "updateParagraphStyle": {
                            "paragraphStyle": {
                                "borderTop": border(COLORS["border_gray"], width=0.5),
                                "spaceAbove": dimension(10.0),
                                "spaceBelow": dimension(6.0),
                            },
                            "range": {"startIndex": start, "endIndex": end},
                            "fields": "borderTop,spaceAbove,spaceBelow",
                        }
                    })

    print(f"  [OK] Found {company_count} companies to style")
    return requests


def style_tech_stack(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Стилизовать строки "Tech: ..." (малый шрифт 9pt, серый цвет).
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    # Найти секцию Experience
    exp_range = find_section_by_heading(content, "Experience", level=2)
    if not exp_range:
        return requests

    exp_start, exp_end = exp_range

    # Найти параграфы начинающиеся с "Tech:"
    tech_count = 0
    for item in content:
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            if start >= exp_start and end <= exp_end:
                text = get_paragraph_text(item)
                if text.strip().startswith("Tech:") or text.strip().startswith("Technologies:"):
                    tech_count += 1
                    requests.append({
                        "updateTextStyle": {
                            "textStyle": {
                                "fontSize": dimension(9.0),
                                "foregroundColor": rgb_color(*COLORS["text_light_gray"]),
                            },
                            "range": {"startIndex": start, "endIndex": end - 1},  # -1 чтобы не захватить \n
                            "fields": "fontSize,foregroundColor",
                        }
                    })

    if tech_count > 0:
        print(f"  [OK] Found {tech_count} tech stack lines to style")

    return requests


def style_education_blocks(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Стилизовать блоки Education (светлый фон #F5F5F5).
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    # Найти секцию Education
    edu_range = find_section_by_heading(content, "Education", level=2)
    if not edu_range:
        print("  [SKIP] Education section not found")
        return requests

    edu_start, edu_end = edu_range
    print(f"  [FOUND] Education section: {edu_start} - {edu_end}")

    # Применить фон ко всем параграфам в Education
    para_count = 0
    for item in content:
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            if start >= edu_start and end <= edu_end:
                # Пропускаем сам заголовок Education
                if get_heading_level(item) == 2:
                    continue

                para_count += 1
                requests.append({
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "shading": {"backgroundColor": rgb_color(*COLORS["bg_gray_2"])},
                            "spaceAbove": dimension(5.0),
                            "spaceBelow": dimension(5.0),
                        },
                        "range": {"startIndex": start, "endIndex": end},
                        "fields": "shading.backgroundColor,spaceAbove,spaceBelow",
                    }
                })

    print(f"  [OK] Found {para_count} education paragraphs to style")
    return requests


# === MAIN LOGIC ===

def apply_cv_styles(document_id: str, access_token: str, dry_run: bool = False) -> None:
    """
    Применить все стили к CV документу.
    """
    print(f"\n{'='*60}")
    print(f"Applying CV styles to document: {document_id}")
    print(f"{'='*60}\n")

    # 1. Получить документ
    print("[1/3] Fetching document...")
    doc = get_doc(document_id=document_id, access_token=access_token)
    doc_title = doc.get("title", "Untitled")
    print(f"  Document: {doc_title}")

    # 2. Собрать все запросы стилизации
    print("\n[2/3] Analyzing document structure...")
    requests = []

    print("\n  Styling Skills section...")
    requests.extend(style_skills_blocks(doc))

    print("\n  Styling Experience section...")
    requests.extend(style_experience_blocks(doc))
    requests.extend(style_tech_stack(doc))

    print("\n  Styling Education section...")
    requests.extend(style_education_blocks(doc))

    print(f"\n  Total style requests: {len(requests)}")

    if dry_run:
        print(f"\n[DRY RUN] Would apply {len(requests)} style requests")
        print("\nFirst 3 requests:")
        for i, req in enumerate(requests[:3]):
            print(f"\n  Request {i+1}:")
            import json
            print(json.dumps(req, indent=2))
        return

    # 3. Применить через batchUpdate
    if requests:
        print("\n[3/3] Applying styles via batchUpdate...")
        result = docs_batch_update(
            document_id=document_id,
            access_token=access_token,
            requests=requests
        )
        print(f"  ✓ Applied {len(requests)} style updates")
        print(f"\n{'='*60}")
        print(f"SUCCESS! Document styled: {doc_title}")
        print(f"{'='*60}\n")
    else:
        print("\n[SKIP] No style updates needed")


def resolve_doc_id(name_or_id: str, links_file: str = "GOOGLE_DOCS_LINKS.md") -> str:
    """
    Преобразовать имя документа или ID в ID.

    Если name_or_id выглядит как ID (длинная строка без пробелов), вернуть как есть.
    Иначе искать по имени в GOOGLE_DOCS_LINKS.md.
    """
    # Если похоже на ID (длинная строка без пробелов)
    if len(name_or_id) > 30 and " " not in name_or_id:
        return name_or_id

    # Иначе искать по имени в links файле
    print(f"Searching for document: '{name_or_id}'...")
    try:
        links = parse_doc_links(read_text(links_file))
        by_name = {d.name: d for d in links}

        if name_or_id in by_name:
            doc_id = by_name[name_or_id].document_id
            print(f"  Found: {doc_id}")
            return doc_id
    except FileNotFoundError:
        pass

    raise SystemExit(f"Document not found: '{name_or_id}'. Add it to {links_file} or use document ID directly.")


def main() -> int:
    p = argparse.ArgumentParser(description="Apply CV styles via Google Docs API")
    p.add_argument("--doc", required=True, help="Document ID or name")
    p.add_argument("--dry-run", action="store_true", help="Show what would be done")
    p.add_argument(
        "--client",
        default=os.environ.get("GDOCS_OAUTH_CLIENT", ".secrets/google-oauth-client.json"),
        help="Path to OAuth client JSON",
    )
    p.add_argument(
        "--token",
        default=os.environ.get("GDOCS_TOKEN", ".secrets/google-token.json"),
        help="Path to token cache",
    )
    args = p.parse_args()

    # Получить access token
    client = load_oauth_client(args.client)
    access_token = ensure_access_token(client=client, token_path=args.token)

    # Преобразовать имя/ID в ID
    document_id = resolve_doc_id(args.doc)

    # Применить стили
    apply_cv_styles(document_id, access_token, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
