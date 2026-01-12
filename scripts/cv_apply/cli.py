"""CLI utilities for interacting with gdocs_cli."""

import subprocess
import sys
from typing import Any

from .constants import GDOCS_SCOPES
from .document import strip_print_header
from .utils import log_line


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    return subprocess.run(cmd, text=True, capture_output=True)


def needs_reauth(output: str) -> bool:
    """Check if output indicates authentication is needed."""
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
    """
    Apply replacements to Google Doc with automatic re-authentication.

    Args:
        doc: Document name
        data_path: Path to replacements JSON
        gdocs_cli: Path to gdocs_cli.py script
        match_case: Whether to match case when replacing
        dry_run: Whether to do a dry run
        auto_auth: Whether to auto-authenticate on token expiry
        client: Path to OAuth client credentials
        token: Path to token cache
    """
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

    # Re-authenticate
    auth_cmd = [sys.executable, gdocs_cli, "auth", "--scopes"] + list(GDOCS_SCOPES)
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

    # Retry apply
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
    """
    Get document text with automatic re-authentication.

    Args:
        doc: Document name
        gdocs_cli: Path to gdocs_cli.py script
        auto_auth: Whether to auto-authenticate on token expiry

    Returns:
        Document text content
    """
    cmd = [sys.executable, gdocs_cli, "print", "--doc", doc, "--format", "plain"]
    first = run_cmd(cmd)
    if first.stderr:
        sys.stderr.write(first.stderr)
    if first.returncode == 0:
        return first.stdout or ""

    combined = (first.stdout or "") + (first.stderr or "")
    if not auto_auth or not needs_reauth(combined):
        raise SystemExit(f"gdocs_cli print failed with exit code {first.returncode}")

    # Re-authenticate
    auth_cmd = [sys.executable, gdocs_cli, "auth", "--scopes"] + list(GDOCS_SCOPES)
    auth = run_cmd(auth_cmd)
    if auth.stdout:
        sys.stdout.write(auth.stdout)
    if auth.stderr:
        sys.stderr.write(auth.stderr)
    if auth.returncode != 0:
        raise SystemExit(f"gdocs_cli auth failed with exit code {auth.returncode}")

    # Retry print
    retry = run_cmd(cmd)
    if retry.returncode != 0:
        if retry.stderr:
            sys.stderr.write(retry.stderr)
        raise SystemExit(f"gdocs_cli print failed after auth (exit code {retry.returncode})")
    return retry.stdout or ""
