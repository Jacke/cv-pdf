# Google Docs CLI (Python)

CLI: `gdocs_cli.py` — проходит OAuth авторизацию и печатает plain-text содержимое Google Docs из `GOOGLE_DOCS_LINKS.md`.

TUI: `gdocs_tui.py` — просмотр/скролл и replace-редактирование в терминале. См. `docs/GOOGLE_DOCS_TUI.md`.

Шаблоны: `docs/GOOGLE_DOCS_TEMPLATE.md`.
Markdown pipeline: `docs/GOOGLE_DOCS_MARKDOWN_PIPELINE.md`.

## 0) Безопасность

- OAuth `client_secret` не коммить в git.
- Если секрет уже “засветился”, сделай rotate в Google Cloud Console.
- Положи client JSON локально в `.secrets/google-oauth-client.json` (папка в `.gitignore`).

## 1) Подготовка

1. Включи API в проекте Google Cloud:
   - Google Docs API
2. Скачай OAuth client JSON (Desktop app) и положи в:
   - `.secrets/google-oauth-client.json`

## 2) Авторизация (получить token)

```bash
python3 gdocs_cli.py auth
```

Файл токена будет записан в `.secrets/google-token.json`.

По умолчанию `auth` запрашивает два read-only scope:
- `https://www.googleapis.com/auth/documents.readonly`
- `https://www.googleapis.com/auth/drive.readonly`

Это нужно, чтобы `print` мог делать fallback на Drive export, если Docs API не подходит.

Если тебе позже понадобится редактирование, можно авторизоваться с read/write scope:

```bash
python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents
```

Проверить, какие scope сейчас в токене:

```bash
python3 gdocs_cli.py token-info
```

## Troubleshooting: `Error 403: access_denied`

Самая частая причина: OAuth consent screen не настроен, приложение в режиме Testing, но твой аккаунт не добавлен в Test users, или выбран тип приложения **Internal**.

Проверь в Google Cloud Console → APIs & Services → OAuth consent screen:

- `User type`: **External** (если ты логинишься обычным Gmail/не Workspace доменом)
- `Publishing status`: **Testing** (или In production)
- `Test users`: добавь свой email (тот, которым открываешь OAuth в браузере)
- Убедись, что включены API: Google Docs API (и Drive API, если используешь export/permissions)

После этого повтори:

```bash
python3 gdocs_cli.py auth
```

## Troubleshooting: `Ineligible accounts not added` (Test users)

Сообщение вида “Ineligible accounts not added … not eligible for designation as a test user” почти всегда означает одно из:

- Проект находится в **Google Workspace Organization**, и приложение фактически **Internal** → нельзя добавить `@gmail.com` как test user (можно только аккаунты внутри домена организации).
- Указанный email реально не является Google Account (редко для `@gmail.com`, но бывает если это не тот email, которым ты логинишься).

Что делать:

- Проверь, есть ли у проекта организация: Google Cloud Console → выпадашка проекта → `Organization`.
- Если нужна авторизация **под Gmail**:
  - создай **новый проект** под `No organization` (личный), затем сделай OAuth consent screen **External** и добавь `iamjacke@gmail.com` в Test users;
  - либо попроси админа Workspace разрешить External/убрать ограничения (если проект обязан быть в организации).

## 3) Печать документов

Показать список:

```bash
python3 gdocs_cli.py list
```

Распечатать все документы:

```bash
python3 gdocs_cli.py print
```

Печать с “форматированием” (Markdown-представление: заголовки, списки, bold/italic/strike, ссылки; underline → `<u>`):

```bash
python3 gdocs_cli.py print --format md
```

Чистый машинно-читаемый вывод (структурированный JSON с `sections`/`blocks` и стилями в `runs`):

```bash
python3 gdocs_cli.py print --format json --doc "Stan Sobolev_HRD_2025"
```

JSON дополнительно включает `outline` (дерево оглавления), которое строится по заголовкам (`headingLevel`/`headingId`), и `tabs`, если документ реально табовый (в Docs API есть поле `tabs`).

В `runs[].style` (если доступно) теперь также есть:
- `fontFamily`
- `fontSize` (`magnitude` + `unit`)
- `foregroundColor` / `backgroundColor` (hex `#RRGGBB`)

По умолчанию `print` работает в режиме `--method auto`: пробует Docs API, и если он падает, делает fallback на Drive.

## 4) Тестовое редактирование (replaceAllText)

Важно: редактирование через Docs API работает только для **Google Docs** (не для `.docx`). Если документ — `.docx`, сначала сконвертируй в Google Doc.

1) Авторизуйся с write-scope:

```bash
python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive.readonly
```

Если после этого всё равно `insufficient authentication scopes`, значит старый grant не обновился. Тогда:

```bash
rm -f .secrets/google-token.json
```

И в браузере: https://myaccount.google.com/permissions → удали доступ для приложения, затем снова запусти `auth`.

2) Замени текст:

```bash
python3 gdocs_cli.py replace \
  --doc "Stan Sobolev_HRD_2025" \
  --from "Successfully finished the startup accelerator program" \
  --to "Successfully completed the startup accelerator program"
```

## 5) Применить много замен из JSON

См. `docs/GOOGLE_DOCS_TEMPLATE.md`.


Распечатать один документ по имени (как в `GOOGLE_DOCS_LINKS.md`):

```bash
python3 gdocs_cli.py print --doc Stan\ Sobolev_HRD_2025
```

Форсировать способ получения текста:

```bash
python3 gdocs_cli.py print --method docs
python3 gdocs_cli.py print --method drive
```

`--method drive` сначала смотрит `mimeType` файла через Drive API:
- если это Google Docs (`application/vnd.google-apps.document`) — делает export в `text/plain` (для `--format plain`) или export в `docx` (для `--format md`)
- если это DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) — скачивает `alt=media` и извлекает текст/Markdown

## Переменные окружения (опционально)

- `GDOCS_OAUTH_CLIENT` — путь к OAuth client JSON
- `GDOCS_TOKEN` — путь к token cache
