#!/usr/bin/env python3
"""
Извлечение стилей из существующего Google Docs документа.

Анализирует документ и показывает применённые paragraph и text стили.
"""
from __future__ import annotations

import argparse
import sys
import os
import json
from typing import Any
from collections import defaultdict

# Add parent directory to path to import gdocs_cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gdocs_cli import (
    ensure_access_token,
    load_oauth_client,
    get_doc,
    parse_doc_links,
    read_text,
)


def rgb_to_hex(rgb: dict[str, Any] | None) -> str | None:
    """Преобразовать RGB color объект в hex."""
    if not rgb:
        return None

    color = rgb.get("color", {}).get("rgbColor", {})
    r = int(color.get("red", 0) * 255)
    g = int(color.get("green", 0) * 255)
    b = int(color.get("blue", 0) * 255)

    return f"#{r:02X}{g:02X}{b:02X}"


def analyze_paragraph_styles(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Анализировать paragraph стили в документе.

    Возвращает словарь с уникальными комбинациями стилей.
    """
    content = doc.get("body", {}).get("content", [])

    styles_seen = defaultdict(list)

    for item in content:
        if not item.get("paragraph"):
            continue

        para = item["paragraph"]
        para_style = para.get("paragraphStyle", {})

        # Получить текст параграфа для контекста
        text_parts = []
        for elem in para.get("elements", []):
            text_run = elem.get("textRun")
            if text_run:
                text_parts.append(text_run.get("content", ""))
        text = "".join(text_parts).strip()

        if not text:
            continue

        # Извлечь интересующие стили
        style_info = {
            "namedStyleType": para_style.get("namedStyleType"),
            "alignment": para_style.get("alignment"),
            "indentStart": para_style.get("indentStart"),
            "indentEnd": para_style.get("indentEnd"),
            "indentFirstLine": para_style.get("indentFirstLine"),
            "lineSpacing": para_style.get("lineSpacing"),
            "spaceAbove": para_style.get("spaceAbove"),
            "spaceBelow": para_style.get("spaceBelow"),
            "borderTop": para_style.get("borderTop"),
            "borderBottom": para_style.get("borderBottom"),
            "borderLeft": para_style.get("borderLeft"),
            "borderRight": para_style.get("borderRight"),
            "borderBetween": para_style.get("borderBetween"),
            "shading": para_style.get("shading"),
        }

        # Удалить None значения
        style_info = {k: v for k, v in style_info.items() if v is not None}

        # Создать ключ для группировки
        style_key = json.dumps(style_info, sort_keys=True)

        # Сохранить пример
        styles_seen[style_key].append({
            "text": text[:100],
            "startIndex": item.get("startIndex"),
            "endIndex": item.get("endIndex"),
        })

    return styles_seen


def analyze_text_styles(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Анализировать text стили в документе.
    """
    content = doc.get("body", {}).get("content", [])

    styles_seen = defaultdict(list)

    for item in content:
        if not item.get("paragraph"):
            continue

        para = item["paragraph"]

        for elem in para.get("elements", []):
            text_run = elem.get("textRun")
            if not text_run:
                continue

            text = text_run.get("content", "").strip()
            if not text:
                continue

            text_style = text_run.get("textStyle", {})

            style_info = {
                "bold": text_style.get("bold"),
                "italic": text_style.get("italic"),
                "underline": text_style.get("underline"),
                "strikethrough": text_style.get("strikethrough"),
                "fontSize": text_style.get("fontSize"),
                "weightedFontFamily": text_style.get("weightedFontFamily"),
                "foregroundColor": text_style.get("foregroundColor"),
                "backgroundColor": text_style.get("backgroundColor"),
                "link": text_style.get("link"),
            }

            # Удалить None значения
            style_info = {k: v for k, v in style_info.items() if v is not None}

            if not style_info:
                continue

            # Создать ключ
            style_key = json.dumps(style_info, sort_keys=True)

            styles_seen[style_key].append({
                "text": text[:50],
            })

    return styles_seen


def print_paragraph_styles(styles: dict[str, Any]) -> None:
    """Вывести paragraph стили в читаемом формате."""
    print("\n" + "="*80)
    print("PARAGRAPH STYLES")
    print("="*80)

    for idx, (style_json, examples) in enumerate(styles.items(), 1):
        style = json.loads(style_json)

        print(f"\n--- Style #{idx} (used {len(examples)} times) ---")

        # Показать первый пример
        print(f"Example: '{examples[0]['text']}'")
        print(f"Range: {examples[0]['startIndex']} - {examples[0]['endIndex']}")

        print("\nStyle properties:")
        for key, value in style.items():
            if key == "shading":
                bg_color = rgb_to_hex(value.get("backgroundColor"))
                print(f"  - backgroundColor: {bg_color}")
            elif key in ["borderTop", "borderBottom", "borderLeft", "borderRight", "borderBetween"]:
                border_color = rgb_to_hex(value.get("color"))
                width = value.get("width", {})
                print(f"  - {key}:")
                print(f"      color: {border_color}")
                print(f"      width: {width.get('magnitude')} {width.get('unit')}")
                print(f"      dashStyle: {value.get('dashStyle')}")
            elif key in ["spaceAbove", "spaceBelow", "indentStart", "indentEnd", "indentFirstLine"]:
                if isinstance(value, dict):
                    print(f"  - {key}: {value.get('magnitude')} {value.get('unit')}")
            else:
                print(f"  - {key}: {value}")


def print_text_styles(styles: dict[str, Any]) -> None:
    """Вывести text стили в читаемом формате."""
    print("\n" + "="*80)
    print("TEXT STYLES")
    print("="*80)

    for idx, (style_json, examples) in enumerate(styles.items(), 1):
        style = json.loads(style_json)

        print(f"\n--- Style #{idx} (used {len(examples)} times) ---")

        # Показать несколько примеров
        for i, example in enumerate(examples[:3]):
            print(f"Example {i+1}: '{example['text']}'")

        print("\nStyle properties:")
        for key, value in style.items():
            if key == "foregroundColor":
                color = rgb_to_hex(value)
                print(f"  - foregroundColor: {color}")
            elif key == "backgroundColor":
                color = rgb_to_hex(value)
                print(f"  - backgroundColor: {color}")
            elif key == "fontSize":
                print(f"  - fontSize: {value.get('magnitude')} {value.get('unit')}")
            elif key == "weightedFontFamily":
                print(f"  - fontFamily: {value.get('fontFamily')}")
                print(f"  - weight: {value.get('weight')}")
            elif key == "link":
                print(f"  - link: {value.get('url')}")
            else:
                print(f"  - {key}: {value}")


def export_styles_to_python(para_styles: dict[str, Any], text_styles: dict[str, Any],
                            output_file: str) -> None:
    """Экспортировать стили в Python код для apply_cv_styles.py."""

    with open(output_file, "w") as f:
        f.write("# Extracted styles from existing document\n")
        f.write("# Copy relevant parts to apply_cv_styles.py\n\n")

        f.write("EXTRACTED_COLORS = {\n")

        # Извлечь все цвета
        colors_seen = set()

        for style_json in para_styles.keys():
            style = json.loads(style_json)

            # Shading colors
            if "shading" in style:
                bg_color = rgb_to_hex(style["shading"].get("backgroundColor"))
                if bg_color:
                    colors_seen.add(bg_color)

            # Border colors
            for border_key in ["borderTop", "borderBottom", "borderLeft", "borderRight"]:
                if border_key in style:
                    border_color = rgb_to_hex(style[border_key].get("color"))
                    if border_color:
                        colors_seen.add(border_color)

        for color in sorted(colors_seen):
            # Преобразовать hex в RGB 0-1
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
            name = f"color_{color[1:].lower()}"
            f.write(f"    '{name}': ({r:.3f}, {g:.3f}, {b:.3f}),  # {color}\n")

        f.write("}\n")

    print(f"\nExported styles to: {output_file}")


def main() -> int:
    p = argparse.ArgumentParser(description="Extract styles from Google Docs document")
    p.add_argument("--doc", required=True, help="Document ID or name")
    p.add_argument("--export", help="Export to Python file")
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

    # Get access token
    client = load_oauth_client(args.client)
    access_token = ensure_access_token(client=client, token_path=args.token)

    # Resolve document ID
    document_id = args.doc
    if len(document_id) <= 30 or " " in document_id:
        try:
            links = parse_doc_links(read_text("GOOGLE_DOCS_LINKS.md"))
            by_name = {d.name: d for d in links}
            if args.doc in by_name:
                document_id = by_name[args.doc].document_id
        except FileNotFoundError:
            pass

    # Fetch document
    print(f"Fetching document: {document_id}")
    doc = get_doc(document_id=document_id, access_token=access_token)
    print(f"Title: {doc.get('title')}\n")

    # Analyze styles
    para_styles = analyze_paragraph_styles(doc)
    text_styles = analyze_text_styles(doc)

    print(f"Found {len(para_styles)} unique paragraph styles")
    print(f"Found {len(text_styles)} unique text styles")

    # Print analysis
    print_paragraph_styles(para_styles)
    print_text_styles(text_styles)

    # Export if requested
    if args.export:
        export_styles_to_python(para_styles, text_styles, args.export)

    return 0


if __name__ == "__main__":
    sys.exit(main())
