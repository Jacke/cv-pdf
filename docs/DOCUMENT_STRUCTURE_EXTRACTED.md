# Document Structure - Extracted Styles

## Источник

**Документ:** Test HRD CV Full (1BlvYvktXHmDutL1DbdW64r6roGLVjwdd8gh7UjRbmNk)
**Дата анализа:** 2026-01-02
**Метод:** Google Docs API document.get()

## Skills Section - Структура

### H2 Заголовок секции

```
[H2 - SKILLS SECTION]
  Range: 389 - 396
  namedStyleType: HEADING_2
  spaceBelow: None (применяется после стилизации)

  TEXT STYLE:
    - bold: True (из namedStyleType)
    - fontSize: 17pt (из namedStyleType)
```

### H3 Категория навыка

```
[H3 - Skill Category] "Go (Back-End)"
  Range: 396 - 410
  namedStyleType: HEADING_3
  spaceAbove: None (применяется 14pt после стилизации)

  TEXT STYLE (после стилизации HRD Standard):
    - bold: True
    - fontSize: 13pt
    - foregroundColor: #000000 (черный)
```

### Bullet Items - Навыки

```
[BULLET] "Microservices architecture with gRPC and REST APIs"
  Range: 410 - 461

  PARAGRAPH STYLE:
    - indentFirstLine: 18pt
    - indentStart: 36pt
    - spaceBelow: 12pt
    - namedStyleType: NORMAL_TEXT

  Является bullet: да (paragraph.bullet != null)

  Визуально:
    ├─ отступ первой строки: 18pt
    ├─ отступ всего параграфа: 36pt
    └─ расстояние после: 12pt
```

**Все bullets в Skills имеют одинаковый стиль:**
- indentFirstLine: 18pt
- indentStart: 36pt
- spaceBelow: 12pt

**Пример из документа:**
```
Skills
  Go (Back-End)
    • Microservices architecture with gRPC and REST APIs
    • PostgreSQL and Redis integration, connection pooling
    • Concurrent programming with goroutines and channels
    • Testing with testify, gomock, and table-driven tests
    • Error handling and context propagation patterns

  Databases & Caching
    • PostgreSQL: optimization, replication, sharding
    • Redis: caching strategies, pub/sub, streams
    • ...
```

---

## Experience Section - Структура

### H2 Заголовок секции

```
[H2 - EXPERIENCE SECTION]
  Range: 1800 - 1811
  namedStyleType: HEADING_2

  TEXT STYLE:
    - bold: True
    - fontSize: 17pt
```

### H3 Название компании (с ссылкой)

```
[H3 - Company Name] "TechCorp"
  Range: 1811 - 1820
  namedStyleType: HEADING_3
  spaceAbove: 14pt

  TEXT STYLE:
    - bold: True
    - fontSize: 13pt
    - foregroundColor: будет применен черный (#000000) чтобы переопределить синий цвет ссылок

  LINK:
    - url: https://techcorp.example.com

  ВАЖНО: Google Docs автоматически красит ссылки в синий.
  Наша тема переопределяет это через foregroundColor: black
```

### Роль и даты

```
[ROLE/DURATION] "Senior Backend Engineer · Jan 2021 - Present"
  Range: 1820 - 1865

  TEXT STYLE:
    - bold: True
    - fontSize: 10pt
    - foregroundColor: #000000 (черный)

  Формат: {role} · {dates}
  Разделитель: · (bullet точка)
```

### Описание компании

```
[COMPANY DESC] "Leading technology company specializing in e-commerce solutions..."
  Range: 1867 - 1944

  TEXT STYLE:
    - italic: True
    - fontSize: 10pt

  Обычно 1-2 предложения о компании
```

### Website ссылка

```
[WEBSITE] "https://techcorp.example.com"
  Range: 1946 - 1976

  TEXT STYLE:
    - fontSize: 10pt

  Обычный текст, может быть ссылкой
```

### Job Title

```
[JOB TITLE] "Lead Backend Engineer"
  Range: 1978 - 2001

  TEXT STYLE:
    - Normal text (без специальных стилей)
```

