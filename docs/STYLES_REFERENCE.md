# CV Styles Reference - Quick Lookup

## Skills Block

### Элементы и их стили (HRD Standard)

```
Skills                                    <- H2, 17pt bold, spaceBelow 4pt
  Go (Back-End)                          <- H3, 13pt bold black, spaceAbove 14pt
    • Microservices architecture...      <- Bullet, indent 18/36pt, spaceBelow 12pt
    • PostgreSQL and Redis...            <- Bullet, indent 18/36pt, spaceBelow 12pt
    • Concurrent programming...          <- Bullet, indent 18/36pt, spaceBelow 12pt
```

### API Requests

```python
# H2 заголовок
{
  "updateParagraphStyle": {
    "paragraphStyle": {
      "namedStyleType": "HEADING_2",
      "spaceBelow": {"magnitude": 4.0, "unit": "PT"}
    },
    "range": {"startIndex": 389, "endIndex": 396},
    "fields": "namedStyleType,spaceBelow"
  }
}
{
  "updateTextStyle": {
    "textStyle": {
      "bold": True,
      "fontSize": {"magnitude": 17.0, "unit": "PT"}
    },
    "range": {"startIndex": 389, "endIndex": 395},
    "fields": "bold,fontSize"
  }
}

# H3 категория
{
  "updateParagraphStyle": {
    "paragraphStyle": {
      "namedStyleType": "HEADING_3",
      "spaceAbove": {"magnitude": 14.0, "unit": "PT"}
    },
    "range": {"startIndex": 396, "endIndex": 410},
    "fields": "namedStyleType,spaceAbove"
  }
}
{
  "updateTextStyle": {
    "textStyle": {
      "bold": True,
      "fontSize": {"magnitude": 13.0, "unit": "PT"},
      "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
    },
    "range": {"startIndex": 396, "endIndex": 409},
    "fields": "bold,fontSize,foregroundColor"
  }
}

# Bullet item
{
  "updateParagraphStyle": {
    "paragraphStyle": {
      "indentFirstLine": {"magnitude": 18.0, "unit": "PT"},
      "indentStart": {"magnitude": 36.0, "unit": "PT"},
      "namedStyleType": "NORMAL_TEXT",
      "spaceBelow": {"magnitude": 12.0, "unit": "PT"}
    },
    "range": {"startIndex": 410, "endIndex": 461},
    "fields": "indentFirstLine,indentStart,namedStyleType,spaceBelow"
  }
}
```

---

## Experience Block

### Элементы и их стили (HRD Standard)

```
Experience                                              <- H2, 17pt bold, spaceBelow 4pt

  TechCorp                                             <- H3, 13pt bold black, spaceAbove 14pt, link
  Senior Backend Engineer · Jan 2021 - Present        <- 10pt bold black

  Leading technology company specializing...           <- 10pt italic

  https://techcorp.example.com                         <- 10pt normal

  Lead Backend Engineer                                <- normal

    • Architected and implemented order processing     <- Bullet, indent 18/36pt
    • Designed and deployed distributed caching        <- Bullet, indent 18/36pt
    • Led migration from monolith to microservices     <- Bullet, indent 18/36pt

  Tech: Go, PostgreSQL, Redis, Kafka, Kubernetes       <- italic
```

### API Requests

