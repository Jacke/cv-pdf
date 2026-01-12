#!/usr/bin/env python3
"""
Применение тематических стилей к CV в Google Docs через API.

Поддерживает разные темы оформления:
- minimalist: чистый профессиональный стиль
- colorful: с цветными акцентами (фоны, рамки)
"""
from __future__ import annotations

import argparse
import sys
import os
from typing import Any
import importlib.util

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

            # Нашли конец секции
            if section_start_idx is not None and h_level is not None and h_level <= level:
                section_end = item.get("startIndex")
                return (section_start, section_end)

    # Секция идёт до конца документа
    if section_start_idx is not None:
        last_item = content[-1]
        section_end = last_item.get("endIndex")
        return (section_start, section_end)

    return None


# === STYLING WITH THEMES ===

def style_skills_section_with_theme(doc: dict[str, Any], theme: Any) -> list[dict[str, Any]]:
    """
    Стилизовать Skills секцию используя тему.
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

            if start >= skills_start and end <= skills_end:
                if is_bullet_paragraph(item):
                    bullet_count += 1
                    # Использовать функцию темы для стилизации
                    requests.extend(theme.apply_skills_section_style(start, end))

    print(f"  [OK] Found {bullet_count} skill bullet items to style")
    return requests


def style_experience_section_with_theme(doc: dict[str, Any], theme: Any) -> list[dict[str, Any]]:
    """
    Стилизовать Experience секцию используя тему.
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    exp_range = find_section_by_heading(content, "Experience", level=2)
    if not exp_range:
        print("  [SKIP] Experience section not found")
        return requests

    exp_start, exp_end = exp_range
    print(f"  [FOUND] Experience section: {exp_start} - {exp_end}")

    # Найти все H3 в Experience секции (компании)
    company_count = 0
    current_company_start = None

    for idx, item in enumerate(content):
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            if start >= exp_start and end <= exp_end:
                h_level = get_heading_level(item)

                # H3 = начало блока компании
                if h_level == 3:
                    company_count += 1
                    company_name = get_paragraph_text(item).strip()
                    print(f"    [COMPANY] {company_name[:50]}...")

                    current_company_start = start

                    # Применить стиль к заголовку компании
                    requests.extend(theme.apply_experience_block_style(start, end))
                    requests.extend(theme.apply_company_name_style(start, end - 1))

                # Найти строку с ролью и датами (первый параграф после H3)
                elif current_company_start is not None and start > current_company_start:
                    text = get_paragraph_text(item)

                    # Если есть " · " - это строка роли
                    if " · " in text or "·" in text:
                        requests.extend(theme.apply_role_duration_style(start, end - 1))
                        current_company_start = None  # Нашли роль, сбрасываем

    print(f"  [OK] Found {company_count} companies to style")
    return requests