### Achievement Bullets

```
[BULLET - Achievement] "Architected and implemented order processing microservice..."
  Range: 2012 - 2163

  PARAGRAPH STYLE:
    - indentFirstLine: 18pt
    - indentStart: 36pt
    - spaceBelow: 12pt (может отсутствовать)
    - namedStyleType: NORMAL_TEXT

  Является bullet: да (paragraph.bullet != null)

  Обычно:
    - Начинается с глагола в прошедшем времени (Built, Implemented, Designed)
    - Содержит метрики (40% improvement, 100K+ transactions)
    - 1-2 строки длиной
```

**Все achievement bullets имеют одинаковый стиль:**
- indentFirstLine: 18pt
- indentStart: 36pt

### Tech Stack

```
[TECH STACK] "Tech: Go, PostgreSQL, Redis, Kafka, Kubernetes, Docker..."
  Range: 2605 - 2684

  TEXT STYLE:
    - italic: True (HRD Standard)
    ИЛИ (для Colorful theme):
    - italic: True
    - fontSize: 9pt
    - foregroundColor: #888888 (серый)

  Формат: "Tech: {технологии через запятую}"
  Начинается с "Tech:" или "Technologies:"
```

**Пример блока компании:**
```
Experience

  TechCorp                                          <- H3, 13pt bold, ссылка
  Senior Backend Engineer · Jan 2021 - Present     <- 10pt bold

  Leading technology company specializing...        <- 10pt italic

  https://techcorp.example.com                      <- 10pt

  Lead Backend Engineer                             <- normal

    • Architected and implemented order processing  <- bullet, indent 18/36pt
    • Designed and deployed distributed caching     <- bullet
    • Led migration from monolith to microservices  <- bullet
    • Mentored team of 5 junior developers          <- bullet
    • Implemented comprehensive monitoring          <- bullet

  Tech: Go, PostgreSQL, Redis, Kafka, Kubernetes    <- italic (или 9pt gray)
```

---

## Важные детали

### 1. Ranges (индексы)

Каждый параграф имеет:
- `startIndex` - начало параграфа (включительно)
- `endIndex` - конец параграфа (не включительно)

**Пример:**
```
Range: 410 - 461
Означает: символы с позиции 410 до 460 (включительно)
```

### 2. Bullet Detection

Параграф является bullet если:
```python
para.get("paragraph", {}).get("bullet") is not None
```

**Структура bullet объекта:**
```json
{
  "bullet": {
    "listId": "kix.list1",
    "nestingLevel": 0
  }
}
```

### 3. Named Style Types

Используются стандартные типы Google Docs:
- `HEADING_1` - H1 (название документа)
- `HEADING_2` - H2 (секции: Summary, Skills, Experience)
- `HEADING_3` - H3 (категории навыков, названия компаний)
- `NORMAL_TEXT` - обычный текст и bullets

### 4. Dimensions (размеры)

Все размеры в Google Docs API хранятся как объекты:
```json
{
  "magnitude": 18.0,
  "unit": "PT"
}
```

Доступные единицы: `PT` (points), `IN` (inches), `MM` (millimeters)

### 5. Links (ссылки)

Ссылки хранятся в textStyle:
```json
{
  "textStyle": {
    "link": {
      "url": "https://example.com"
    }
  }
}
```

**Проблема:** Google Docs автоматически красит ссылки в синий цвет.
**Решение:** Переопределяем через `foregroundColor` в темах.

---

## Применение стилей - Mapping

### Skills Section

| Элемент | Range Example | Функция применения |
|---------|---------------|-------------------|
| H2 "Skills" | 389 - 396 | `apply_section_heading_style()` |
| H3 "Go (Back-End)" | 396 - 410 | `apply_skill_category_style()` |
| Bullet "Microservices..." | 410 - 461 | `apply_achievement_bullet_style()` |

### Experience Section

