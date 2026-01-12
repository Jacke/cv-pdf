# CV template placeholders (v1)

Use these placeholders inside your Google Doc template, then apply values with:

`python3 gdocs_cli.py apply --doc "<doc name>" --data templates/cv.replacements.example.json`

Conventions:
- Placeholders are `{{UPPER_SNAKE_CASE}}`
- For bullet lists use numbered placeholders (`..._1`, `..._2`, ...) to preserve bullet formatting
- Unused placeholders can be replaced with empty string

## Header / Contact

- `{{FULL_NAME}}`
- `{{ROLE_TITLE}}` (e.g. "Senior Go Developer")

- `{{CONTACT_EMAIL}}`
- `{{CONTACT_GITHUB}}`
- `{{CONTACT_PHONE}}`
- `{{CONTACT_LOCATION}}`
- `{{CONTACT_TIMEZONE}}`
- `{{CONTACT_AVAILABILITY}}`
- `{{CONTACT_LEGAL_ENTITY}}`
- `{{CONTACT_ENGLISH}}`

## Summary / About

- `{{SUMMARY_PARAGRAPH}}`
- `{{ABOUT_PARAGRAPH}}`

## Skills (optional structure)

- `{{SKILLS_GO_TITLE}}` (e.g. "Go (Back-End)")
- `{{SKILLS_GO_BULLET_1}}`
- `{{SKILLS_GO_BULLET_2}}`
- `{{SKILLS_GO_BULLET_3}}`
- `{{SKILLS_GO_BULLET_4}}`
- `{{SKILLS_GO_BULLET_5}}`

- `{{SKILLS_DB_TITLE}}` (e.g. "Databases & Message Queues")
- `{{SKILLS_DB_BULLET_1}}`
- `{{SKILLS_DB_BULLET_2}}`
- `{{SKILLS_DB_BULLET_3}}`

- `{{SKILLS_DEVOPS_TITLE}}` (e.g. "Infrastructure & DevOps")
- `{{SKILLS_DEVOPS_BULLET_1}}`
- `{{SKILLS_DEVOPS_BULLET_2}}`
- `{{SKILLS_DEVOPS_BULLET_3}}`

- `{{KEY_SKILLS_LINE}}` (one long comma-separated line)

## Experience (generic, 4 positions)

Repeat block `N` = 1..4 (add more if needed):

- `{{EXP_N_COMPANY}}` (e.g. "Mvideo")
- `{{EXP_N_DATES}}` (e.g. "06/2022 – Present")
- `{{EXP_N_DURATION}}` (e.g. "2.5 years")
- `{{EXP_N_COMPANY_DESC}}` (1 line)
- `{{EXP_N_COMPANY_URL}}`

- `{{EXP_N_ROLE}}` (e.g. "Senior Go Developer")
- `{{EXP_N_EMPLOYMENT}}` (e.g. "Full-time")

- `{{EXP_N_BULLET_1}}`
- `{{EXP_N_BULLET_2}}`
- `{{EXP_N_BULLET_3}}`
- `{{EXP_N_BULLET_4}}`
- `{{EXP_N_BULLET_5}}`
- `{{EXP_N_BULLET_6}}`

- `{{EXP_N_TECHNOLOGIES}}` (one line)

## Education

- `{{EDU_DATES}}`
- `{{EDU_SCHOOL}}`
- `{{EDU_DEGREE}}`

## Extras

- `{{HOBBIES_PARAGRAPH}}`

