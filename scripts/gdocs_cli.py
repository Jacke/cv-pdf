#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import io
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from typing import Any, Iterable
import xml.etree.ElementTree as ET


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_API_BASE = "https://docs.googleapis.com/v1"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path: str, value: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-+*]|\d+[.)])\s+")


def normalize_markdown_lists(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    drop: set[int] = set()
    for i, line in enumerate(lines):
        if line.strip():
            continue
        prev = None
        for j in range(i - 1, -1, -1):
            if lines[j].strip():
                prev = j
                break
        nxt = None
        for k in range(i + 1, len(lines)):
            if lines[k].strip():
                nxt = k
                break
        if prev is None or nxt is None:
            continue
        if _LIST_ITEM_RE.match(lines[prev]) and _LIST_ITEM_RE.match(lines[nxt]):
            drop.add(i)
    out_lines = [line for idx, line in enumerate(lines) if idx not in drop]
    out = "\n".join(out_lines)
    if text.endswith("\n"):
        out += "\n"
    return out


def write_bytes(path: str, value: bytes) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(value)
    os.replace(tmp, path)


def now_epoch() -> int:
    return int(time.time())


@dataclass(frozen=True)
class OAuthClient:
    client_id: str
    client_secret: str
    auth_uri: str
    token_uri: str


def load_oauth_client(path: str) -> OAuthClient:
    raw = read_json(path)
    installed = raw.get("installed") or raw.get("web") or {}
    missing = [k for k in ("client_id", "client_secret", "auth_uri", "token_uri") if k not in installed]
    if missing:
        raise SystemExit(f"Invalid OAuth client JSON, missing: {', '.join(missing)}")
    return OAuthClient(
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        auth_uri=installed["auth_uri"],
        token_uri=installed["token_uri"],
    )


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    server_version = "gdocs-cli/1.0"
    oauth_result: dict[str, str] | None = None

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = (params.get("code") or [None])[0]
        state = (params.get("state") or [None])[0]
        error = (params.get("error") or [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if error:
            self.wfile.write(f"OAuth error: {error}\n".encode("utf-8"))
            self.__class__.oauth_result = {"error": error, "state": state or ""}
            return

        if not code:
            self.wfile.write(b"Missing code\n")
            self.__class__.oauth_result = {"error": "missing_code", "state": state or ""}
            return

        self.wfile.write(b"OK. You can close this tab.\n")
        self.__class__.oauth_result = {"code": code, "state": state or ""}


def http_post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=encoded,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} during POST {url}: {err_body}") from None
    except URLError as exc:
        raise SystemExit(f"Network error during POST {url}: {exc}") from None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise SystemExit(f"Non-JSON response from POST {url}: {body[:500]}") from None


def http_get_json(url: str, access_token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url=url,
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise HTTPError(url, exc.code, err_body, exc.headers, None) from None
    except URLError as exc:
        raise SystemExit(f"Network error during GET {url}: {exc}") from None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise SystemExit(f"Non-JSON response from GET {url}: {body[:500]}") from None


def http_get_bytes(url: str, access_token: str) -> bytes:
    req = urllib.request.Request(
        url=url,
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise HTTPError(url, exc.code, err_body, exc.headers, None) from None
    except URLError as exc:
        raise SystemExit(f"Network error during GET {url}: {exc}") from None


def http_post_json(url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise HTTPError(url, exc.code, err_body, exc.headers, None) from None
    except URLError as exc:
        raise SystemExit(f"Network error during POST {url}: {exc}") from None
    try:
        return json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        raise SystemExit(f"Non-JSON response from POST {url}: {body[:500]}") from None


def ensure_access_token(
    *,
    client: OAuthClient,
    token_path: str,
    min_ttl_seconds: int = 60,
) -> str:
    token = read_json(token_path)
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    expires_at = int(token.get("expires_at") or 0)

    if access_token and expires_at - now_epoch() > min_ttl_seconds:
        return access_token

    if not refresh_token:
        raise SystemExit(f"No refresh_token in {token_path}; run `auth` first.")

    refreshed = http_post_form(
        client.token_uri,
        {
            "client_id": client.client_id,
            "client_secret": client.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )

    if "access_token" not in refreshed:
        raise SystemExit(f"Token refresh failed: {refreshed}")

    token["access_token"] = refreshed["access_token"]
    token["token_type"] = refreshed.get("token_type", "Bearer")
    token["expires_in"] = int(refreshed.get("expires_in") or 3600)
    token["expires_at"] = now_epoch() + int(token["expires_in"])
    write_json(token_path, token)
    return token["access_token"]


def token_scopes(token_path: str) -> set[str]:
    try:
        token = read_json(token_path)
    except FileNotFoundError:
        return set()
    raw = (token.get("scope") or "").strip()
    if not raw:
        return set()
    return set(raw.split())


def require_scopes(token_path: str, required: list[str]) -> None:
    scopes = token_scopes(token_path)
    if not scopes:
        raise SystemExit(
            f"Token scopes are unknown/empty in {token_path}. Re-run auth with scopes:\n"
            f"  python3 gdocs_cli.py auth --scopes {' '.join(required)}"
        )
    missing = [s for s in required if s not in scopes]
    if not missing:
        return
    raise SystemExit(
        "Request will fail due to missing OAuth scopes.\n"
        f"Missing: {' '.join(missing)}\n"
        "Fix:\n"
        f"  python3 gdocs_cli.py auth --scopes {' '.join(sorted(scopes | set(required)))}\n"
        f"If it still fails, delete {token_path} and revoke app access at https://myaccount.google.com/permissions, then re-run auth."
    )


def oauth_authorize_interactive(
    *,
    client: OAuthClient,
    token_path: str,
    scopes: list[str],
) -> None:
    _OAuthCallbackHandler.oauth_result = None

    server = HTTPServer(("127.0.0.1", 0), _OAuthCallbackHandler)
    _, port = server.server_address
    redirect_uri = f"http://localhost:{port}"

    state = secrets.token_urlsafe(16)
    auth_params = {
        "client_id": client.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    auth_url = f"{client.auth_uri}?{urllib.parse.urlencode(auth_params)}"

    eprint("Opening browser for OAuth consent...")
    eprint(auth_url)
    try:
        webbrowser.open(auth_url, new=1, autoraise=True)
    except Exception:
        pass

    server.handle_request()
    result = _OAuthCallbackHandler.oauth_result
    if not result:
        raise SystemExit("OAuth callback not received.")

    if result.get("state") != state:
        raise SystemExit("OAuth state mismatch.")

    if "error" in result:
        raise SystemExit(f"OAuth failed: {result}")

    code = result["code"]

    exchanged = http_post_form(
        client.token_uri,
        {
            "code": code,
            "client_id": client.client_id,
            "client_secret": client.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )

    if "access_token" not in exchanged:
        raise SystemExit(f"Token exchange failed: {exchanged}")

    token = {
        "access_token": exchanged["access_token"],
        "refresh_token": exchanged.get("refresh_token"),
        "token_type": exchanged.get("token_type", "Bearer"),
        "scope": exchanged.get("scope", " ".join(scopes)),
        "expires_in": int(exchanged.get("expires_in") or 3600),
        "expires_at": now_epoch() + int(exchanged.get("expires_in") or 3600),
    }

    if not token.get("refresh_token"):
        eprint("Warning: refresh_token missing. If this is the first run, ensure `prompt=consent` worked.")
        eprint("You may need to revoke app access at https://myaccount.google.com/permissions and retry.")

    write_json(token_path, token)
    eprint(f"Wrote token to {token_path}")


@dataclass(frozen=True)
class DocLink:
    name: str
    document_id: str
    url: str


def parse_doc_links(markdown: str) -> list[DocLink]:
    out: list[DocLink] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        # Format: - Name: https://docs.google.com/document/d/<id>/edit
        try:
            name, url = line[2:].split(":", 1)
        except ValueError:
            continue
        name = name.strip()
        url = url.strip()
        parsed = urllib.parse.urlparse(url)
        parts = parsed.path.split("/")
        if "document" not in parts:
            continue
        try:
            d_idx = parts.index("d")
        except ValueError:
            continue
        if d_idx + 1 >= len(parts):
            continue
        document_id = parts[d_idx + 1]
        if not document_id:
            continue
        out.append(DocLink(name=name, document_id=document_id, url=url))
    return out


def iter_text_runs(doc_json: dict[str, Any]) -> Iterable[str]:
    body = (doc_json.get("body") or {}).get("content") or []
    for block in body:
        paragraph = block.get("paragraph")
        if not paragraph:
            continue
        for elem in paragraph.get("elements") or []:
            text_run = elem.get("textRun")
            if not text_run:
                continue
            content = (text_run.get("content") or "")
            if content:
                yield content


def get_doc(
    *,
    document_id: str,
    access_token: str,
) -> dict[str, Any]:
    return http_get_json(f"{DOCS_API_BASE}/documents/{document_id}", access_token)


def docs_batch_update(*, document_id: str, access_token: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    url = f"{DOCS_API_BASE}/documents/{document_id}:batchUpdate"
    return http_post_json(url, access_token, {"requests": requests})


def drive_export_bytes(*, file_id: str, access_token: str, mime_type: str) -> bytes:
    qs = urllib.parse.urlencode({"mimeType": mime_type})
    url = f"{DRIVE_API_BASE}/files/{file_id}/export?{qs}"
    return http_get_bytes(url, access_token)


def drive_export_plain_text(*, file_id: str, access_token: str) -> str:
    raw = drive_export_bytes(file_id=file_id, access_token=access_token, mime_type="text/plain")
    return raw.decode("utf-8", errors="replace")


def drive_get_metadata(*, file_id: str, access_token: str) -> dict[str, Any]:
    fields = "id,name,mimeType,shortcutDetails(targetId,targetMimeType)"
    qs = urllib.parse.urlencode({"fields": fields})
    url = f"{DRIVE_API_BASE}/files/{file_id}?{qs}"
    return http_get_json(url, access_token)


def drive_download_bytes(*, file_id: str, access_token: str) -> bytes:
    url = f"{DRIVE_API_BASE}/files/{file_id}?alt=media"
    return http_get_bytes(url, access_token)


def drive_upload_multipart(
    *,
    access_token: str,
    url: str,
    metadata: dict[str, Any],
    media_bytes: bytes,
    media_type: str,
    method: str = "POST",
) -> dict[str, Any]:
    boundary = f"===============gdocs_cli_{secrets.token_hex(12)}"
    meta_json = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
    ).encode("utf-8")
    body += meta_json + b"\r\n"
    body += (
        f"--{boundary}\r\n"
        f"Content-Type: {media_type}\r\n\r\n"
    ).encode("utf-8")
    body += media_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_body = resp.read().decode("utf-8")
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} during {method} {url}: {err_body}") from None
    except URLError as exc:
        raise SystemExit(f"Network error during {method} {url}: {exc}") from None
    if not resp_body.strip():
        return {}
    try:
        return json.loads(resp_body)
    except json.JSONDecodeError:
        raise SystemExit(f"Non-JSON response from {method} {url}: {resp_body[:500]}") from None


def render_markdown_to_docx(
    md_path: str,
    out_path: str,
    reference_docx: str | None,
    *,
    normalize_lists: bool,
) -> None:
    if not shutil.which("pandoc"):
        raise SystemExit("pandoc not found; install it or make sure it's on PATH.")
    md_format = "markdown+pipe_tables+fenced_divs+markdown_attribute"
    raw = read_text(md_path)
    if normalize_lists:
        raw = normalize_markdown_lists(raw)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tmp:
            tmp.write(raw)
            tmp.flush()
            tmp_path = tmp.name
        cmd = ["pandoc", "--from", md_format, tmp_path, "-o", out_path]
        if reference_docx:
            cmd.extend(["--reference-doc", reference_docx])
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"pandoc failed with exit code {exc.returncode}") from None
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def drive_resolve_target(*, file_id: str, access_token: str) -> tuple[str, dict[str, Any]]:
    meta = drive_get_metadata(file_id=file_id, access_token=access_token)
    if meta.get("mimeType") == "application/vnd.google-apps.shortcut":
        shortcut = meta.get("shortcutDetails") or {}
        target_id = shortcut.get("targetId")
        if not target_id:
            raise SystemExit(f"Drive shortcut without targetId for file {file_id}")
        meta = drive_get_metadata(file_id=target_id, access_token=access_token)
        return target_id, meta
    return file_id, meta


def extract_text_from_docx(data: bytes) -> str:
    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        xml_bytes = zf.read("word/document.xml")
    except KeyError:
        raise SystemExit("DOCX missing word/document.xml") from None

    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    lines: list[str] = []
    for p in root.findall(".//w:p", ns):
        parts: list[str] = []
        for node in p.iter():
            tag = node.tag
            if tag.endswith("}t") and node.text:
                parts.append(node.text)
            elif tag.endswith("}tab"):
                parts.append("\t")
            elif tag.endswith("}br"):
                parts.append("\n")
        line = "".join(parts).strip("\r")
        lines.append(line)
    text = "\n".join([ln for ln in lines if ln != ""])
    return text


def extract_markdown_from_docx(data: bytes) -> str:
    def escape_md(s: str) -> str:
        return (
            s.replace("\\", "\\\\")
            .replace("*", "\\*")
            .replace("_", "\\_")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("`", "\\`")
        )

    def apply_styles(text: str, *, bold: bool, italic: bool, strike: bool, underline: bool) -> str:
        out = text
        if strike:
            out = f"~~{out}~~"
        if bold and italic:
            out = f"***{out}***"
        elif bold:
            out = f"**{out}**"
        elif italic:
            out = f"*{out}*"
        if underline:
            out = f"<u>{out}</u>"
        return out

    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        doc_xml = zf.read("word/document.xml")
    except KeyError:
        raise SystemExit("DOCX missing word/document.xml") from None

    rels: dict[str, str] = {}
    try:
        rels_xml = zf.read("word/_rels/document.xml.rels")
        rel_root = ET.fromstring(rels_xml)
        for rel in rel_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            rid = rel.attrib.get("Id") or ""
            target = rel.attrib.get("Target") or ""
            mode = rel.attrib.get("TargetMode") or ""
            if rid and target and mode.lower() == "external":
                rels[rid] = target
    except KeyError:
        pass

    ns = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    root = ET.fromstring(doc_xml)

    out_lines: list[str] = []
    for p in root.findall(".//w:body/w:p", ns):
        p_style = ""
        ppr = p.find("w:pPr", ns)
        if ppr is not None:
            ps = ppr.find("w:pStyle", ns)
            if ps is not None:
                p_style = ps.attrib.get(f"{{{ns['w']}}}val", "") or ""

        heading_prefix = ""
        style_norm = p_style.lower()
        if style_norm in ("title",):
            heading_prefix = "# "
        elif style_norm in ("subtitle",):
            heading_prefix = "## "
        elif style_norm.startswith("heading"):
            # Heading1/Heading2/etc
            level_str = "".join(ch for ch in p_style if ch.isdigit())
            level = int(level_str) if level_str else 1
            level = max(1, min(6, level))
            heading_prefix = "#" * level + " "

        list_prefix = ""
        indent = ""
        if ppr is not None:
            num_pr = ppr.find("w:numPr", ns)
            if num_pr is not None:
                ilvl = num_pr.find("w:ilvl", ns)
                level = 0
                if ilvl is not None:
                    level = int(ilvl.attrib.get(f"{{{ns['w']}}}val", "0") or 0)
                indent = "  " * max(0, level)
                list_prefix = "- "

        parts: list[str] = []

        def handle_run(r: ET.Element, link_url: str | None) -> None:
            rpr = r.find("w:rPr", ns)
            bold = italic = strike = underline = False
            if rpr is not None:
                b = rpr.find("w:b", ns)
                if b is not None and (b.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    bold = True
                i = rpr.find("w:i", ns)
                if i is not None and (i.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    italic = True
                s = rpr.find("w:strike", ns)
                if s is not None and (s.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    strike = True
                u = rpr.find("w:u", ns)
                if u is not None and (u.attrib.get(f"{{{ns['w']}}}val", "single") != "none"):
                    underline = True

            text_chunks: list[str] = []
            for node in r:
                if node.tag == f"{{{ns['w']}}}t" and node.text:
                    text_chunks.append(node.text)
                elif node.tag == f"{{{ns['w']}}}tab":
                    text_chunks.append("\t")
                elif node.tag == f"{{{ns['w']}}}br":
                    text_chunks.append("\n")
            raw_text = "".join(text_chunks)
            if not raw_text:
                return

            text = escape_md(raw_text)
            styled = apply_styles(text, bold=bold, italic=italic, strike=strike, underline=underline)
            if link_url:
                parts.append(f"[{styled}]({link_url})")
            else:
                parts.append(styled)

        for child in p:
            if child.tag == f"{{{ns['w']}}}r":
                handle_run(child, None)
            elif child.tag == f"{{{ns['w']}}}hyperlink":
                rid = child.attrib.get(f"{{{ns['r']}}}id", "")
                link_url = rels.get(rid) if rid else None
                for r in child.findall("w:r", ns):
                    handle_run(r, link_url)

        line = "".join(parts).strip("\r")
        line = line.strip()
        if not line:
            out_lines.append("")
            continue
        out_lines.append(f"{indent}{heading_prefix}{list_prefix}{line}".rstrip())

    # Collapse excessive blank lines a bit
    normalized: list[str] = []
    blank_run = 0
    for line in out_lines:
        if line == "":
            blank_run += 1
            if blank_run <= 1:
                normalized.append("")
            continue
        blank_run = 0
        normalized.append(line)
    return "\n".join(normalized).strip() + "\n"


def _escape_md_text(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("`", "\\`")
    )


def docs_to_markdown(doc_json: dict[str, Any]) -> str:
    def apply_styles(text: str, style: dict[str, Any]) -> str:
        bold = bool(style.get("bold"))
        italic = bool(style.get("italic"))
        strike = bool(style.get("strikethrough"))
        underline = bool(style.get("underline"))
        out = text
        if strike:
            out = f"~~{out}~~"
        if bold and italic:
            out = f"***{out}***"
        elif bold:
            out = f"**{out}**"
        elif italic:
            out = f"*{out}*"
        if underline:
            out = f"<u>{out}</u>"
        return out

    lists = doc_json.get("lists") or {}
    body = (doc_json.get("body") or {}).get("content") or []

    out_lines: list[str] = []
    for block in body:
        paragraph = block.get("paragraph")
        if not paragraph:
            continue

        pstyle = paragraph.get("paragraphStyle") or {}
        named = (pstyle.get("namedStyleType") or "").upper()
        heading_prefix = ""
        if named == "TITLE":
            heading_prefix = "# "
        elif named == "SUBTITLE":
            heading_prefix = "## "
        elif named.startswith("HEADING_"):
            try:
                level = int(named.split("_", 1)[1])
            except Exception:
                level = 1
            level = max(1, min(6, level))
            heading_prefix = "#" * level + " "

        bullet = paragraph.get("bullet")
        indent = ""
        list_prefix = ""
        if bullet:
            nesting = int(bullet.get("nestingLevel") or 0)
            indent = "  " * max(0, nesting)

            list_id = bullet.get("listId") or ""
            glyph = ""
            try:
                levels = ((lists.get(list_id) or {}).get("listProperties") or {}).get("nestingLevels") or []
                glyph = ((levels[nesting] or {}).get("glyphType") or "").upper()
            except Exception:
                glyph = ""

            ordered = any(k in glyph for k in ("NUMBER", "ROMAN", "ALPHA"))
            list_prefix = "1. " if ordered else "- "

        parts: list[str] = []
        for elem in paragraph.get("elements") or []:
            tr = elem.get("textRun")
            if not tr:
                continue
            content = tr.get("content") or ""
            if not content:
                continue
            content = content.replace("\n", "")
            if not content:
                continue
            escaped = _escape_md_text(content)
            style = tr.get("textStyle") or {}
            styled = apply_styles(escaped, style)
            link = (style.get("link") or {}).get("url")
            if link:
                parts.append(f"[{styled}]({link})")
            else:
                parts.append(styled)

        line = "".join(parts).strip()
        if not line:
            out_lines.append("")
            continue
        out_lines.append(f"{indent}{heading_prefix}{list_prefix}{line}".rstrip())

    normalized: list[str] = []
    blank_run = 0
    for line in out_lines:
        if line == "":
            blank_run += 1
            if blank_run <= 1:
                normalized.append("")
            continue
        blank_run = 0
        normalized.append(line)
    return "\n".join(normalized).strip() + "\n"


def docs_to_struct(doc_json: dict[str, Any]) -> dict[str, Any]:
    def rgb01_to_255(x: Any) -> int | None:
        try:
            v = float(x)
        except Exception:
            return None
        if v < 0:
            v = 0.0
        if v > 1:
            v = 1.0
        return int(round(v * 255))

    def color_to_hex(color_obj: Any) -> str | None:
        if not isinstance(color_obj, dict):
            return None
        # foregroundColor/backgroundColor usually: {"color":{"rgbColor":{"red":0.1,"green":...}}}
        c = color_obj.get("color")
        if isinstance(c, dict):
            rgb = c.get("rgbColor")
            if isinstance(rgb, dict):
                r = rgb01_to_255(rgb.get("red"))
                g = rgb01_to_255(rgb.get("green"))
                b = rgb01_to_255(rgb.get("blue"))
                if r is None or g is None or b is None:
                    return None
                return f"#{r:02X}{g:02X}{b:02X}"
        return None

    def extract_style(style: dict[str, Any]) -> dict[str, Any]:
        weighted = style.get("weightedFontFamily") or {}
        if not isinstance(weighted, dict):
            weighted = {}
        font_family = weighted.get("fontFamily")

        font_size = style.get("fontSize") or {}
        if not isinstance(font_size, dict):
            font_size = {}
        magnitude = font_size.get("magnitude")
        unit = font_size.get("unit")
        if magnitude is None or unit is None:
            font_size_out = None
        else:
            font_size_out = {"magnitude": magnitude, "unit": unit}

        return {
            "bold": bool(style.get("bold")),
            "italic": bool(style.get("italic")),
            "underline": bool(style.get("underline")),
            "strikethrough": bool(style.get("strikethrough")),
            "fontFamily": font_family if isinstance(font_family, str) else None,
            "fontSize": font_size_out,
            "foregroundColor": color_to_hex(style.get("foregroundColor")),
            "backgroundColor": color_to_hex(style.get("backgroundColor")),
        }

    def named_style_to_level(named: str) -> int | None:
        named = (named or "").upper()
        if named == "TITLE":
            return 1
        if named == "SUBTITLE":
            return 2
        if named.startswith("HEADING_"):
            try:
                lvl = int(named.split("_", 1)[1])
            except Exception:
                return 1
            return max(1, min(6, lvl))
        return None

    def parse_blocks(*, body: list[dict[str, Any]], lists: dict[str, Any]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for block in body:
            paragraph = block.get("paragraph")
            if not paragraph:
                continue

            pstyle = paragraph.get("paragraphStyle") or {}
            named = (pstyle.get("namedStyleType") or "").upper()
            heading_level = named_style_to_level(named)
            heading_id = pstyle.get("headingId")

            bullet = paragraph.get("bullet")
            list_info: dict[str, Any] | None = None
            if bullet:
                nesting = int(bullet.get("nestingLevel") or 0)
                list_id = bullet.get("listId") or ""
                glyph = ""
                try:
                    levels = ((lists.get(list_id) or {}).get("listProperties") or {}).get("nestingLevels") or []
                    glyph = ((levels[nesting] or {}).get("glyphType") or "").upper()
                except Exception:
                    glyph = ""
                ordered = any(k in glyph for k in ("NUMBER", "ROMAN", "ALPHA"))
                list_info = {
                    "nestingLevel": nesting,
                    "ordered": ordered,
                    "listId": list_id or None,
                    "glyphType": glyph or None,
                }

            runs: list[dict[str, Any]] = []
            for elem in paragraph.get("elements") or []:
                tr = elem.get("textRun")
                if not tr:
                    continue
                content = tr.get("content") or ""
                if not content:
                    continue
                content = content.replace("\n", "")
                if not content:
                    continue
                style = tr.get("textStyle") or {}
                link = (style.get("link") or {}).get("url")
                runs.append(
                    {
                        "text": content,
                        "style": extract_style(style),
                        "link": link or None,
                    }
                )

            blocks.append(
                {
                    "type": "paragraph",
                    "namedStyleType": named or None,
                    "headingLevel": heading_level,
                    "headingId": heading_id or None,
                    "list": list_info,
                    "runs": runs,
                }
            )
        return blocks

    # Some Google Docs use "Tabs". In that case the content lives under doc_json["tabs"][...]["documentTab"].
    if isinstance(doc_json.get("tabs"), list):
        tabs_out: list[dict[str, Any]] = []
        for t in doc_json.get("tabs") or []:
            if not isinstance(t, dict):
                continue
            tab_id = t.get("tabId") or t.get("id") or t.get("tab_id")
            tab_props = t.get("tabProperties") or {}
            tab_title = t.get("title") or (tab_props.get("title") if isinstance(tab_props, dict) else None)

            tab_root = t.get("documentTab") if isinstance(t.get("documentTab"), dict) else t
            body = (tab_root.get("body") or {}).get("content") or []
            lists = tab_root.get("lists") or doc_json.get("lists") or {}
            tabs_out.append({"tabId": tab_id, "title": tab_title, "blocks": parse_blocks(body=body, lists=lists)})

        return {"documentId": doc_json.get("documentId"), "title": doc_json.get("title"), "tabs": tabs_out}

    lists = doc_json.get("lists") or {}
    body = (doc_json.get("body") or {}).get("content") or []
    return {"documentId": doc_json.get("documentId"), "title": doc_json.get("title"), "blocks": parse_blocks(body=body, lists=lists)}


def struct_to_sections(doc: dict[str, Any]) -> dict[str, Any]:
    blocks = doc.get("blocks") or []

    def block_text(b: dict[str, Any]) -> str:
        return "".join((r.get("text") or "") for r in (b.get("runs") or []))

    sections: list[dict[str, Any]] = []
    current = {"title": None, "level": 0, "blocks": []}
    sections.append(current)

    for b in blocks:
        level = b.get("headingLevel")
        if isinstance(level, int) and level >= 1:
            current = {"title": block_text(b).strip() or None, "level": level, "blocks": []}
            sections.append(current)
            continue
        current["blocks"].append(b)

    out = dict(doc)
    out["sections"] = sections
    return out


def blocks_to_outline(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def block_text(b: dict[str, Any]) -> str:
        return "".join((r.get("text") or "") for r in (b.get("runs") or []))

    root: dict[str, Any] = {"level": 0, "children": []}
    stack: list[dict[str, Any]] = [root]

    for idx, b in enumerate(blocks):
        level = b.get("headingLevel")
        if not isinstance(level, int) or level < 1:
            continue
        node: dict[str, Any] = {
            "title": block_text(b).strip() or None,
            "level": level,
            "headingId": b.get("headingId"),
            "blockIndex": idx,
            "children": [],
        }
        while stack and int(stack[-1].get("level") or 0) >= level:
            stack.pop()
        if not stack:
            stack = [root]
        stack[-1]["children"].append(node)
        stack.append(node)

    return root["children"]


def enrich_struct(doc: dict[str, Any]) -> dict[str, Any]:
    if isinstance(doc.get("tabs"), list):
        tabs = []
        for tab in doc["tabs"]:
            if not isinstance(tab, dict):
                continue
            blocks = tab.get("blocks") or []
            enriched = struct_to_sections(tab)
            enriched["outline"] = blocks_to_outline(blocks)
            tabs.append(enriched)
        out = dict(doc)
        out["tabs"] = tabs
        return out

    blocks = doc.get("blocks") or []
    out = struct_to_sections(doc)
    out["outline"] = blocks_to_outline(blocks)
    return out


def docx_to_struct(data: bytes, *, file_id: str | None = None, title: str | None = None) -> dict[str, Any]:
    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        doc_xml = zf.read("word/document.xml")
    except KeyError:
        raise SystemExit("DOCX missing word/document.xml") from None

    rels: dict[str, str] = {}
    try:
        rels_xml = zf.read("word/_rels/document.xml.rels")
        rel_root = ET.fromstring(rels_xml)
        for rel in rel_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            rid = rel.attrib.get("Id") or ""
            target = rel.attrib.get("Target") or ""
            mode = rel.attrib.get("TargetMode") or ""
            if rid and target and mode.lower() == "external":
                rels[rid] = target
    except KeyError:
        pass

    ns = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    root = ET.fromstring(doc_xml)

    def style_to_level(p_style: str) -> int | None:
        style_norm = (p_style or "").lower()
        if style_norm == "title":
            return 1
        if style_norm == "subtitle":
            return 2
        if style_norm.startswith("heading"):
            level_str = "".join(ch for ch in p_style if ch.isdigit())
            level = int(level_str) if level_str else 1
            return max(1, min(6, level))
        return None

    blocks: list[dict[str, Any]] = []
    for p in root.findall(".//w:body/w:p", ns):
        p_style = ""
        ppr = p.find("w:pPr", ns)
        if ppr is not None:
            ps = ppr.find("w:pStyle", ns)
            if ps is not None:
                p_style = ps.attrib.get(f"{{{ns['w']}}}val", "") or ""

        heading_level = style_to_level(p_style)

        list_info: dict[str, Any] | None = None
        if ppr is not None:
            num_pr = ppr.find("w:numPr", ns)
            if num_pr is not None:
                ilvl = num_pr.find("w:ilvl", ns)
                nesting = 0
                if ilvl is not None:
                    nesting = int(ilvl.attrib.get(f"{{{ns['w']}}}val", "0") or 0)
                list_info = {"nestingLevel": nesting, "ordered": None}

        runs: list[dict[str, Any]] = []

        def run_style(r: ET.Element) -> dict[str, Any]:
            rpr = r.find("w:rPr", ns)
            bold = italic = strike = underline = False
            font_family: str | None = None
            font_size_pt: float | None = None
            foreground_color: str | None = None
            if rpr is not None:
                rfonts = rpr.find("w:rFonts", ns)
                if rfonts is not None:
                    ascii_font = rfonts.attrib.get(f"{{{ns['w']}}}ascii")
                    hansi_font = rfonts.attrib.get(f"{{{ns['w']}}}hAnsi")
                    font_family = (ascii_font or hansi_font or None)

                sz = rpr.find("w:sz", ns)
                if sz is not None:
                    raw = sz.attrib.get(f"{{{ns['w']}}}val")
                    try:
                        # DOCX stores half-points
                        font_size_pt = int(raw) / 2.0 if raw is not None else None
                    except Exception:
                        font_size_pt = None

                col = rpr.find("w:color", ns)
                if col is not None:
                    val = (col.attrib.get(f"{{{ns['w']}}}val") or "").strip()
                    if val and val.lower() != "auto" and len(val) in (6, 8):
                        # Usually RRGGBB; sometimes AARRGGBB. Keep last 6.
                        foreground_color = "#" + val[-6:].upper()

                b = rpr.find("w:b", ns)
                if b is not None and (b.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    bold = True
                i = rpr.find("w:i", ns)
                if i is not None and (i.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    italic = True
                s = rpr.find("w:strike", ns)
                if s is not None and (s.attrib.get(f"{{{ns['w']}}}val", "1") != "0"):
                    strike = True
                u = rpr.find("w:u", ns)
                if u is not None and (u.attrib.get(f"{{{ns['w']}}}val", "single") != "none"):
                    underline = True
            return {
                "bold": bold,
                "italic": italic,
                "underline": underline,
                "strikethrough": strike,
                "fontFamily": font_family,
                "fontSize": {"magnitude": font_size_pt, "unit": "PT"} if font_size_pt is not None else None,
                "foregroundColor": foreground_color,
                "backgroundColor": None,
            }

        def run_text(r: ET.Element) -> str:
            parts: list[str] = []
            for node in r:
                if node.tag == f"{{{ns['w']}}}t" and node.text:
                    parts.append(node.text)
                elif node.tag == f"{{{ns['w']}}}tab":
                    parts.append("\t")
                elif node.tag == f"{{{ns['w']}}}br":
                    parts.append("\n")
            return "".join(parts)

        for child in p:
            if child.tag == f"{{{ns['w']}}}r":
                txt = run_text(child)
                if txt:
                    runs.append({"text": txt, "style": run_style(child), "link": None})
            elif child.tag == f"{{{ns['w']}}}hyperlink":
                rid = child.attrib.get(f"{{{ns['r']}}}id", "")
                link_url = rels.get(rid) if rid else None
                for r in child.findall("w:r", ns):
                    txt = run_text(r)
                    if txt:
                        runs.append({"text": txt, "style": run_style(r), "link": link_url})

        blocks.append(
            {
                "type": "paragraph",
                "namedStyleType": p_style or None,
                "headingLevel": heading_level,
                "list": list_info,
                "runs": runs,
            }
        )

    return enrich_struct({"documentId": file_id, "title": title, "blocks": blocks})


def drive_get_text_smart(*, file_id: str, access_token: str, output_format: str) -> tuple[str, str]:
    resolved_id, meta = drive_resolve_target(file_id=file_id, access_token=access_token)
    name = meta.get("name") or resolved_id
    mime = meta.get("mimeType") or ""

    if mime == "application/vnd.google-apps.document":
        if output_format == "plain":
            return name, drive_export_plain_text(file_id=resolved_id, access_token=access_token)
        docx = drive_export_bytes(
            file_id=resolved_id,
            access_token=access_token,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return name, extract_markdown_from_docx(docx)

    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw = drive_download_bytes(file_id=resolved_id, access_token=access_token)
        if output_format == "plain":
            return name, extract_text_from_docx(raw)
        return name, extract_markdown_from_docx(raw)

    raise SystemExit(f"Unsupported Drive mimeType for printing: {mime} (file: {resolved_id})")


def cmd_list(args: argparse.Namespace) -> int:
    links = parse_doc_links(read_text(args.links_file))
    for link in links:
        print(f"{link.name}\t{link.document_id}\t{link.url}")
    return 0


def cmd_auth(args: argparse.Namespace) -> int:
    client = load_oauth_client(args.client)
    oauth_authorize_interactive(client=client, token_path=args.token, scopes=args.scopes)
    return 0


def cmd_print(args: argparse.Namespace) -> int:
    client = load_oauth_client(args.client)
    access_token = ensure_access_token(client=client, token_path=args.token)
    links = parse_doc_links(read_text(args.links_file))

    if args.doc:
        by_name = {d.name: d for d in links}
        if args.doc not in by_name:
            raise SystemExit(f"Unknown --doc {args.doc!r}. Use `list` to see available names.")
        links = [by_name[args.doc]]

    def render_one(link: DocLink) -> dict[str, Any] | None:
        if args.method in ("docs", "auto"):
            try:
                doc = get_doc(document_id=link.document_id, access_token=access_token)
                if args.format == "plain":
                    title = doc.get("title") or link.name
                    print(f"===== {title} ({link.document_id}) =====")
                    print("".join(iter_text_runs(doc)).rstrip())
                    print()
                    return None
                if args.format == "md":
                    title = doc.get("title") or link.name
                    print(f"===== {title} ({link.document_id}) =====")
                    print(docs_to_markdown(doc).rstrip())
                    print()
                    return None

                structured = enrich_struct(docs_to_struct(doc))
                structured["source"] = {"method": "docs_api"}
                return structured
            except HTTPError as exc:
                if args.method == "docs":
                    raise SystemExit(f"Docs API error HTTP {exc.code}: {exc.msg}") from None
                eprint(f"Docs API failed for {link.name} (HTTP {exc.code}): {exc.msg}")
                eprint("Trying Drive fallback...")

        try:
            if args.format in ("plain", "md"):
                title, text = drive_get_text_smart(
                    file_id=link.document_id,
                    access_token=access_token,
                    output_format=args.format,
                )
                print(f"===== {title} ({link.document_id}) =====")
                print(text.rstrip())
                print()
                return None

            resolved_id, meta = drive_resolve_target(file_id=link.document_id, access_token=access_token)
            mime = meta.get("mimeType") or ""
            name = meta.get("name") or link.name

            if mime == "application/vnd.google-apps.document":
                docx = drive_export_bytes(
                    file_id=resolved_id,
                    access_token=access_token,
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                structured = docx_to_struct(docx, file_id=link.document_id, title=name)
                structured["source"] = {"method": "drive_export_docx", "mimeType": mime, "resolvedFileId": resolved_id}
                return structured

            if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                raw = drive_download_bytes(file_id=resolved_id, access_token=access_token)
                structured = docx_to_struct(raw, file_id=link.document_id, title=name)
                structured["source"] = {"method": "drive_download_docx", "mimeType": mime, "resolvedFileId": resolved_id}
                return structured

            raise SystemExit(f"Unsupported Drive mimeType for JSON output: {mime} (file: {resolved_id})")
        except HTTPError as exc:
            raise SystemExit(f"Drive error HTTP {exc.code}: {exc.msg}") from None

    results: list[dict[str, Any]] = []
    for link in links:
        rendered = render_one(link)
        if rendered is not None:
            results.append(rendered)

    if args.format == "json":
        if args.doc and len(results) == 1:
            print(json.dumps(results[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


def cmd_replace(args: argparse.Namespace) -> int:
    client = load_oauth_client(args.client)
    require_scopes(args.token, ["https://www.googleapis.com/auth/documents"])
    access_token = ensure_access_token(client=client, token_path=args.token)
    links = parse_doc_links(read_text(args.links_file))

    by_name = {d.name: d for d in links}
    if args.doc not in by_name:
        raise SystemExit(f"Unknown --doc {args.doc!r}. Use `list` to see available names.")
    link = by_name[args.doc]

    req = {
        "replaceAllText": {
            "containsText": {"text": args.from_text, "matchCase": bool(args.match_case)},
            "replaceText": args.to_text,
        }
    }

    try:
        resp = docs_batch_update(document_id=link.document_id, access_token=access_token, requests=[req])
    except HTTPError as exc:
        msg = exc.msg
        if exc.code in (401, 403):
            msg += "\nLikely missing scope; re-run: python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents"
        raise SystemExit(f"Docs batchUpdate failed HTTP {exc.code}: {msg}") from None

    # Google returns replies + writeControl. We keep output small unless requested.
    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        replies = resp.get("replies") or []
        print(f"OK. replaceAllText applied. replies={len(replies)} doc={link.name} id={link.document_id}")
    return 0


def cmd_apply_template(args: argparse.Namespace) -> int:
    client = load_oauth_client(args.client)
    require_scopes(args.token, ["https://www.googleapis.com/auth/documents"])
    access_token = ensure_access_token(client=client, token_path=args.token)

    links = parse_doc_links(read_text(args.links_file))
    by_name = {d.name: d for d in links}
    if args.doc not in by_name:
        raise SystemExit(f"Unknown --doc {args.doc!r}. Use `list` to see available names.")
    link = by_name[args.doc]

    data = read_json(args.data)
    if isinstance(data, dict) and isinstance(data.get("replacements"), dict):
        replacements = data["replacements"]
    elif isinstance(data, dict):
        # allow {"{{A}}":"b"} directly
        replacements = data
    else:
        raise SystemExit("Template data must be a JSON object or {\"replacements\": {...}}")

    requests: list[dict[str, Any]] = []
    for k, v in replacements.items():
        if not isinstance(k, str):
            continue
        if v is None:
            v = ""
        if not isinstance(v, str):
            v = str(v)
        requests.append(
            {
                "replaceAllText": {
                    "containsText": {"text": k, "matchCase": bool(args.match_case)},
                    "replaceText": v,
                }
            }
        )

    if not requests:
        raise SystemExit("No replacements to apply.")

    if args.dry_run:
        print(json.dumps({"document": link.name, "documentId": link.document_id, "requests": requests}, ensure_ascii=False, indent=2))
        return 0

    try:
        resp = docs_batch_update(document_id=link.document_id, access_token=access_token, requests=requests)
    except HTTPError as exc:
        msg = exc.msg
        if exc.code in (401, 403):
            msg += "\nLikely missing scope; re-run: python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents"
        raise SystemExit(f"Docs batchUpdate failed HTTP {exc.code}: {msg}") from None

    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        replies = resp.get("replies") or []
        print(f"OK. Applied {len(requests)} replacements. replies={len(replies)} doc={link.name} id={link.document_id}")
    return 0


def cmd_export_docx(args: argparse.Namespace) -> int:
    client = load_oauth_client(args.client)
    require_scopes(args.token, ["https://www.googleapis.com/auth/drive.readonly"])
    access_token = ensure_access_token(client=client, token_path=args.token)

    links = parse_doc_links(read_text(args.links_file))
    by_name = {d.name: d for d in links}
    if args.doc not in by_name:
        raise SystemExit(f"Unknown --doc {args.doc!r}. Use `list` to see available names.")
    link = by_name[args.doc]

    resolved_id, meta = drive_resolve_target(file_id=link.document_id, access_token=access_token)
    mime = meta.get("mimeType") or ""
    if mime == "application/vnd.google-apps.document":
        raw = drive_export_bytes(
            file_id=resolved_id,
            access_token=access_token,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw = drive_download_bytes(file_id=resolved_id, access_token=access_token)
    else:
        raise SystemExit(f"Unsupported mimeType for DOCX export: {mime}")

    write_bytes(args.out, raw)
    print(f"OK. Wrote DOCX to {args.out}")
    return 0


def cmd_import_md(args: argparse.Namespace) -> int:
    md_path = args.md
    if not os.path.exists(md_path):
        raise SystemExit(f"Markdown file not found: {md_path}")
    if args.reference_docx and not os.path.exists(args.reference_docx):
        raise SystemExit(f"Reference DOCX not found: {args.reference_docx}")

    docx_out = args.docx_out or os.path.join(".tmp", "rendered.docx")
    os.makedirs(os.path.dirname(os.path.abspath(docx_out)), exist_ok=True)
    render_markdown_to_docx(
        md_path,
        docx_out,
        args.reference_docx,
        normalize_lists=not args.preserve_list_spacing,
    )

    if args.dry_run:
        print(f"OK. Rendered DOCX to {docx_out} (dry-run, not uploaded).")
        return 0

    if not args.doc and not args.name:
        raise SystemExit("Provide --doc to update an existing document or --name to create a new one.")

    client = load_oauth_client(args.client)
    require_scopes(args.token, ["https://www.googleapis.com/auth/drive"])
    access_token = ensure_access_token(client=client, token_path=args.token)

    with open(docx_out, "rb") as f:
        docx_bytes = f.read()

    metadata: dict[str, Any] = {"mimeType": "application/vnd.google-apps.document"}
    if args.name:
        metadata["name"] = args.name

    if args.doc:
        links = parse_doc_links(read_text(args.links_file))
        by_name = {d.name: d for d in links}
        if args.doc not in by_name:
            raise SystemExit(f"Unknown --doc {args.doc!r}. Use `list` to see available names.")
        link = by_name[args.doc]
        url = f"{DRIVE_UPLOAD_BASE}/files/{link.document_id}?uploadType=multipart"
        resp = drive_upload_multipart(
            access_token=access_token,
            url=url,
            metadata=metadata,
            media_bytes=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            method="PATCH",
        )
        doc_id = resp.get("id") or link.document_id
        print(f"OK. Updated doc {link.name} ({doc_id}).")
    else:
        url = f"{DRIVE_UPLOAD_BASE}/files?uploadType=multipart"
        resp = drive_upload_multipart(
            access_token=access_token,
            url=url,
            metadata=metadata,
            media_bytes=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            method="POST",
        )
        doc_id = resp.get("id")
        name = resp.get("name") or args.name or "Untitled"
        print(f"OK. Created doc {name} ({doc_id}).")
    return 0


def cmd_token_info(args: argparse.Namespace) -> int:
    try:
        token = read_json(args.token)
    except FileNotFoundError:
        raise SystemExit(f"Token file not found: {args.token}. Run `auth` first.") from None
    out = {
        "token_path": args.token,
        "scope": token.get("scope"),
        "expires_at": token.get("expires_at"),
        "has_refresh_token": bool(token.get("refresh_token")),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Google Docs CLI (OAuth) - print docs content")
    p.add_argument(
        "--client",
        default=os.environ.get("GDOCS_OAUTH_CLIENT", ".secrets/google-oauth-client.json"),
        help="Path to OAuth client JSON (default: .secrets/google-oauth-client.json or $GDOCS_OAUTH_CLIENT)",
    )
    p.add_argument(
        "--token",
        default=os.environ.get("GDOCS_TOKEN", ".secrets/google-token.json"),
        help="Path to token cache (default: .secrets/google-token.json or $GDOCS_TOKEN)",
    )
    p.add_argument(
        "--links-file",
        default=os.path.join(ROOT_DIR, "docs", "resources", "GOOGLE_DOCS_LINKS.md"),
        help="Markdown file with doc links (default: docs/resources/GOOGLE_DOCS_LINKS.md)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List documents parsed from links file")
    p_list.set_defaults(func=cmd_list)

    p_auth = sub.add_parser("auth", help="Run interactive OAuth and save token")
    p_auth.add_argument(
        "--scopes",
        nargs="+",
        default=[
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
        help="OAuth scopes (default: documents.readonly + drive.readonly)",
    )
    p_auth.set_defaults(func=cmd_auth)

    p_print = sub.add_parser("print", help="Print document(s) plain text to stdout")
    p_print.add_argument("--doc", help="Document name (as in links file) to print only one")
    p_print.add_argument(
        "--format",
        choices=["plain", "md", "json"],
        default="plain",
        help="Output format: plain, md (Markdown-like), or json (structured) (default: plain)",
    )
    p_print.add_argument(
        "--method",
        choices=["auto", "docs", "drive"],
        default="auto",
        help="How to fetch text: auto=Docs API then Drive export fallback (default: auto)",
    )
    p_print.set_defaults(func=cmd_print)

    p_replace = sub.add_parser("replace", help="Replace text in a Google Doc via Docs API (replaceAllText)")
    p_replace.add_argument("--doc", required=True, help="Document name (as in links file)")
    p_replace.add_argument("--from", dest="from_text", required=True, help="Text to search for")
    p_replace.add_argument("--to", dest="to_text", required=True, help="Replacement text")
    p_replace.add_argument("--match-case", action="store_true", help="Match case (default: false)")
    p_replace.add_argument("--json", action="store_true", help="Print full API response as JSON")
    p_replace.set_defaults(func=cmd_replace)

    p_apply = sub.add_parser("apply", help="Apply many replacements from JSON via Docs API")
    p_apply.add_argument("--doc", required=True, help="Document name (as in links file)")
    p_apply.add_argument("--data", required=True, help="Path to JSON with replacements")
    p_apply.add_argument("--match-case", action="store_true", help="Match case (default: false)")
    p_apply.add_argument("--dry-run", action="store_true", help="Print requests JSON without changing the document")
    p_apply.add_argument("--json", action="store_true", help="Print full API response as JSON")
    p_apply.set_defaults(func=cmd_apply_template)

    p_export_docx = sub.add_parser("export-docx", help="Export a Google Doc as DOCX via Drive API")
    p_export_docx.add_argument("--doc", required=True, help="Document name (as in links file)")
    p_export_docx.add_argument("--out", required=True, help="Output DOCX path")
    p_export_docx.set_defaults(func=cmd_export_docx)

    p_import_md = sub.add_parser("import-md", help="Render Markdown to DOCX (pandoc) and upload to Google Docs")
    p_import_md.add_argument("md", help="Path to Markdown file")
    p_import_md.add_argument("--doc", help="Document name to update (as in links file)")
    p_import_md.add_argument("--name", help="Name for a new document (or rename existing)")
    p_import_md.add_argument("--reference-docx", help="DOCX with styles for pandoc (optional)")
    p_import_md.add_argument("--docx-out", help="Where to write rendered DOCX (default: .tmp/rendered.docx)")
    p_import_md.add_argument("--dry-run", action="store_true", help="Only render DOCX, do not upload")
    p_import_md.add_argument(
        "--preserve-list-spacing",
        action="store_true",
        help="Keep blank lines inside lists (default: normalize to tight lists)",
    )
    p_import_md.set_defaults(func=cmd_import_md)

    p_token = sub.add_parser("token-info", help="Show cached token scopes/expiry")
    p_token.set_defaults(func=cmd_token_info)

    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
