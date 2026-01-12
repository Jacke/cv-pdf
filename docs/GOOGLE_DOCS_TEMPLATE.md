# Шаблон (template) для Google Docs

Идея: держать один “template” документ в Google Docs с плейсхолдерами, а затем:
- копировать template (Drive API / вручную),
- применять набор замен (Docs API `replaceAllText`) из JSON.

## Плейсхолдеры

Используй уникальные маркеры, которые не встретятся случайно, например:
- `{{FULL_NAME}}`
- `{{SUMMARY}}`
- `{{EXP_MVIDEO_1}}`, `{{EXP_MVIDEO_2}}` …

Для списков лучше заранее сделать нужное количество bullet-строк и поставить плейсхолдер в каждую строку (так сохранится bullet форматирование).

Готовый набор плейсхолдеров (v1): `templates/CV_PLACEHOLDERS.md`.

## Применение замен (CLI)

1) Авторизация с write scope:

```bash
python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive.readonly
```

2) Создай файл замен, например `template.replacements.json`:

```json
{
  "replacements": {
    "{{FULL_NAME}}": "Stanislav Sobolev",
    "{{SUMMARY}}": "Senior Go developer with 8+ years..."
  }
}
```

3) Dry-run (посмотреть какие запросы уйдут):

```bash
python3 gdocs_cli.py apply --doc "Stan Sobolev_HRD_2025" --data template.replacements.json --dry-run
```

4) Применить:

```bash
python3 gdocs_cli.py apply --doc "Stan Sobolev_HRD_2025" --data template.replacements.json
```

Пример replacements файла: `templates/cv.replacements.example.json`.
