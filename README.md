# Curriculum Vitae

*Tempora mutantur, et nos mutamur in illis.*

<p align="center">
  <img src="./logo.png" alt="CV Apply Logo" width="720"/>
</p>

> **English:** Times change, and we change with them.
>
> **Русский:** Времена меняются, и мы меняемся вместе с ними.
>
> **한국어:** 시간은 흐르고 우리도 그 속에서 변해간다.

---

## Overview

Personal CV management and automation tool that applies structured CV data to Google Docs templates. Python 3.14+, no external dependencies (stdlib only).

## Quick Start

```bash
# Apply CV to Google Doc
python scripts/cv_structured_apply_refactored.py --data cv_components/cv.hard_skills.en.json --doc "Resume"

# Apply with Russian labels
python scripts/cv_structured_apply_refactored.py --data cv_components/cv.default.ru.json --lang ru --doc "Resume"

# Dry run (preview without changes)
python scripts/cv_structured_apply_refactored.py --data cv.json --doc "Resume" --dry-run

# Reset document to placeholders
python scripts/cv_structured_apply_refactored.py --reset --doc "Resume"
```

---

## Project Structure

```
CV/
├── cv_components/           # CV data and A/B testing resources
│   ├── ab_tests/           # Interview preparation & CV variants
│   │   ├── summary.md      # 25 summary variants with pros/cons
│   │   ├── skills.md       # 25 skill set variants (Go/K8s focus)
│   │   ├── exps.md         # Experience achievement variants
│   │   └── legends.md      # 15 interview stories (STAR format)
│   ├── cv.hard_skills.en.json
│   ├── cv.soft_skills.en.json
│   ├── cv.default.ru.json
│   └── ...
├── scripts/
│   ├── cv_structured_apply_refactored.py  # Main entry point
│   ├── cv_apply/           # Core package modules
│   └── gdocs_cli.py        # Google Docs API wrapper
├── docs/                   # Documentation and guides
└── .secrets/               # OAuth credentials (gitignored)
```

---

## CV Profiles

Available CV profiles in `cv_components/`:

| Profile | EN | RU |
|---------|----|----|
| Default (balanced) | `cv.replacements.stanislav_sobolev.json` | `cv.default.ru.json` |
| Hard Skills (Principal/Staff) | `cv.hard_skills.en.json` | `cv.hard_skills.ru.json` |
| Soft Skills (EM/VP) | `cv.soft_skills.en.json` | `cv.soft_skills.ru.json` |

Use `--lang en` or `--lang ru` to set label language (Email/Почта, Tech/Технологии, etc.)

---

## A/B Testing Resources

The `cv_components/ab_tests/` directory contains interview preparation materials and CV optimization variants:

### `summary.md` — 25 Summary Variants

Different approaches for the CV summary section:

| Category | Variants | Best For |
|----------|----------|----------|
| Technical Focus | 1, 7, 9 | Principal/Staff IC roles |
| Business Value | 4, 22 | Management-friendly positions |
| Go/K8s Specialist | 5, 13 | Targeted technical roles |
| Leadership Hybrid | 6, 24 | Tech Lead positions |
| Startup-Friendly | 8, 10, 17 | Early-stage companies |
| Remote-First | 11, 15 | Distributed teams |
| FinTech/Security | 12, 19 | Regulated industries |

Each variant includes:
- Full text of the summary
- **Strengths** — why this approach works
- **Weaknesses** — potential drawbacks

### `skills.md` — 25 Skill Set Variants

Go/Kubernetes-focused skill sections:

| Domain | Variants | Focus Area |
|--------|----------|------------|
| Pure Go | 1, 5, 11, 15 | Language-specific expertise |
| Kubernetes | 2, 6, 23, 24 | Container orchestration |
| Performance | 3, 11, 14 | Optimization & latency |
| Microservices | 4, 13, 24 | Architecture patterns |
| Data/Storage | 7, 14 | Databases & caching |
| Security | 12, 16 | Compliance & encryption |
| Real-Time | 13, 17 | Streaming & messaging |
| Enterprise | 19, 22 | Integration & multi-cloud |