| Элемент | Range Example | Функция применения |
|---------|---------------|-------------------|
| H2 "Experience" | 1800 - 1811 | `apply_section_heading_style()` |
| H3 "TechCorp" | 1811 - 1820 | `apply_company_name_style()` |
| "Senior Backend..." | 1820 - 1865 | `apply_role_duration_style()` |
| "Leading technology..." | 1867 - 1944 | `apply_company_description_style()` |
| "https://..." | 1946 - 1976 | `apply_website_link_style()` |
| Bullet "Architected..." | 2012 - 2163 | `apply_achievement_bullet_style()` |
| "Tech: Go, PostgreSQL..." | 2605 - 2684 | `apply_tech_stack_style()` |

---

## Стили после применения HRD Standard темы

### Skills Section

```python
# H2 "Skills"
{
  "namedStyleType": "HEADING_2",
  "spaceBelow": {"magnitude": 4.0, "unit": "PT"}
}
TEXT: {
  "bold": True,
  "fontSize": {"magnitude": 17.0, "unit": "PT"}
}

# H3 "Go (Back-End)"
{
  "namedStyleType": "HEADING_3",
  "spaceAbove": {"magnitude": 14.0, "unit": "PT"}
}
TEXT: {
  "bold": True,
  "fontSize": {"magnitude": 13.0, "unit": "PT"},
  "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
}

# Bullet items
{
  "indentFirstLine": {"magnitude": 18.0, "unit": "PT"},
  "indentStart": {"magnitude": 36.0, "unit": "PT"},
  "namedStyleType": "NORMAL_TEXT",
  "spaceBelow": {"magnitude": 12.0, "unit": "PT"}
}
```

### Experience Section

```python
# H3 "TechCorp" (с ссылкой)
{
  "namedStyleType": "HEADING_3",
  "spaceAbove": {"magnitude": 14.0, "unit": "PT"}
}
TEXT: {
  "bold": True,
  "fontSize": {"magnitude": 13.0, "unit": "PT"},
  "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
}

# "Senior Backend Engineer · Jan 2021 - Present"
TEXT: {
  "bold": True,
  "fontSize": {"magnitude": 10.0, "unit": "PT"},
  "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
}

# "Leading technology company..."
TEXT: {
  "fontSize": {"magnitude": 10.0, "unit": "PT"},
  "italic": True
}

# "Tech: Go, PostgreSQL..."
TEXT: {
  "italic": True
}

# Achievement bullets
{
  "indentFirstLine": {"magnitude": 18.0, "unit": "PT"},
  "indentStart": {"magnitude": 36.0, "unit": "PT"},
  "namedStyleType": "NORMAL_TEXT"
}
```

---

## Выводы

### Общие паттерны

1. **Bullets всегда имеют:**
   - `indentFirstLine: 18pt`
   - `indentStart: 36pt`
   - Присутствует `paragraph.bullet` объект

2. **H3 заголовки всегда имеют:**
   - `namedStyleType: HEADING_3`
   - `spaceAbove: 14pt`
   - `bold: True, fontSize: 13pt`

3. **Ссылки требуют:**
   - Переопределение `foregroundColor` на черный
   - Иначе Google Docs красит их в синий

4. **Все размеры:**
   - Хранятся как объекты `{magnitude, unit}`
   - Обычно используется `PT` (points)

### Использование в коде

```python
# Найти Skills секцию
skills_range = find_section_by_heading(content, "Skills", level=2)
# -> (389, 1800)

# Найти все bullets в Skills
for item in content:
    if item.get("paragraph", {}).get("bullet") is not None:
        start = item["startIndex"]
        end = item["endIndex"]

        if start >= 389 and end <= 1800:
            # Это skill bullet
            apply_achievement_bullet_style(start, end)

# Найти Tech: строки
for item in content:
    text = get_paragraph_text(item)
    if text.startswith("Tech:"):
        apply_tech_stack_style(item["startIndex"], item["endIndex"])
```

---

**Документ создан:** 2026-01-02
**Источник данных:** Google Docs API document.get()
**Применимость:** Для всех CV документов с такой же структурой