def style_tech_stack_with_theme(doc: dict[str, Any], theme: Any) -> list[dict[str, Any]]:
    """
    Стилизовать строки Tech используя тему.
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    exp_range = find_section_by_heading(content, "Experience", level=2)
    if not exp_range:
        return requests

    exp_start, exp_end = exp_range

    tech_count = 0
    for item in content:
        if item.get("paragraph"):
            start = item.get("startIndex")
            end = item.get("endIndex")

            if start >= exp_start and end <= exp_end:
                text = get_paragraph_text(item)
                if text.strip().startswith("Tech:") or text.strip().startswith("Technologies:"):
                    tech_count += 1
                    requests.extend(theme.apply_tech_stack_style(start, end))

    if tech_count > 0:
        print(f"  [OK] Found {tech_count} tech stack lines to style")

    return requests


def style_education_section_with_theme(doc: dict[str, Any], theme: Any) -> list[dict[str, Any]]:
    """
    Стилизовать Education секцию используя тему.
    """
    requests = []
    content = doc.get("body", {}).get("content", [])

    edu_range = find_section_by_heading(content, "Education", level=2)
    if not edu_range:
        print("  [SKIP] Education section not found")
        return requests

    edu_start, edu_end = edu_range
    print(f"  [FOUND] Education section: {edu_start} - {edu_end}")

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
                requests.extend(theme.apply_education_section_style(start, end))

    print(f"  [OK] Found {para_count} education paragraphs to style")
    return requests


# === MAIN LOGIC ===

def load_theme(theme_name: str) -> Any:
    """Загрузить модуль темы."""
    theme_path = os.path.join(
        os.path.dirname(__file__),
        "themes",
        f"{theme_name}.py"
    )

    if not os.path.exists(theme_path):
        raise SystemExit(f"Theme not found: {theme_name} (expected at {theme_path})")

    spec = importlib.util.spec_from_file_location(f"theme_{theme_name}", theme_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Failed to load theme: {theme_name}")

    theme_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme_module)

    return theme_module


def apply_cv_styles_with_theme(document_id: str, access_token: str,
                               theme_name: str, dry_run: bool = False) -> None:
    """
    Применить стили темы к CV документу.
    """
    # Загрузить тему
    print(f"\nLoading theme: {theme_name}")
    theme = load_theme(theme_name)

    if hasattr(theme, "THEME_INFO"):
        info = theme.THEME_INFO
        print(f"  Name: {info.get('name')}")
        print(f"  Description: {info.get('description')}")

    print(f"\n{'='*60}")
    print(f"Applying '{theme_name}' theme to document: {document_id}")
    print(f"{'='*60}\n")

    # Получить документ
    print("[1/3] Fetching document...")
    doc = get_doc(document_id=document_id, access_token=access_token)
    doc_title = doc.get("title", "Untitled")
    print(f"  Document: {doc_title}")

    # Собрать все запросы стилизации
    print("\n[2/3] Analyzing document structure...")
    requests = []

    print("\n  Styling Skills section...")
    requests.extend(style_skills_section_with_theme(doc, theme))

    print("\n  Styling Experience section...")
    requests.extend(style_experience_section_with_theme(doc, theme))
    requests.extend(style_tech_stack_with_theme(doc, theme))

    print("\n  Styling Education section...")
    requests.extend(style_education_section_with_theme(doc, theme))

    print(f"\n  Total style requests: {len(requests)}")

    if dry_run:
        print(f"\n[DRY RUN] Would apply {len(requests)} style requests")
        if requests:
            print("\nFirst 2 requests:")
            import json
            for i, req in enumerate(requests[:2]):
                print(f"\n  Request {i+1}:")
                print(json.dumps(req, indent=2))
        return

    # Применить через batchUpdate
    if requests:
        print("\n[3/3] Applying styles via batchUpdate...")
        result = docs_batch_update(
            document_id=document_id,
            access_token=access_token,
            requests=requests
        )
        print(f"  ✓ Applied {len(requests)} style updates")
        print(f"\n{'='*60}")
        print(f"SUCCESS! Document styled with '{theme_name}' theme: {doc_title}")
        print(f"{'='*60}\n")
    else:
        print("\n[SKIP] No style updates needed")


def resolve_doc_id(name_or_id: str, links_file: str = "GOOGLE_DOCS_LINKS.md") -> str:
    """Преобразовать имя документа или ID в ID."""
    if len(name_or_id) > 30 and " " not in name_or_id:
        return name_or_id

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


def list_themes() -> None:
    """Показать список доступных тем."""
    themes_dir = os.path.join(os.path.dirname(__file__), "themes")

    if not os.path.exists(themes_dir):
        print("No themes directory found")
        return

    print("\nAvailable themes:")
    print("="*60)

    for filename in sorted(os.listdir(themes_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            theme_name = filename[:-3]
            try:
                theme = load_theme(theme_name)
                info = getattr(theme, "THEME_INFO", {})
                print(f"\n  {theme_name}")
                print(f"    {info.get('description', 'No description')}")
                if info.get("features"):
                    print(f"    Features: {', '.join(info['features'][:3])}")
            except Exception as e:
                print(f"\n  {theme_name} (failed to load: {e})")

    print()


def main() -> int:
    p = argparse.ArgumentParser(description="Apply themed styles to CV via Google Docs API")
    p.add_argument("--doc", help="Document ID or name")
    p.add_argument("--theme", default="minimalist", help="Theme to apply (default: minimalist)")
    p.add_argument("--list-themes", action="store_true", help="List available themes")
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

    if args.list_themes:
        list_themes()
        return 0

    if not args.doc:
        print("Error: --doc is required (or use --list-themes)")
        return 1

    # Получить access token
    client = load_oauth_client(args.client)
    access_token = ensure_access_token(client=client, token_path=args.token)

    # Преобразовать имя/ID в ID
    document_id = resolve_doc_id(args.doc)

    # Применить тему
    apply_cv_styles_with_theme(document_id, access_token, args.theme, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
