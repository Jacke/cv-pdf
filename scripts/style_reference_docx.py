#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import zipfile
import xml.etree.ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _w(tag: str) -> str:
    return f"{{{NS['w']}}}{tag}"


def _find_style(root: ET.Element, style_id: str) -> ET.Element | None:
    for style in root.findall("w:style", NS):
        if style.get(_w("styleId")) == style_id:
            return style
    return None


def _ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(f"w:{tag}", NS)
    if child is None:
        child = ET.SubElement(parent, _w(tag))
    return child


def _apply_block_bullet_style(style: ET.Element) -> None:
    ppr = _ensure_child(style, "pPr")

    spacing = _ensure_child(ppr, "spacing")
    spacing.set(_w("before"), "120")
    spacing.set(_w("after"), "120")
    spacing.set(_w("line"), "240")
    spacing.set(_w("lineRule"), "auto")

    ind = _ensure_child(ppr, "ind")
    ind.set(_w("left"), "360")

    p_bdr = _ensure_child(ppr, "pBdr")
    left = p_bdr.find("w:left", NS)
    if left is None:
        left = ET.SubElement(p_bdr, _w("left"))
    left.set(_w("val"), "single")
    left.set(_w("sz"), "12")
    left.set(_w("space"), "8")
    left.set(_w("color"), "D0D4D9")

    shd = _ensure_child(ppr, "shd")
    shd.set(_w("val"), "clear")
    shd.set(_w("color"), "auto")
    shd.set(_w("fill"), "F3F5F7")


def _ensure_style(root: ET.Element, style_id: str, name: str) -> ET.Element:
    style = _find_style(root, style_id)
    if style is not None:
        return style

    style = ET.SubElement(root, _w("style"))
    style.set(_w("type"), "paragraph")
    style.set(_w("styleId"), style_id)
    style.set(_w("customStyle"), "1")

    name_el = ET.SubElement(style, _w("name"))
    name_el.set(_w("val"), name)

    based_on = _find_style(root, "BodyText") or _find_style(root, "Normal")
    if based_on is not None:
        based = ET.SubElement(style, _w("basedOn"))
        based.set(_w("val"), based_on.get(_w("styleId")) or "Normal")

    qfmt = ET.SubElement(style, _w("qFormat"))
    _ = qfmt
    return style


def style_docx(in_path: str, out_path: str) -> None:
    with zipfile.ZipFile(in_path, "r") as zf:
        try:
            styles_xml = zf.read("word/styles.xml")
        except KeyError:
            raise SystemExit("DOCX missing word/styles.xml") from None

        root = ET.fromstring(styles_xml)
        style = _ensure_style(root, "Compact", "Compact")
        _apply_block_bullet_style(style)

        new_styles = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        tmp_out = f"{out_path}.tmp"
        with zipfile.ZipFile(tmp_out, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for item in zf.infolist():
                if item.filename == "word/styles.xml":
                    continue
                out.writestr(item, zf.read(item.filename))
            out.writestr("word/styles.xml", new_styles)

    os.replace(tmp_out, out_path)


def main() -> int:
    p = argparse.ArgumentParser(description="Patch DOCX styles for blocky bullet lists.")
    p.add_argument("--in", dest="in_path", required=True, help="Input DOCX")
    p.add_argument("--out", dest="out_path", required=True, help="Output DOCX")
    args = p.parse_args()

    if not os.path.exists(args.in_path):
        raise SystemExit(f"Input DOCX not found: {args.in_path}")

    style_docx(args.in_path, args.out_path)
    print(f"OK. Wrote styled DOCX to {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
