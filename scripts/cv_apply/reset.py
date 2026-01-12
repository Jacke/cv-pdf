"""Document reset operations."""

import re
import sys
import os
from typing import Any

from .constants import BLOCK_LANDMARKS
from .document import (
    find_section_range,
    iter_all_paragraphs,
)
from .state import read_state, invert_replacements
from .utils import log_line

# Import gdocs_cli functions
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
from gdocs_cli import docs_batch_update, ensure_access_token, get_doc, load_oauth_client


def reset_document(
    *,
    doc: str,
    state_file: str,
    links_file: str,
    client_path: str,
    token_path: str,
) -> int:
    """
    Reset document back to placeholder anchors.

    Args:
        doc: Document name
        state_file: Path to state file
        links_file: Path to links file
        client_path: Path to OAuth client credentials
        token_path: Path to token cache

    Returns:
        Exit code (0 for success)
    """
    from .document import find_doc_info

    state = read_state(state_file)
    doc_state = (state.get("docs") or {}).get(doc)
    if not doc_state:
        raise SystemExit(f"No saved state for doc {doc!r} in {state_file}")

    stored_replacements = doc_state.get("cleaned_replacements") or doc_state.get("replacements")
    if not isinstance(stored_replacements, dict):
        raise SystemExit(f"Invalid stored replacements for doc {doc!r}")

    inverted, collisions, skipped = invert_replacements(stored_replacements)
    if not inverted:
        raise SystemExit("No stored text to reset.")

    log_line("♻️ Reset mode enabled")
    log_line(f"📄 Target doc: {doc}")

    saved_doc_url = doc_state.get("doc_url")
    saved_doc_id = doc_state.get("doc_id")
    link_url, link_id = (None, None)
    if not saved_doc_url or not saved_doc_id:
        link_url, link_id = find_doc_info(links_file, doc)

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

    access_token = ensure_access_token(client=load_oauth_client(client_path), token_path=token_path)
    log_line("🚀 Scanning document for reset...")
    doc_data = get_doc(document_id=doc_id, access_token=access_token)

    # Segment-aware processing (Body + Headers + Footers)
    segments = [(doc_data.get("body", {}).get("content", []), None)]
    for hid, h in doc_data.get("headers", {}).items():
        segments.append((h.get("content", []), hid))
    for fid, f in doc_data.get("footers", {}).items():
        segments.append((f.get("content", []), fid))

    segment_terminal_indices = {}
    all_matches = []
    processed_anchors = set()

    # 1. Landmark-based reset for major blocks
    for seg_content, seg_id in segments:
        term_idx = seg_content[-1].get("endIndex") or 0 if seg_content else 0
        segment_terminal_indices[seg_id] = term_idx

        for anchor, header in BLOCK_LANDMARKS.items():
            if anchor in processed_anchors:
                continue
            if anchor not in stored_replacements:
                continue

            r = find_section_range(seg_content, header, level=2)
            if not r:
                r = find_section_range(seg_content, header, level=0)
            if r:
                all_matches.append((r[0], r[1], anchor, seg_id))
                processed_anchors.add(anchor)
                log_line(f"📍 Found block landmark for {anchor} in {'Body' if not seg_id else seg_id}")

    # 2. Regex for remaining fields
    remaining_inverted = {
        v: k for k, v in stored_replacements.items()
        if k not in processed_anchors and v and isinstance(v, str)
    }

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

            if not doc_text:
                continue

            for text_to_find, anchor in sorted(remaining_inverted.items(), key=lambda x: len(x[0]), reverse=True):
                if not text_to_find.strip():
                    continue

                use_boundaries = len(text_to_find) < 10 and ' ' not in text_to_find
                regex_text = re.escape(text_to_find)
                if use_boundaries:
                    regex_text = rf"\b{regex_text}\b"

                for m in re.finditer(regex_text, doc_text):
                    g_start = index_map[m.start()]
                    if m.end() < len(index_map):
                        g_end = index_map[m.end()]
                    else:
                        g_end = index_map[m.end() - 1] + 1
                    all_matches.append((g_start, g_end, anchor, seg_id))

    if not all_matches:
        log_line("ℹ️ No content found to reset.")
        return 0

    # Sort matches by startIndex DESCENDING (within segments)
    all_matches.sort(key=lambda x: (x[1], -x[0]), reverse=True)

    requests = []
    applied_count = 0
    pushed_ranges = {}

    for s, e, anchor, seg_id in all_matches:
        if s >= e:
            continue

        # Check terminal newline restriction
        term_idx = segment_terminal_indices.get(seg_id)
        if term_idx is not None and e >= term_idx:
            e = term_idx - 1
        if s >= e:
            continue

        # Check overlap
        if seg_id not in pushed_ranges:
            pushed_ranges[seg_id] = []
        overlap = False
        for ps, pe in pushed_ranges[seg_id]:
            if (s < pe and e > ps):
                overlap = True
                break
        if overlap:
            continue

        # Clear styles for block landmarks only
        if anchor in BLOCK_LANDMARKS:
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
                    "textStyle": {
                        "bold": False,
                        "italic": False,
                        "fontSize": {"magnitude": 11, "unit": "PT"}
                    },
                    "fields": "bold,italic,fontSize"
                }
            })

        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": s, "endIndex": e, "segmentId": seg_id}
            }
        })

        text_to_insert = anchor
        if anchor in BLOCK_LANDMARKS:
            text_to_insert += "\n"

        requests.append({
            "insertText": {
                "location": {"index": s, "segmentId": seg_id},
                "text": text_to_insert
            }
        })

        # Ensure the inserted anchor is Normal Text
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
