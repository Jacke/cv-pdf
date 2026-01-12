# TEMPLATE_USE

Цель: иметь один “шаблон” Google Doc с плейсхолдерами `{{...}}`, а затем быстро генерировать/обновлять версии резюме (HRD/SFT/RU/EN) через API.

## 0) Что уже есть в репозитории

- Ссылки на документы: `GOOGLE_DOCS_LINKS.md`
- CLI для просмотра/редактирования: `gdocs_cli.py`
- TUI для просмотра/replace: `gdocs_tui.py`
- Шаблоны (общая концепция): `docs/GOOGLE_DOCS_TEMPLATE.md`
- Набор плейсхолдеров (v1): `templates/CV_PLACEHOLDERS.md`
- Пример replacements JSON: `templates/cv.replacements.example.json`

## 1) Подготовка OAuth (один раз)

1) Положи OAuth client JSON локально:
- `.secrets/google-oauth-client.json`

2) Авторизуйся:

```bash
python3 gdocs_cli.py auth --scopes \
  https://www.googleapis.com/auth/documents \
  https://www.googleapis.com/auth/drive.readonly
```

Появится token cache:
- `.secrets/google-token.json`

Проверить текущие scope/expiry:

```bash
python3 gdocs_cli.py token-info
```

## 2) Сделай Google Doc “Template CV”

Важно: редактирование через Docs API работает только для **Google Docs** (`mimeType = application/vnd.google-apps.document`), не для `.docx`.

Рекомендованный подход:

1) Создай новый Google Doc “Template CV”.
2) Скопируй в него структуру резюме (заголовки/списки/разделы).
3) Заменяй переменные места на плейсхолдеры из `templates/CV_PLACEHOLDERS.md`.

### Как сохранять форматирование

- Для bullet-списков: заранее создай нужное число пунктов и ставь по одному плейсхолдеру на строку:
  - `• {{SKILLS_GO_BULLET_1}}`
  - `• {{SKILLS_GO_BULLET_2}}`
  - …
  Так останутся bullet/отступы/стили.
- Для заголовков: ставь плейсхолдер прямо в заголовок, если нужно менять заголовок целиком (например `{{SKILLS_GO_TITLE}}`).
- Если что-то “опционально”: просто заменяй плейсхолдер на пустую строку `""` (но пустой bullet может остаться — лучше иметь отдельный “cleanup” шаг или заранее держать ровно нужное число строк).

## 3) Подготовь replacements JSON (данные)

Скопируй пример и заполни своими значениями:

- `templates/cv.replacements.example.json`

Формат поддерживается такой:

```json
{
  "replacements": {
    "{{FULL_NAME}}": "Stanislav Sobolev",
    "{{SUMMARY_PARAGRAPH}}": "..."
  }
}
```

Можно также передавать “плоский” объект без `replacements`.

## 4) Применить replacements к документу (batchUpdate)

Сначала “dry-run” (посмотреть запросы, ничего не меняя):

```bash
python3 gdocs_cli.py apply \
  --doc "Stan Sobolev_HRD_2025" \
  --data templates/cv.replacements.example.json \
  --dry-run
```

Применить:

```bash
python3 gdocs_cli.py apply \
  --doc "Stan Sobolev_HRD_2025" \
  --data templates/cv.replacements.example.json
```

## 5) Проверка результата

Текст:

```bash
python3 gdocs_cli.py print --doc "Stan Sobolev_HRD_2025"
```

Markdown-представление:

```bash
python3 gdocs_cli.py print --format md --doc "Stan Sobolev_HRD_2025"
```

Структурированный JSON (удобно для анализа абзацев/секций/стилей):

```bash
python3 gdocs_cli.py print --format json --doc "Stan Sobolev_HRD_2025"
```

## 6) TUI (быстро посмотреть/заменить руками)

```bash
python3 gdocs_tui.py
```

- `Enter` открыть документ
- `m` / `F2` переключить формат (по умолчанию `para`)
- `e` replace (только для Google Docs)
- `A` переавторизация (если не хватает scope)
- `d` показать последнюю ошибку полностью

## 7) Типовые проблемы

### 403 (Drive metadata / export / download)

Обычно одно из:
- не хватает `drive.readonly` в токене
- документ не расшарен на тот аккаунт, которым ты авторизовался

Решение:
- `python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive.readonly`
- или проверь доступ к документу в браузере под тем же аккаунтом

### Docs API “not supported for this document”

Значит это `.docx`/не Google Doc. Нужно конвертировать в Google Doc и работать уже с ним.