```python
# H3 название компании (с ссылкой!)
{
  "updateParagraphStyle": {
    "paragraphStyle": {
      "namedStyleType": "HEADING_3",
      "spaceAbove": {"magnitude": 14.0, "unit": "PT"}
    },
    "range": {"startIndex": 1811, "endIndex": 1820},
    "fields": "namedStyleType,spaceAbove"
  }
}
{
  "updateTextStyle": {
    "textStyle": {
      "bold": True,
      "fontSize": {"magnitude": 13.0, "unit": "PT"},
      "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
      # ^^ ВАЖНО: переопределяет синий цвет ссылок!
    },
    "range": {"startIndex": 1811, "endIndex": 1819},
    "fields": "bold,fontSize,foregroundColor"
  }
}

# Роль и даты
{
  "updateTextStyle": {
    "textStyle": {
      "bold": True,
      "fontSize": {"magnitude": 10.0, "unit": "PT"},
      "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
    },
    "range": {"startIndex": 1820, "endIndex": 1864},
    "fields": "bold,fontSize,foregroundColor"
  }
}

# Описание компании
{
  "updateTextStyle": {
    "textStyle": {
      "fontSize": {"magnitude": 10.0, "unit": "PT"},
      "italic": True
    },
    "range": {"startIndex": 1867, "endIndex": 1943},
    "fields": "fontSize,italic"
  }
}

# Website link
{
  "updateTextStyle": {
    "textStyle": {
      "fontSize": {"magnitude": 10.0, "unit": "PT"}
    },
    "range": {"startIndex": 1946, "endIndex": 1975},
    "fields": "fontSize"
  }
}

# Achievement bullet
{
  "updateParagraphStyle": {
    "paragraphStyle": {
      "indentFirstLine": {"magnitude": 18.0, "unit": "PT"},
      "indentStart": {"magnitude": 36.0, "unit": "PT"},
      "namedStyleType": "NORMAL_TEXT"
    },
    "range": {"startIndex": 2012, "endIndex": 2163},
    "fields": "indentFirstLine,indentStart,namedStyleType"
  }
}

# Tech stack
{
  "updateTextStyle": {
    "textStyle": {
      "italic": True
      # Colorful theme добавляет:
      # "fontSize": {"magnitude": 9.0, "unit": "PT"},
      # "foregroundColor": {"color": {"rgbColor": {"red": 0.533, "green": 0.533, "blue": 0.533}}}
    },
    "range": {"startIndex": 2605, "endIndex": 2683},
    "fields": "italic"  # или "fontSize,foregroundColor,italic" для Colorful
  }
}
```

---

## Color Palette

### HRD Standard (только черный)

```python
COLORS = {
    "text_black": (0.0, 0.0, 0.0),  # #000000
}
```

### Colorful Theme

```python
COLORS = {
    "accent_blue": (0.290, 0.565, 0.886),    # #4A90E2 - синяя рамка для Skills
    "text_dark": (0.102, 0.102, 0.102),      # #1A1A1A - основной текст
    "text_gray": (0.400, 0.400, 0.400),      # #666666 - даты
    "text_light_gray": (0.533, 0.533, 0.533),# #888888 - tech stack
    "border_gray": (0.878, 0.878, 0.878),    # #E0E0E0 - разделители
    "bg_gray_1": (0.973, 0.976, 0.980),      # #F8F9FA - Skills фон (УБРАН)
    "bg_gray_2": (0.961, 0.961, 0.961),      # #F5F5F5 - Education фон
}
```

---

## Dimension Helper

```python
def dimension(magnitude: float, unit: str = "PT") -> dict:
    return {"magnitude": magnitude, "unit": unit}

# Примеры:
dimension(18.0)      # -> {"magnitude": 18.0, "unit": "PT"}
dimension(1.0, "IN") # -> {"magnitude": 1.0, "unit": "IN"}
```

---

## RGB Color Helper

```python
def rgb_color(r: float, g: float, b: float) -> dict:
    """
    Args:
        r, g, b: 0.0 - 1.0 (не 0-255!)
    """
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}

# Примеры:
rgb_color(0.0, 0.0, 0.0)                # Черный
rgb_color(0.290, 0.565, 0.886)          # #4A90E2 синий
rgb_color(0.533, 0.533, 0.533)          # #888888 серый
```

---

## Common Sizes

| Элемент | Размер | Применение |
|---------|--------|-----------|
| H2 заголовки | 17pt | Summary, Skills, Experience |
| H3 категории/компании | 13pt | Go (Back-End), TechCorp |
| Роль/даты | 10pt bold | Senior Backend Engineer · ... |
| Описание компании | 10pt italic | Leading technology company... |
| Website | 10pt | https://... |
| Tech stack | italic (или 9pt gray) | Tech: Go, PostgreSQL... |
| Bullets indent | 18pt (first), 36pt (start) | • Achievement item |
| Spacing below bullet | 12pt | После каждого bullet |
| Spacing above H3 | 14pt | Перед категорией/компанией |
| Spacing below H2 | 4pt | После заголовка секции |

