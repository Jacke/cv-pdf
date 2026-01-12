#!/usr/bin/env python3
from __future__ import annotations

import curses
import os
import textwrap
from dataclasses import dataclass
from typing import Any

import gdocs_cli


@dataclass(frozen=True)
class DocItem:
    name: str
    document_id: str
    url: str


class App:
    def __init__(self, stdscr: "curses._CursesWindow", *, client_path: str, token_path: str, links_file: str):
        self.stdscr = stdscr
        self.client_path = client_path
        self.token_path = token_path
        self.links_file = links_file

        self.client: gdocs_cli.OAuthClient | None = None
        self.items: list[DocItem] = []
        self.selected = 0
        self.status = ""
        self.last_error = ""

        self.meta_cache: dict[str, dict[str, Any]] = {}
        self.view_cache: dict[tuple[str, str], str] = {}
        self.view_cache_struct: dict[str, dict[str, Any]] = {}

        self.mode = "list"  # list | view | help
        self.view_format = "para"  # plain | md | para
        self.view_lines: list[str] = []
        self.view_scroll = 0
        self.active: DocItem | None = None

    def set_status(self, msg: str) -> None:
        self.status = msg

    def set_error(self, msg: str) -> None:
        self.last_error = msg
        self.status = msg

    def safe_addstr(self, y: int, x: int, s: str, attr: int = 0) -> None:
        try:
            if attr:
                self.stdscr.addstr(y, x, s, attr)
            else:
                self.stdscr.addstr(y, x, s)
        except curses.error:
            return

    def safe_hline(self, y: int, x: int, ch: int, n: int) -> None:
        try:
            if n > 0:
                self.stdscr.hline(y, x, ch, n)
        except curses.error:
            return

    def ensure_client(self) -> gdocs_cli.OAuthClient | None:
        if self.client is not None:
            return self.client
        try:
            self.client = gdocs_cli.load_oauth_client(self.client_path)
            return self.client
        except BaseException as exc:  # noqa: BLE001
            self.set_error(f"Missing/invalid OAuth client JSON: {exc} (press 'A')")
            return None

    def access_token(self) -> str | None:
        client = self.ensure_client()
        if client is None:
            return None
        try:
            return gdocs_cli.ensure_access_token(client=client, token_path=self.token_path)
        except BaseException as exc:  # noqa: BLE001
            self.set_error(f"Auth required: {exc} (press 'A')")
            return None

    def load_items(self) -> None:
        links_md = gdocs_cli.read_text(self.links_file)
        links = gdocs_cli.parse_doc_links(links_md)
        self.items = [DocItem(name=l.name, document_id=l.document_id, url=l.url) for l in links]
        self.selected = max(0, min(self.selected, len(self.items) - 1))

    def get_meta(self, file_id: str) -> dict[str, Any] | None:
        if file_id in self.meta_cache:
            return self.meta_cache[file_id]
        try:
            token = self.access_token()
            if token is None:
                return None
            meta = gdocs_cli.drive_get_metadata(file_id=file_id, access_token=token)
        except BaseException as exc:  # noqa: BLE001 - show as status
            self.set_error(f"Drive metadata error: {exc}")
            return None
        self.meta_cache[file_id] = meta
        return meta

    def is_editable(self, item: DocItem) -> bool:
        meta = self.get_meta(item.document_id)
        if not meta:
            return False
        return meta.get("mimeType") == "application/vnd.google-apps.document"

    def ensure_write_scope(self) -> bool:
        try:
            gdocs_cli.require_scopes(self.token_path, ["https://www.googleapis.com/auth/documents"])
            return True
        except BaseException as exc:  # noqa: BLE001
            self.set_error(str(exc))
            return False

    def run_auth(self, scopes: list[str]) -> None:
        client = self.ensure_client()
        if client is None:
            return
        curses.endwin()
        try:
            gdocs_cli.oauth_authorize_interactive(
                client=client,
                token_path=self.token_path,
                scopes=scopes,
            )
        finally:
            # Repaint after returning to curses
            self.stdscr.refresh()
            curses.doupdate()

    def prompt(self, title: str, initial: str = "") -> str | None:
        h, w = self.stdscr.getmaxyx()
        win_h = 5
        win_w = min(max(40, len(title) + 10), w - 4)
        y = (h - win_h) // 2
        x = (w - win_w) // 2
        win = curses.newwin(win_h, win_w, y, x)
        win.keypad(True)
        win.border()
        win.addstr(1, 2, title[: win_w - 4])
        win.addstr(2, 2, "> ")
        curses.curs_set(1)
        buf = list(initial)
        pos = len(buf)

        while True:
            win.move(2, 4)
            win.clrtoeol()
            display = "".join(buf)
            if len(display) > win_w - 6:
                display = display[-(win_w - 6) :]
            win.addstr(2, 4, display)
            win.move(2, 4 + min(pos, win_w - 6))
            win.refresh()

            ch = win.getch()
            if ch in (10, 13):  # Enter
                curses.curs_set(0)
                return "".join(buf)
            if ch in (27,):  # ESC
                curses.curs_set(0)
                return None
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                if pos > 0:
                    buf.pop(pos - 1)
                    pos -= 1
                continue
            if ch == curses.KEY_LEFT:
                pos = max(0, pos - 1)
                continue
            if ch == curses.KEY_RIGHT:
                pos = min(len(buf), pos + 1)
                continue
            if ch == curses.KEY_HOME:
                pos = 0
                continue
            if ch == curses.KEY_END:
                pos = len(buf)
                continue
            if 32 <= ch <= 126:
                buf.insert(pos, chr(ch))
                pos += 1

    def open_view(self, item: DocItem) -> None:
        self.active = item
        self.view_scroll = 0
        self.mode = "view"
        self.set_status("Loading...")
        self.render()

        token = self.access_token()
        if token is None:
            self.view_lines = ["Auth required. Press 'A' to authorize.", ""]
            self.set_error("Auth required.")
            return

        if self.view_format == "para":
            try:
                doc = self.get_struct(item, token)
                width = max(20, self.stdscr.getmaxyx()[1] - 2)
                self.view_lines = self.struct_to_para_lines(doc, width=width)
                self.set_status("")
            except BaseException as exc:  # noqa: BLE001
                self.set_error(f"View error: {exc}")
                self.view_lines = []
            return

        key = (item.document_id, self.view_format)
        if key in self.view_cache:
            text = self.view_cache[key]
        else:
            try:
                _, text = gdocs_cli.drive_get_text_smart(
                    file_id=item.document_id,
                    access_token=token,
                    output_format=self.view_format,
                )
            except BaseException as exc:  # noqa: BLE001
                self.set_error(f"View error: {exc}")
                text = ""
            self.view_cache[key] = text
        self.view_lines = text.splitlines()
        self.set_status("")

    def get_struct(self, item: DocItem, token: str) -> dict[str, Any]:
        if item.document_id in self.view_cache_struct:
            return self.view_cache_struct[item.document_id]

        resolved_id, meta = gdocs_cli.drive_resolve_target(file_id=item.document_id, access_token=token)
        mime = meta.get("mimeType") or ""
        name = meta.get("name") or item.name

        if mime == "application/vnd.google-apps.document":
            docx = gdocs_cli.drive_export_bytes(
                file_id=resolved_id,
                access_token=token,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            doc = gdocs_cli.docx_to_struct(docx, file_id=item.document_id, title=name)
        elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            raw = gdocs_cli.drive_download_bytes(file_id=resolved_id, access_token=token)
            doc = gdocs_cli.docx_to_struct(raw, file_id=item.document_id, title=name)
        else:
            raise RuntimeError(f"Unsupported mimeType for paragraph view: {mime}")

        self.view_cache_struct[item.document_id] = doc
        return doc

    def struct_to_para_lines(self, doc: dict[str, Any], *, width: int) -> list[str]:
        def runs_text(runs: list[dict[str, Any]]) -> str:
            return "".join((r.get("text") or "") for r in runs)

        def add_wrapped(lines: list[str], prefix: str, text: str) -> None:
            text = text.replace("\n", " ").strip()
            if not text:
                lines.append("")
                return
            wrapped = textwrap.wrap(text, width=max(10, width - len(prefix)), break_long_words=False) or [""]
            for i, part in enumerate(wrapped):
                if i == 0:
                    lines.append(prefix + part)
                else:
                    lines.append(" " * len(prefix) + part)

        out: list[str] = []

        tabs = doc.get("tabs")
        if isinstance(tabs, list) and tabs:
            for tab in tabs:
                title = (tab.get("title") or "Tab").strip()
                out.append(f"== {title} ==")
                out.append("")
                out.extend(self._sections_to_para_lines(tab.get("sections") or [], width=width))
                out.append("")
            return self._normalize_blank_lines(out, max_blank=2)

        return self._normalize_blank_lines(self._sections_to_para_lines(doc.get("sections") or [], width=width), max_blank=2)

    def _sections_to_para_lines(self, sections: list[dict[str, Any]], *, width: int) -> list[str]:
        def runs_text(runs: list[dict[str, Any]]) -> str:
            return "".join((r.get("text") or "") for r in runs)

        def add_wrapped(lines: list[str], prefix: str, text: str) -> None:
            text = text.replace("\n", " ").strip()
            if not text:
                lines.append("")
                return
            wrapped = textwrap.wrap(text, width=max(10, width - len(prefix)), break_long_words=False) or [""]
            for i, part in enumerate(wrapped):
                if i == 0:
                    lines.append(prefix + part)
                else:
                    lines.append(" " * len(prefix) + part)

        out: list[str] = []

        def ensure_trailing_blanks(n: int) -> None:
            if n <= 0:
                return
            blank_count = 0
            for line in reversed(out):
                if line.strip() == "":
                    blank_count += 1
                else:
                    break
            while blank_count < n:
                out.append("")
                blank_count += 1

        def last_non_blank_line() -> str | None:
            for line in reversed(out):
                if line.strip() != "":
                    return line
            return None

        for sec in sections:
            title = (sec.get("title") or "").strip()
            level = int(sec.get("level") or 0)
            if title and level > 0:
                # Add spacing before headings so different levels (#/##/###) are visually separated.
                if out:
                    prev = last_non_blank_line() or ""
                    if prev.startswith("#"):
                        ensure_trailing_blanks(2)
                    else:
                        ensure_trailing_blanks(1)
                out.append("#" * min(6, level) + " " + title)
                ensure_trailing_blanks(1)

            for b in sec.get("blocks") or []:
                runs = b.get("runs") or []
                text = runs_text(runs)

                bullet = b.get("list")
                if isinstance(bullet, dict):
                    nesting = int(bullet.get("nestingLevel") or 0)
                    ordered = bullet.get("ordered")
                    marker = "1. " if ordered else "- "
                    prefix = ("  " * nesting) + marker
                else:
                    prefix = "  "  # paragraph indent

                add_wrapped(out, prefix, text)
                ensure_trailing_blanks(1)

        return out

    def _normalize_blank_lines(self, lines: list[str], *, max_blank: int = 1) -> list[str]:
        out: list[str] = []
        blank = 0
        for line in lines:
            if line.strip() == "":
                blank += 1
                if blank <= max_blank:
                    out.append("")
                continue
            blank = 0
            out.append(line.rstrip())
        while out and out[-1] == "":
            out.pop()
        return out

    def do_replace(self) -> None:
        if not self.active:
            return
        if not self.is_editable(self.active):
            self.set_error("Not editable via Docs API (not a Google Doc). Convert to Google Doc first.")
            return
        if not self.ensure_write_scope():
            self.set_error("Missing write scope; press 'A' to re-auth with documents scope.")
            return

        from_text = self.prompt("Replace FROM (ESC to cancel):")
        if from_text is None or from_text == "":
            self.set_status("Canceled.")
            return
        to_text = self.prompt("Replace TO (ESC to cancel):")
        if to_text is None:
            self.set_status("Canceled.")
            return

        self.set_status("Applying replace...")
        self.render()
        req = {
            "replaceAllText": {
                "containsText": {"text": from_text, "matchCase": False},
                "replaceText": to_text,
            }
        }
        try:
            token = self.access_token()
            if token is None:
                self.set_error("Auth required.")
                return
            gdocs_cli.docs_batch_update(
                document_id=self.active.document_id,
                access_token=token,
                requests=[req],
            )
        except BaseException as exc:  # noqa: BLE001
            self.set_error(f"Replace failed: {exc}")
            return

        # Invalidate cached views for this doc
        for fmt in ("plain", "md"):
            self.view_cache.pop((self.active.document_id, fmt), None)
        self.view_cache_struct.pop(self.active.document_id, None)
        self.open_view(self.active)
        self.set_status("OK: replaced.")

    def draw_status_bar(self) -> None:
        h, w = self.stdscr.getmaxyx()
        msg = self.status
        if not msg and self.mode == "list":
            msg = "Enter: view  m: toggle format  A: auth  ?: help  q: quit"
        elif not msg and self.mode == "view":
            msg = "q: back  e: replace  m: toggle format  A: auth(write)  ?: help"
        self.stdscr.attron(curses.A_REVERSE)
        self.safe_addstr(h - 1, 0, (msg[: max(0, w - 1)]).ljust(max(0, w - 1)))
        self.stdscr.attroff(curses.A_REVERSE)

    def render_list(self) -> None:
        h, w = self.stdscr.getmaxyx()
        title = f"Google Docs TUI  |  format={self.view_format}  |  links={self.links_file}  token={self.token_path}"
        self.safe_addstr(0, 0, title[: max(0, w - 1)])
        self.safe_hline(1, 0, curses.ACS_HLINE, w - 1)

        if not self.items:
            self.safe_addstr(3, 2, "No documents found in links file.")
            return

        top = max(0, self.selected - (h - 6) // 2)
        bottom = min(len(self.items), top + (h - 3))
        for idx in range(top, bottom):
            item = self.items[idx]
            line = item.name
            meta = self.meta_cache.get(item.document_id)
            if meta and meta.get("mimeType"):
                mt = meta["mimeType"]
                short = "gdoc" if mt == "application/vnd.google-apps.document" else ("docx" if mt.endswith("wordprocessingml.document") else mt.split(".")[-1])
                line = f"{line}  [{short}]"
            y = 2 + (idx - top)
            if idx == self.selected:
                self.stdscr.attron(curses.A_REVERSE)
                self.safe_addstr(y, 0, line[: max(0, w - 1)].ljust(max(0, w - 1)))
                self.stdscr.attroff(curses.A_REVERSE)
            else:
                self.safe_addstr(y, 0, line[: max(0, w - 1)])

    def render_view(self) -> None:
        h, w = self.stdscr.getmaxyx()
        if not self.active:
            self.mode = "list"
            return
        meta = self.meta_cache.get(self.active.document_id) or {}
        mt = meta.get("mimeType") or ""
        editable = "editable" if self.is_editable(self.active) else "read-only"
        header = f"{self.active.name}  |  format={self.view_format}  |  {editable}  |  {mt}"
        self.safe_addstr(0, 0, header[: max(0, w - 1)])
        self.safe_hline(1, 0, curses.ACS_HLINE, w - 1)

        usable_h = h - 3
        self.view_scroll = max(0, min(self.view_scroll, max(0, len(self.view_lines) - usable_h)))
        for i in range(usable_h):
            y = 2 + i
            idx = self.view_scroll + i
            self.stdscr.move(y, 0)
            self.stdscr.clrtoeol()
            if idx >= len(self.view_lines):
                continue
            line = self.view_lines[idx]
            # Show markdown as-is; wrap long lines for readability
            if len(line) <= w - 1:
                self.safe_addstr(y, 0, line[: max(0, w - 1)])
            else:
                self.safe_addstr(y, 0, (line[: max(0, w - 2)] + "…")[: max(0, w - 1)])

    def render_help(self) -> None:
        h, w = self.stdscr.getmaxyx()
        lines = [
            "Keys:",
            "  Up/Down        Move selection / scroll",
            "  Enter          View selected document",
            "  q              Quit / back",
            "  m              Toggle view format (plain/md)",
            "                 (cycles: plain -> md -> para)",
            "                 (if your keyboard layout is RU, use F2 instead of 'm')",
            "  e              Replace text in Google Doc (Docs API)",
            "  A              OAuth auth (view: documents+drive readonly; edit: documents write)",
            "  r              Reload links file",
            "  d              Show last error (full)",
            "  F2             Toggle view format (safe for RU layout)",
            "",
            "Notes:",
            "  - Viewing uses Drive API (export/download) and works for Google Docs and DOCX.",
            "  - Editing works only for Google Docs (mimeType application/vnd.google-apps.document).",
            f"  - Links: {self.links_file}",
            f"  - Token: {self.token_path}",
            "",
            "Press any key to close help.",
        ]
        y = 0
        for line in lines:
            for wrapped in textwrap.wrap(line, width=max(20, w - 2)) or [""]:
                if y >= h - 1:
                    break
                self.safe_addstr(y, 0, wrapped[: max(0, w - 1)])
                y += 1

    def show_text_popup(self, title: str, text: str) -> None:
        h, w = self.stdscr.getmaxyx()
        win_h = min(h - 2, max(8, h // 2))
        win_w = min(w - 2, max(40, w - 4))
        y0 = (h - win_h) // 2
        x0 = (w - win_w) // 2
        win = curses.newwin(win_h, win_w, y0, x0)
        win.keypad(True)
        win.border()
        try:
            win.addstr(1, 2, title[: win_w - 4])
        except curses.error:
            pass

        lines: list[str] = []
        for raw in (text or "").splitlines() or ["(empty)"]:
            lines.extend(textwrap.wrap(raw, width=max(10, win_w - 4)) or [""])
        top = 0
        while True:
            for i in range(2, win_h - 2):
                idx = top + (i - 2)
                try:
                    win.move(i, 2)
                    win.clrtoeol()
                except curses.error:
                    continue
                if idx >= len(lines):
                    continue
                try:
                    win.addstr(i, 2, lines[idx][: win_w - 4])
                except curses.error:
                    continue
            try:
                win.addstr(win_h - 2, 2, "Up/Down scroll, any other key close"[: win_w - 4])
            except curses.error:
                pass
            win.refresh()
            ch = win.getch()
            if ch == curses.KEY_UP:
                top = max(0, top - 1)
                continue
            if ch == curses.KEY_DOWN:
                top = min(max(0, len(lines) - (win_h - 4)), top + 1)
                continue
            break

    def render(self) -> None:
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        if h < 5 or w < 20:
            self.safe_addstr(0, 0, "Terminal too small. Resize.")
            self.draw_status_bar()
            self.stdscr.refresh()
            return
        if self.mode == "list":
            self.render_list()
        elif self.mode == "view":
            self.render_view()
        else:
            self.render_help()
        self.draw_status_bar()
        self.stdscr.refresh()

    def toggle_format(self) -> None:
        order = ["plain", "md", "para"]
        try:
            idx = order.index(self.view_format)
        except ValueError:
            idx = 0
        self.view_format = order[(idx + 1) % len(order)]
        if self.mode == "view" and self.active:
            self.open_view(self.active)

    def loop(self) -> None:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        curses.use_default_colors()

        try:
            self.load_items()
        except BaseException as exc:  # noqa: BLE001
            self.items = []
            self.set_status(f"Failed to read links file: {exc}")
        self.render()

        while True:
            try:
                ch = self.stdscr.get_wch()
            except Exception:  # noqa: BLE001
                ch = self.stdscr.getch()

            if self.mode == "help":
                self.mode = "view" if self.active else "list"
                self.set_status("")
                self.render()
                continue

            if ch in ("?", ord("?")):
                self.mode = "help"
                self.render()
                continue

            if (ch in ("d", "D", ord("d"), ord("D"))) and self.last_error:
                self.show_text_popup("Last error", self.last_error)
                self.render()
                continue

            if ch in ("q", "Q", ord("q"), ord("Q"), 27):  # q / ESC
                if self.mode == "view":
                    self.mode = "list"
                    self.active = None
                    self.view_lines = []
                    self.view_scroll = 0
                    self.set_status("")
                    self.render()
                    continue
                return

            if ch in ("r", "R", ord("r"), ord("R")):
                self.load_items()
                self.set_status("Reloaded links.")
                self.render()
                continue

            if ch in ("m", "M", "ь", "Ь") or ch in (ord("m"), ord("M")) or ch == curses.KEY_F2:
                self.toggle_format()
                self.set_status(f"format={self.view_format}")
                self.render()
                continue

            if ch in ("A", "a", ord("A"), ord("a")):
                if self.mode == "view":
                    scopes = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.readonly"]
                else:
                    scopes = [
                        "https://www.googleapis.com/auth/documents.readonly",
                        "https://www.googleapis.com/auth/drive.readonly",
                    ]
                self.run_auth(scopes)
                self.set_status("Auth finished.")
                # Invalidate caches to ensure new permissions apply
                self.meta_cache.clear()
                self.view_cache.clear()
                if self.mode == "view" and self.active:
                    self.open_view(self.active)
                self.render()
                continue

            if self.mode == "list":
                if ch == curses.KEY_UP:
                    self.selected = max(0, self.selected - 1)
                    self.render()
                    continue
                if ch == curses.KEY_DOWN:
                    self.selected = min(len(self.items) - 1, self.selected + 1)
                    self.render()
                    continue
                if ch in ("\n", "\r", curses.KEY_ENTER, 10, 13) and self.items:  # Enter
                    item = self.items[self.selected]
                    self.open_view(item)
                    self.render()
                    continue
                continue

            if self.mode == "view":
                if ch == curses.KEY_UP:
                    self.view_scroll = max(0, self.view_scroll - 1)
                    self.render()
                    continue
                if ch == curses.KEY_DOWN:
                    self.view_scroll += 1
                    self.render()
                    continue
                if ch == curses.KEY_NPAGE:  # PageDown
                    self.view_scroll += 20
                    self.render()
                    continue
                if ch == curses.KEY_PPAGE:  # PageUp
                    self.view_scroll = max(0, self.view_scroll - 20)
                    self.render()
                    continue
                if ch == curses.KEY_HOME:
                    self.view_scroll = 0
                    self.render()
                    continue
                if ch == curses.KEY_END:
                    self.view_scroll = 10**9
                    self.render()
                    continue
                if ch in ("e", "E", ord("e"), ord("E")):
                    self.do_replace()
                    self.render()
                    continue


def main() -> int:
    client_path = os.environ.get("GDOCS_OAUTH_CLIENT", ".secrets/google-oauth-client.json")
    token_path = os.environ.get("GDOCS_TOKEN", ".secrets/google-token.json")
    links_file = os.environ.get("GDOCS_LINKS_FILE", "GOOGLE_DOCS_LINKS.md")

    def run(stdscr: "curses._CursesWindow") -> None:
        app = App(stdscr, client_path=client_path, token_path=token_path, links_file=links_file)
        app.loop()

    curses.wrapper(run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
