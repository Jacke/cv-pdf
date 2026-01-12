# Google Docs TUI (Python)

TUI: `gdocs_tui.py` — просмотр документов из `GOOGLE_DOCS_LINKS.md` и тестовое редактирование через Docs API (replaceAllText).

## Требования

- Python 3 (без внешних зависимостей; используется `curses`)
- OAuth client JSON в `.secrets/google-oauth-client.json`

## Запуск

```bash
python3 gdocs_tui.py
```

Если нужно — можно переопределить пути:

- `GDOCS_OAUTH_CLIENT` (default: `.secrets/google-oauth-client.json`)
- `GDOCS_TOKEN` (default: `.secrets/google-token.json`)
- `GDOCS_LINKS_FILE` (default: `GOOGLE_DOCS_LINKS.md`)

## Клавиши

- `↑/↓` — выбрать документ / скролл
- `Enter` — открыть документ
- `m` — переключить формат просмотра `plain` / `md` / `para` (абзацы с отступами)
- `F2` — переключить формат просмотра (удобно, если включена RU раскладка)
- `e` — заменить текст (работает только для Google Docs, не для `.docx`)
- `A` — пройти OAuth (в режиме просмотра запрашивает write scope для редактирования)
- `r` — перечитать `GOOGLE_DOCS_LINKS.md`
- `?` — помощь
- `q` — назад / выход

## Примечания

- Просмотр делается через Drive API (export/download), поэтому работает и для Google Docs, и для `.docx`.
- Редактирование делается через Docs API и требует scope `https://www.googleapis.com/auth/documents`.
  - Для просмотра также нужен `https://www.googleapis.com/auth/drive.readonly` (иначе будет 403 на Drive API).
- Режим `para` строит отображение по абзацам/спискам и добавляет отступы (best-effort).
  - Дополнительно сохраняет больше пустых строк вокруг заголовков, чтобы уровни `#` / `##` / `###` визуально разделялись.

## Troubleshooting

- Если видишь “пустой экран”: попробуй нажать `?` (help) или увеличь размер терминала.
- Запускай в обычном терминале (Terminal/iTerm). В некоторых IDE-консолях `curses` работает нестабильно.
- Если ловишь `403`:
  - Нажми `d` чтобы увидеть полный текст ошибки.
  - Обычно причина — недостаточно scope в токене. В TUI нажми `A` (переавторизация), либо в CLI: `python3 gdocs_cli.py auth --scopes https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive.readonly`
