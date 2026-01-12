# Markdown -> DOCX -> Google Docs (styled)

Idea: store CV content in Markdown, render DOCX locally (pandoc),
then upload and convert to Google Docs while keeping headings/lists/styles.

## 1) Requirements

- `pandoc` in PATH (you already have `/opt/homebrew/bin/pandoc`).
- OAuth token with **Drive write** scope:

```bash
python3 gdocs_cli.py auth --scopes \
  https://www.googleapis.com/auth/drive \
  https://www.googleapis.com/auth/documents
```

## 2) Reference DOCX (style template)

Pandoc can apply styles from a reference DOCX. Recommended flow:

1. Create a Google Doc "Style Master" (or reuse the HRD doc).
2. Tune heading/paragraph/list styles (fonts, spacing, indents).
3. Export to DOCX:

```bash
python3 gdocs_cli.py export-docx \
  --doc "Stan Sobolev_HRD_2025" \
  --out templates/cv.reference.docx
```

This file controls the visual style.

### Make blocky bullet lists

Pandoc uses the `Compact` paragraph style for tight bullet lists.
We can patch that style to look like blocks (shaded background + left border).

```bash
python3 scripts/style_reference_docx.py \
  --in templates/cv.reference.docx \
  --out templates/cv.reference.block.docx
```

Use the `templates/cv.reference.block.docx` as your reference.

## 3) Markdown structure (minimal)

- `#` / `##` / `###` -> Heading 1/2/3
- `-` / `*` -> bullet lists

By default, `import-md` normalizes lists to "tight" (removes blank lines between items),
so blocky bullet styling always applies. Use `--preserve-list-spacing` if you want to
keep blank lines inside lists.
- `**bold**`, `*italic*` preserved

Example: `templates/cv.md.example`.

## 4) Render and upload

Update an existing document:

```bash
python3 gdocs_cli.py import-md \
  templates/cv.md.example \
  --doc "Stan Sobolev_HRD_2025" \
  --reference-docx templates/cv.reference.block.docx
```

Create a new document:

```bash
python3 gdocs_cli.py import-md \
  templates/cv.md.example \
  --name "Stan Sobolev_HRD_2025" \
  --reference-docx templates/cv.reference.block.docx
```

Render DOCX only (no upload):

```bash
python3 gdocs_cli.py import-md \
  templates/cv.md.example \
  --reference-docx templates/cv.reference.block.docx \
  --docx-out .tmp/cv.rendered.docx \
  --dry-run
```

## 5) Style tips

- Heading 1: 16-18 pt, bold, extra spacing above.
- Heading 2: 13-14 pt, bold.
- Body: 10.5-11 pt, line spacing 1.1-1.2.
- Bullets: compact spacing, no empty rows.

Edit styles in Google Docs, then re-export the reference DOCX.