---

## Detection Patterns

### Является ли параграф bullet?

```python
def is_bullet(para: dict) -> bool:
    return para.get("paragraph", {}).get("bullet") is not None
```

### Какой уровень заголовка?

```python
def get_heading_level(para: dict) -> int | None:
    style = para.get("paragraph", {}).get("paragraphStyle", {})
    named = style.get("namedStyleType", "")

    if named == "HEADING_1": return 1
    if named == "HEADING_2": return 2
    if named == "HEADING_3": return 3
    # ... до HEADING_6
    return None
```

### Получить текст параграфа

```python
def get_paragraph_text(para: dict) -> str:
    elements = para.get("paragraph", {}).get("elements", [])
    text_parts = []
    for elem in elements:
        text_run = elem.get("textRun")
        if text_run:
            text_parts.append(text_run.get("content", ""))
    return "".join(text_parts)
```

### Найти секцию по заголовку

```python
def find_section_by_heading(content: list, heading_text: str, level: int = 2):
    """
    Найти range секции (startIndex, endIndex).

    Секция начинается с заголовка уровня level с текстом heading_text
    и заканчивается перед следующим заголовком того же уровня.
    """
    section_start = None

    for idx, item in enumerate(content):
        if not item.get("paragraph"):
            continue

        h_level = get_heading_level(item)
        text = get_paragraph_text(item).strip()

        # Нашли начало
        if h_level == level and heading_text.lower() in text.lower():
            section_start = item.get("startIndex")
            continue

        # Нашли конец
        if section_start is not None and h_level == level:
            section_end = item.get("startIndex")
            return (section_start, section_end)

    # До конца документа
    if section_start is not None:
        section_end = content[-1].get("endIndex")
        return (section_start, section_end)

    return None
```

---

## Fields Parameter

При использовании `updateParagraphStyle` или `updateTextStyle`, поле `fields` определяет **какие именно свойства обновить**.

**Синтаксис:** `"field1,field2.subfield,field3"`

**Примеры:**

```python
# Обновить только bold и fontSize
"fields": "bold,fontSize"

# Обновить фон и левую рамку
"fields": "shading.backgroundColor,borderLeft"

# Обновить все свойства параграфа
"fields": "indentFirstLine,indentStart,namedStyleType,spaceBelow"

# Обновить цвет текста
"fields": "foregroundColor"
```

**ВАЖНО:** Если не указать поле в `fields`, оно НЕ будет обновлено, даже если присутствует в объекте!

---

## Typical Workflow

```python
# 1. Получить документ
doc = get_doc(document_id="...", access_token=token)

# 2. Извлечь content
content = doc.get("body", {}).get("content", [])

# 3. Найти секцию
skills_range = find_section_by_heading(content, "Skills", level=2)
# -> (389, 1800)

# 4. Найти элементы в секции
requests = []
for item in content:
    start = item.get("startIndex")
    end = item.get("endIndex")

    if start >= 389 and end <= 1800:
        if is_bullet(item):
            # Создать request для bullet
            requests.append({
                "updateParagraphStyle": {
                    "paragraphStyle": {
                        "indentFirstLine": dimension(18.0),
                        "indentStart": dimension(36.0),
                        "spaceBelow": dimension(12.0),
                    },
                    "range": {"startIndex": start, "endIndex": end},
                    "fields": "indentFirstLine,indentStart,spaceBelow"
                }
            })

# 5. Применить все requests
docs_batch_update(
    document_id="...",
    access_token=token,
    requests=requests
)
```

---

**См. также:**
- [Full Documentation](CV_THEME_SYSTEM.md)
- [Document Structure](DOCUMENT_STRUCTURE_EXTRACTED.md)
- [Quick Start](THEME_QUICK_START.md)
