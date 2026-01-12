"""Document operations and content extraction."""

import re
import urllib.parse
from typing import Any, Iterator

from .constants import URL_REGEX, EMAIL_REGEX, PHONE_REGEX


def parse_doc_links(markdown: str) -> dict[str, dict[str, str]]:
    """Parse Google Docs links from markdown format."""
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
    """Extract Google Doc ID from URL."""
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
    """
    Find document URL and ID from links file.

    Args:
        links_path: Path to links markdown file
        doc_name: Name of the document to find

    Returns:
        Tuple of (url, document_id)
    """
    from .utils import read_text

    try:
        links = parse_doc_links(read_text(links_path))
    except FileNotFoundError:
        return None, None
    info = links.get(doc_name)
    if not info:
        return None, None
    return info.get("url"), info.get("document_id")


def iter_all_paragraphs(content: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Iterate over all paragraphs in document content, including nested tables."""
    for item in content:
        if item.get("paragraph"):
            yield item
        elif item.get("table"):
            table = item.get("table")
            for row in table.get("tableRows") or []:
                for cell in row.get("tableCells") or []:
                    yield from iter_all_paragraphs(cell.get("content") or [])


def get_paragraph_text(item: dict[str, Any]) -> str:
    """Extract stripped text from a paragraph item."""
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
    """Extract raw (unstripped) text from a paragraph item."""
    para = item.get("paragraph")
    if not para:
        return ""
    elements = para.get("elements") or []
    return "".join(elem.get("text_run", elem.get("textRun", {})).get("content", "") for elem in elements)


def get_heading_level(item: dict[str, Any]) -> int | None:
    """Get heading level from paragraph item (1-6) or None if not a heading."""
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
    """Check if paragraph is blank/empty."""
    text = get_paragraph_text(item)
    return not text


def find_section_range(
    content: list[dict[str, Any]],
    heading_text: str,
    level: int = 2
) -> tuple[int, int] | None:
    """
    Find the range (start_index, end_index) of a section by heading.

    Args:
        content: Document content items
        heading_text: Text to search for in headings
        level: Heading level to match (0 for flexible search)

    Returns:
        Tuple of (start_index, end_index) or None if not found
    """
    section_start_index = None
    for item in content:
        if not item.get("paragraph"):
            continue
        h_level = get_heading_level(item) or 0
        text = get_paragraph_text(item)

        # Match by level if specified, or by any non-zero level if level=0
        match = False
        if level > 0:
            match = (h_level == level and heading_text.lower() in text.lower())
        else:
            # Flexible search: exact text match
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
    """Collect all paragraphs within a range."""
    out: list[dict[str, Any]] = []
    for item in content:
        if not item.get("paragraph"):
            continue
        item_start = item.get("startIndex") or 0
        item_end = item.get("endIndex") or 0
        if item_start < start or item_end > end:
            continue
        out.append({
            "item": item,
            "start": item_start,
            "end": item_end,
            "text": get_paragraph_text(item)
        })
    return out


def split_blocks(paragraphs: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split paragraphs into blocks separated by blank lines."""
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
    """Collect all list IDs within a range."""
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


def create_link_requests(text: str, start_index: int) -> list[dict[str, Any]]:
    """
    Create Google Docs API requests to linkify URLs, emails, and phone numbers.

    Args:
        text: Text to scan for linkable content
        start_index: Starting index in the document

    Returns:
        List of API request objects
    """
    requests = []

    # URLs
    for match in URL_REGEX.finditer(text):
        url = match.group()
        # Clean up trailing punctuation
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


def strip_print_header(text: str) -> str:
    """Remove separator lines from gdocs_cli print output."""
    lines = []
    for line in text.splitlines():
        if line.startswith("====="):
            continue
        lines.append(line)
    return "\n".join(lines)
