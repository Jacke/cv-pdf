# Google Docs API: доступ и локальное редактирование

Важно: OAuth `client_secret` — это секрет. Не коммить в git и не хранить в открытом виде. Если ты уже где-то “засветил” секрет (например, в чате/публичном месте) — в Google Cloud Console лучше **перевыпустить (rotate)** OAuth Client Secret.

## Что нужно включить в Google Cloud

1. Google Cloud Console → твой проект.
2. APIs & Services → Enable APIs:
   - **Google Docs API**
   - **Google Drive API** (нужен для export/поиска/прав доступа; для чистых правок Docs API может хватить, но на практике Drive почти всегда пригодится).
3. OAuth consent screen:
   - заполни минимум (app name, email),
   - добавь себя в Test users (если приложение в testing).
4. Credentials → OAuth client ID:
   - тип **Desktop app**,
   - redirect URI для loopback обычно `http://localhost` или `http://localhost:8080/` (если будешь поднимать локальный callback).

## Какой тип авторизации выбрать

### Вариант A: OAuth “под твоим аккаунтом” (рекомендую для личных доков)

Подходит, если документы принадлежат/доступны твоему Google-аккаунту.

Скоупы (минимально полезные):
- Редактирование Docs: `https://www.googleapis.com/auth/documents`
- Экспорт/работа с Drive: `https://www.googleapis.com/auth/drive.readonly` (если только скачивать) или `https://www.googleapis.com/auth/drive` (если управлять правами/шарингом и т.п.)

Что происходит:
1. Ты один раз проходишь OAuth flow в браузере.
2. Получаешь `refresh_token`.
3. Дальше локальная утилита обновляет `access_token` автоматически.

### Вариант B: Service Account

Подходит для полностью автоматического режима без интерактива.

Требования:
1. Создаёшь service account, скачиваешь JSON-ключ.
2. Шаришь каждый Google Doc на email service account (как на пользователя) с правами Editor.
3. Работаешь от service account токеном JWT.

## Что значит “редактировать локально”

Google Doc — это не файл `.docx`, который можно “сохранить обратно” как есть.

Типовые стратегии:

1) **API-first (самый корректный путь)**  
Локальная утилита получает документ через Docs API и применяет изменения через `documents.batchUpdate`.

2) **Export → редактировать локально → синхронизировать через API (упрощённо)**  
- скачиваешь документ в `txt`/`docx` через Drive API (`files.export`),
- редактируешь локально,
- затем либо:
  - применяешь точечные замены через `replaceAllText`,
  - либо перезаписываешь текст целиком (обычно теряется часть форматирования),
  - либо пишешь diff-алгоритм и маппишь изменения в batchUpdate-операции.

3) **Google Drive for Desktop**  
Даёт “локальные ярлыки” `.gdoc`, но редактирование всё равно идёт через Google Docs (браузер), это не API-редактирование.

## Как понять documentId из ссылки

В ссылке вида:
`https://docs.google.com/document/d/<DOCUMENT_ID>/edit`

`DOCUMENT_ID` — это то, что нужно передавать в Docs API.

## Минимальный набор вызовов API

- Читать документ: `docs.documents.get(documentId)`
- Вносить изменения: `docs.documents.batchUpdate(documentId, requests[])`
  - `replaceAllText` — безопасные замены по шаблону
  - `insertText` / `deleteContentRange` — вставка/удаление

Drive (часто нужно):
- Экспорт в `docx/pdf/txt`: `drive.files.export(fileId, mimeType)`
- Права доступа (если надо): `drive.permissions.create`

## Практический совет по безопасности

- Храни OAuth client JSON в файле вроде `google-oauth-client.json` (он в `.gitignore`).
- Храни token cache отдельно (например, `google-token.json`, тоже в `.gitignore`).
- Если нужно расшарить проект/репо — передавай только пример конфига без секрета.

## Troubleshooting: `Error 403: access_denied`

Если при OAuth видишь `Error 403: access_denied`, чаще всего это одно из:

- OAuth consent screen не настроен или не сохранён
- приложение в режиме **Testing**, но твой аккаунт не добавлен в **Test users**
- выбран `User type = Internal`, а ты логинишься аккаунтом вне Google Workspace домена
- Google Workspace админ запретил сторонние OAuth-приложения/согласование скоупов

Что проверить:
- Google Cloud Console → APIs & Services → OAuth consent screen:
  - `User type`: **External** (для обычных Gmail)
  - `Test users`: добавь свой email
  - `Publishing status`: Testing/Production
- Включены API: Docs (и Drive при необходимости)