Includes:
- JSON-formatted skill blocks ready for CV
- Recommended keyword lists by category
- Combination strategies for different roles

### `exps.md` — Experience Achievement Variants

Multiple ways to phrase the same achievements:

- **Performance Optimization** — 500ms→59ms, 83x improvement
- **Scale/Load Handling** — 100K+ concurrent users
- **Platform Building** — 40K stores, 160K users
- **Cost Optimization** — 10x infrastructure reduction
- **Framework Development** — Integration time reduction

Each achievement has 5 variants:
1. Metrics-first approach
2. Technical deep-dive
3. Business impact focus
4. STAR format
5. Action verb strong start

### `legends.md` — 15 Interview Stories

Complete interview answers in STAR format:

| Part | Stories | Topics |
|------|---------|--------|
| Technical Challenges | 1-5 | 83x performance, scaling, protocols |
| Leadership & Teamwork | 6-8 | Team building, deadlines, collaboration |
| Failure & Learning | 9-10 | Startup failure, technical mistakes |
| Problem-Solving | 11-12 | Debugging, technology decisions |
| Personal & Behavioral | 13-15 | Learning, work style, motivation |

Each story includes:
- **30-second version** for quick answers
- **2-3 minute STAR version** for full responses
- **Follow-up Q&A** for common drill-down questions

---

## Architecture

The main entry point is `scripts/cv_structured_apply_refactored.py` which orchestrates the `scripts/cv_apply/` package:

```
CV JSON Data → formatters.py (transform sections)
            → document.py (find Google Doc by name)
            → gdocs_cli.py (apply replacements via API)
            → styling.py (add bullets, links, headers)
            → state.py (persist for reset capability)
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `constants.py` | Regexes, OAuth scopes, system constants |
| `utils.py` | JSON I/O, logging, text normalization |
| `formatters.py` | Transform CV sections (summary, skills, experience, education, publications) |
| `translations.py` | Label translations for EN/RU support |
| `document.py` | Parse `docs/resources/GOOGLE_DOCS_LINKS.md` for doc URLs, extract IDs |
| `styling.py` | Apply bullet formatting, hyperlinks, H2 headers |
| `state.py` | Track applied changes in `.cv_apply_state.json` for reset |
| `cli.py` | CLI utilities, Google authentication |
| `reset.py` | Invert replacements to restore placeholders |

---

## CV Data Format

```json
{
  "summary": "Text or {paragraph, about}",
  "skills": [{"title": "Category", "bullets": ["skill1"]}],
  "experiences": [{
    "company": "Name", "dates": "...", "duration": "...",
    "role": "Title", "bullets": ["achievement"], "technologies": "..."
  }],
  "education": [...],
  "publications": [...]
}
```

Template placeholders: `{{fullname}}`, `{{email}}`, `{{SUMMARY}}`, `{{skills}}`, `{{exps}}`, `{{entrepreneurship}}`, `{{education}}`, `{{publications}}`

---

## Key Files

| File | Description |
|------|-------------|
| `docs/resources/GOOGLE_DOCS_LINKS.md` | Document registry mapping names to URLs |
| `cv_components/cv.*.json` | CV data files (profiles) |
| `.cv_apply_state.json` | State tracking for reset operations |
| `.secrets/` | OAuth credentials (gitignored) |
| `scripts/gdocs_cli.py` | Low-level Google Docs API wrapper |

---

## Testing

```bash
# Run unit tests
python scripts/cv_apply/test_formatters.py
```

---

## Notes

- Uses marker-based styling (`<<SKILL_BULLET>>`, `<<EXP_BULLET>>`) for post-processing
- Auto-reauth on token expiry via gdocs_cli.py OAuth flow
- Legacy script `cv_structured_apply.py` exists but use the refactored version

---

## License

Personal use only.
