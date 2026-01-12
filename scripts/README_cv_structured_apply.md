# cv_structured_apply.py

Apply structured CV JSON data to a Google Docs template and then style sections (skills, experience, education).

## What it does

- Builds replacements from a structured JSON file.
- Applies replacements to a Google Doc via `gdocs_cli.py`.
- Styles sections and bullets in the doc.
- Stores state in `.cv_apply_state.json` for reset mode.

## Requirements

- Python 3.10+
- OAuth files:
  - Client: `.secrets/google-oauth-client.json` (or `$GDOCS_OAUTH_CLIENT`)
  - Token: `.secrets/google-token.json` (or `$GDOCS_TOKEN`)

## Google Docs links file

Default lookup file is `docs/resources/GOOGLE_DOCS_LINKS.md`.

## Examples

Generate replacements JSON only:

```bash
python3 scripts/cv_structured_apply.py --data path/to/structured.json --out /tmp/replacements.json
```

Apply to a doc by name (from links file):

```bash
python3 scripts/cv_structured_apply.py \
  --data path/to/structured.json \
  --doc "CV - English" \
  --links-file docs/resources/GOOGLE_DOCS_LINKS.md \
  --gdocs-cli scripts/gdocs_cli.py
```

Dry-run (show requests without changing the doc):

```bash
python3 scripts/cv_structured_apply.py \
  --data path/to/structured.json \
  --doc "CV - English" \
  --links-file docs/resources/GOOGLE_DOCS_LINKS.md \
  --gdocs-cli scripts/gdocs_cli.py \
  --dry-run
```

Reset a doc back to placeholder anchors (uses saved state):

```bash
python3 scripts/cv_structured_apply.py \
  --doc "CV - English" \
  --links-file docs/resources/GOOGLE_DOCS_LINKS.md \
  --gdocs-cli scripts/gdocs_cli.py \
  --reset
```

## Notes

- If auth is expired, the script can re-run OAuth automatically (default `--auto-auth`).
- Placeholders used by the script include `{{SUMMARY}}`, `{{skills}}`, `{{exps}}`, `{{education}}`,
  `{{entrepreneurship}}`, `{{publications}}`, plus header fields like `{{fullname}}`.
