#!/usr/bin/env python3
"""
CV Structured Apply - Apply structured CV JSON to Google Docs templates.

This script reads structured CV data and applies it to Google Docs templates,
with support for automatic styling, reset operations, and state management.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

# Setup path for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from cv_apply.formatters import build_replacements
from cv_apply.document import find_doc_info, strip_print_header
from cv_apply.styling import apply_block_styles
from cv_apply.state import update_state
from cv_apply.cli import apply_with_auto_auth, get_doc_text
from cv_apply.reset import reset_document
from cv_apply.utils import read_json, write_json, log_line, extract_placeholders


def handle_reset(args: argparse.Namespace) -> int:
    """
    Handle document reset operation.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    if not args.doc:
        raise SystemExit("--reset requires --doc")

    return reset_document(
        doc=args.doc,
        state_file=args.state_file,
        links_file=args.links_file,
        client_path=args.client,
        token_path=args.token,
    )


def handle_apply(args: argparse.Namespace) -> int:
    """
    Handle document apply operation.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    if not args.data:
        raise SystemExit("--data is required unless --reset is set")

    # Load and validate data
    data = read_json(args.data)
    if not isinstance(data, dict):
        raise SystemExit("Structured CV data must be a JSON object.")

    # Build replacements
    replacements = build_replacements(data)
    payload = {"replacements": replacements}

    should_log = bool(args.out or args.doc)

    if should_log:
        log_line("🧾 Loaded structured data")
        log_line(f"📦 Data file: {args.data}")
        log_line(f"🧩 Total placeholders: {len(replacements)}")

    # Write replacements to output file or temp file
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
        # Just print to stdout
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    # Apply to document if specified
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

        # Analyze placeholders
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

        # Apply replacements
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

        # Apply styling
        if not args.dry_run and not args.reset:
            apply_block_styles(
                doc_id=doc_id,
                client_path=args.client,
                token_path=args.token,
                replacements=replacements
            )

        # Update state
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

    # Cleanup temp file
    if tmp_path:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return 0


def main(argv: list[str]) -> int:
    """
    Main entry point for CV apply script.

    Args:
        argv: Command-line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Apply structured CV JSON to template placeholders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input/Output
    parser.add_argument("--data", help="Path to structured CV JSON")
    parser.add_argument("--out", help="Where to write replacements JSON (optional)")
    parser.add_argument("--doc", help="Google Doc name to update (optional)")

    # Configuration
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
    parser.add_argument(
        "--state-file",
        default=".cv_apply_state.json",
        help="Path to apply state JSON"
    )

    # Options
    parser.add_argument(
        "--match-case",
        action="store_true",
        help="Match case when replacing placeholders"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print requests JSON without changing the document"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset document back to last applied anchors"
    )
    parser.add_argument(
        "--auto-auth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Re-run OAuth auth if the token is expired or revoked (default: true)",
    )

    args = parser.parse_args(argv)

    # Handle reset or apply
    if args.reset:
        return handle_reset(args)
    else:
        return handle_apply(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
