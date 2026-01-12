#!/usr/bin/env python3
"""
Show Google Docs document styles, including margins/indents and spacing.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Iterable

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import (  # noqa: E402
    ensure_access_token,
    load_oauth_client,
    get_doc,
    parse_doc_links,
    read_text,
)


def format_dimension(value: dict[str, Any] | None) -> str | None:
    if not isinstance(value, dict):
        return None
    magnitude = value.get("magnitude")
    unit = value.get("unit")
    if magnitude is None or unit is None:
        return None
    return f"{magnitude} {unit}"


def format_page_size(page_size: dict[str, Any] | None) -> str | None:
    if not isinstance(page_size, dict):
        return None
    width = format_dimension(page_size.get("width"))
    height = format_dimension(page_size.get("height"))
    if not width or not height:
        return None
    return f"{width} x {height}"


def show_document_style(doc: dict[str, Any]) -> None:
    style = doc.get("documentStyle") or {}
    print("\n" + "=" * 80)
    print("DOCUMENT STYLE")
    print("=" * 80)

    if not style:
        print("No documentStyle found.")
        return

    page_size = format_page_size(style.get("pageSize"))
    if page_size:
        print(f"- pageSize: {page_size}")

    for key in ("marginTop", "marginRight", "marginBottom", "marginLeft"):
        value = format_dimension(style.get(key))
        if value:
            print(f"- {key}: {value}")

    if "pageOrientation" in style:
        print(f"- pageOrientation: {style.get('pageOrientation')}")


def show_section_styles(content: Iterable[dict[str, Any]]) -> None:
    print("\n" + "=" * 80)
    print("SECTION STYLES")
    print("=" * 80)

    found = False
    for item in content:
        section = item.get("sectionBreak")
        if not section:
            continue
        section_style = section.get("sectionStyle") or {}
        index = item.get("startIndex")
        print(f"\n--- SectionBreak at index {index} ---")
        found = True

        for key in ("marginTop", "marginRight", "marginBottom", "marginLeft"):
            value = format_dimension(section_style.get(key))
            if value:
                print(f"  - {key}: {value}")

        column_props = section_style.get("columnProperties") or []
        if column_props:
            print(f"  - columns: {len(column_props)}")

    if not found:
        print("No section breaks found.")


def extract_paragraph_text(para: dict[str, Any]) -> str:
    parts: list[str] = []
    for elem in para.get("elements", []):
        text_run = elem.get("textRun")
        if text_run:
            parts.append(text_run.get("content", ""))
    text = "".join(parts).replace("\n", " ").strip()
    return text


def show_paragraph_styles(content: Iterable[dict[str, Any]], max_paragraphs: int | None,
                          include_empty: bool) -> None:
    print("\n" + "=" * 80)
    print("PARAGRAPH STYLES")
    print("=" * 80)

    count = 0
    for item in content:
        para = item.get("paragraph")
        if not para:
            continue
        text = extract_paragraph_text(para)
        if not text and not include_empty:
            continue

        para_style = para.get("paragraphStyle") or {}
        bullet = para.get("bullet") or {}

        count += 1
        print(f"\n--- Paragraph #{count} ---")
        if text:
            print(f"Text: \"{text[:120]}\"")
        print(f"Range: {item.get('startIndex')} - {item.get('endIndex')}")

        if bullet:
            list_id = bullet.get("listId")
            nesting = bullet.get("nestingLevel")
            print(f"List: listId={list_id} nestingLevel={nesting}")

        if "namedStyleType" in para_style:
            print(f"  - namedStyleType: {para_style.get('namedStyleType')}")
        if "alignment" in para_style:
            print(f"  - alignment: {para_style.get('alignment')}")
        if "lineSpacing" in para_style:
            print(f"  - lineSpacing: {para_style.get('lineSpacing')}")

        for key in ("indentStart", "indentEnd", "indentFirstLine", "spaceAbove", "spaceBelow"):
            value = format_dimension(para_style.get(key))
            if value:
                print(f"  - {key}: {value}")

        if max_paragraphs and count >= max_paragraphs:
            print(f"\n... truncated at {max_paragraphs} paragraphs")
            break

    if count == 0:
        print("No paragraphs found.")


def resolve_doc_id(doc_arg: str) -> str:
    if len(doc_arg) > 30 and " " not in doc_arg:
        return doc_arg
    try:
        links = parse_doc_links(read_text("GOOGLE_DOCS_LINKS.md"))
        by_name = {d.name: d for d in links}
        if doc_arg in by_name:
            return by_name[doc_arg].document_id
    except FileNotFoundError:
        pass
    return doc_arg


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Google Docs styles and indents")
    parser.add_argument("--doc", required=True, help="Document ID or name")
    parser.add_argument("--max-paragraphs", type=int, help="Limit paragraph output")
    parser.add_argument("--include-empty", action="store_true", help="Include empty paragraphs")
    parser.add_argument(
        "--client",
        default=os.environ.get("GDOCS_OAUTH_CLIENT", ".secrets/google-oauth-client.json"),
        help="Path to OAuth client JSON",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GDOCS_TOKEN", ".secrets/google-token.json"),
        help="Path to token cache",
    )
    args = parser.parse_args()

    client = load_oauth_client(args.client)
    access_token = ensure_access_token(client=client, token_path=args.token)

    document_id = resolve_doc_id(args.doc)
    print(f"Fetching document: {document_id}")
    doc = get_doc(document_id=document_id, access_token=access_token)
    print(f"Title: {doc.get('title')}")

    content = doc.get("body", {}).get("content", [])
    show_document_style(doc)
    show_section_styles(content)
    show_paragraph_styles(
        content,
        max_paragraphs=args.max_paragraphs,
        include_empty=args.include_empty,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
