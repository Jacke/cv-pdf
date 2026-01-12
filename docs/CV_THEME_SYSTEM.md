# CV Theme System Documentation

## Обзор

Система тем для автоматической стилизации CV документов через Google Docs API. Позволяет переиспользовать стили и применять их к разным документам консистентно.

## Архитектура

```
scripts/
  themes/
    hrd_standard.py      # Стандартная HRD тема (из Stan Sobolev_HRD_2025)
    minimalist.py        # Минималистичная тема
    colorful.py          # Цветная тема с акцентами
  apply_cv_styles_themed.py  # Скрипт применения тем
  extract_styles.py           # Извлечение стилей из документов
```

## Структура темы

Каждая тема — это Python модуль со следующими компонентами:

### 1. Стили элементов (Element Styles)

Функции, возвращающие стили для каждого типа элемента CV:

```python
# Paragraph styles
def section_heading_paragraph() -> dict[str, Any]:
    """H2 заголовки секций."""
    return {
        "namedStyleType": "HEADING_2",
        "spaceBelow": dimension(4.0),
    }

# Text styles
def section_heading_text() -> dict[str, Any]:
    """Текст заголовков секций."""
    return {
        "bold": True,
        "fontSize": dimension(17.0),
    }
```

### 2. Функции применения (Application Functions)

Функции, применяющие стили к конкретным ranges документа:

```python
def apply_section_heading_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к H2 заголовку секции.

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для Google Docs API batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": section_heading_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceBelow",
            }
        },
        {
            "updateTextStyle": {
                "textStyle": section_heading_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize",
            }
        }
    ]
```

### 3. Метаданные темы (Theme Metadata)

```python
THEME_INFO = {
    "name": "HRD Standard",
    "description": "Стандартная тема на основе Stan Sobolev_HRD_2025",
    "author": "Extracted from production document",
    "source_document": "Stan Sobolev_HRD_2025",
    "features": [...],
    "elements": {...}
}
```

## Структура CV документа

### Skills Section

```
Skills                          # H2: section_heading
  {{SKILL_1_TITLE}}            # H3: skill_category
  {skill_description1}         # Normal: skill_description
  {skill_description2}         # Normal: skill_description

  {{SKILL_2_TITLE}}            # H3: skill_category
  {skill_description3}         # Normal: skill_description
```

**Элементы:**
- `section_heading` - H2 заголовок "Skills"
- `skill_category` - H3 категория навыка (например, "Go (Back-End)")
- `skill_description` - Описание навыков в категории

**Стили (HRD Standard):**
- Section heading: H2, bold, 17pt, spaceBelow 4pt
- Skill category: H3, bold, 13pt, spaceAbove 14pt, black color
- Skill description: Normal, spaceAbove/Below 12pt

### Experience Section

```
Experience                      # H2: section_heading

  {exp_company}                # H3: company_name (может содержать ссылку)
  {exp_range} {exp_duration}   # Normal: role_duration
  {company_desc}               # Normal: company_description
  {website}                    # Normal: website_link
  {job_title}                  # Normal: job_title
  {bullet_item}                # Bullet: achievement_bullet
  {bullet_item}                # Bullet: achievement_bullet
  {tech_stack}                 # Normal: tech_stack

  {exp_company}                # H3: следующая компания
  ...
```

**Элементы:**
- `section_heading` - H2 заголовок "Experience"
- `company_name` - H3 название компании (часто ссылка)
- `role_duration` - Роль и даты работы
- `company_description` - Описание компании
- `website_link` - Ссылка на сайт
- `job_title` - Название должности
- `achievement_bullet` - Bullet item с достижением
- `tech_stack` - Список технологий

**Стили (HRD Standard):**
- Section heading: H2, bold, 17pt, spaceBelow 4pt
- Company name: H3, bold, 13pt, black (переопределяет синий цвет ссылок), spaceAbove 14pt
- Role duration: bold, 10pt, black
- Company description: italic, 10pt
- Website link: 10pt
- Achievement bullet: indent 18/36pt, spaceBelow 12pt
- Tech stack: italic

### Education Section

```
Education                       # H2: section_heading

  {edu_title}                  # Normal: education_entry
  {student_role}               # Normal with bold: student_role
  {publications}               # Normal: publications
```

**Элементы:**
- `section_heading` - H2 заголовок "Education"
- `education_entry` - Название учебного заведения, степень
- `student_role` - Роль студента/исследователя
- `publications` - Публикации, работы

**Стили (HRD Standard):**
- Section heading: H2, bold, 17pt, spaceBelow 4pt
- Education entry: Normal, spaceAbove/Below 12pt
- Student role: bold
- Publications: Compact, spaceBelow 10pt

## Использование

### Применить тему к документу

```bash
# Список доступных тем
python3 scripts/apply_cv_styles_themed.py --list-themes

# Применить HRD Standard тему
python3 scripts/apply_cv_styles_themed.py \
  --doc "Stan Sobolev_HRD_2025" \
  --theme hrd_standard

# Применить к документу по ID
python3 scripts/apply_cv_styles_themed.py \
  --doc "1zcyMjH4HyVPPvLq-D4oE8x7qTtES0RPGcruCdU8CbBA" \
  --theme hrd_standard
```

### Создать новую тему

1. Скопируйте `scripts/themes/hrd_standard.py` как шаблон
2. Измените стили элементов
3. Обновите THEME_INFO
4. Сохраните в `scripts/themes/your_theme_name.py`

```python
# scripts/themes/my_custom_theme.py

from typing import Any

def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}

def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    return {"magnitude": magnitude, "unit": unit}

# Определите свои цвета
COLORS = {
    "primary": (0.2, 0.4, 0.8),  # Синий
    "text": (0.1, 0.1, 0.1),     # Темно-серый
}

# Определите стили элементов
def section_heading_text() -> dict[str, Any]:
    return {
        "bold": True,
        "fontSize": dimension(18.0),  # Больше чем в HRD
        "foregroundColor": rgb_color(*COLORS["primary"]),  # Синий цвет
    }

# Функции применения
def apply_section_heading_style(start: int, end: int) -> list[dict[str, Any]]:
    return [
        {
            "updateTextStyle": {
                "textStyle": section_heading_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize,foregroundColor",
            }
        }
    ]

# ... остальные стили ...

THEME_INFO = {
    "name": "My Custom Theme",
    "description": "Кастомная тема с синими акцентами",
    "author": "Your Name",
}
```

### Извлечь стили из существующего документа

```bash
# Показать все стили
python3 scripts/extract_styles.py \
  --doc "Stan Sobolev_HRD_2025"

# Экспортировать в Python файл
python3 scripts/extract_styles.py \
  --doc "Stan Sobolev_HRD_2025" \
  --export .tmp/extracted_styles.py
```

## Переиспользование стилей в коде

### Вариант 1: Через apply_cv_styles_themed.py

Автоматически применяет тему ко всему документу:

```python
from apply_cv_styles_themed import apply_cv_styles_with_theme

apply_cv_styles_with_theme(
    document_id="1zcyMjH4HyVPPvLq-D4oE8x7qTtES0RPGcruCdU8CbBA",
    access_token=access_token,
    theme_name="hrd_standard"
)
```

### Вариант 2: Прямое использование темы

Для точного контроля над применением стилей:

```python
from scripts.themes import hrd_standard as theme
from gdocs_cli import get_doc, docs_batch_update

# Получить документ
doc = get_doc(document_id=doc_id, access_token=token)

# Найти нужные элементы и применить стили
requests = []

# Пример: стилизовать заголовок Skills
skills_heading_start = 200
skills_heading_end = 207
requests.extend(theme.apply_section_heading_style(
    skills_heading_start,
    skills_heading_end
))

# Пример: стилизовать категорию навыка
skill_cat_start = 210
skill_cat_end = 225
requests.extend(theme.apply_skill_category_style(
    skill_cat_start,
    skill_cat_end
))

# Применить все requests
docs_batch_update(
    document_id=doc_id,
    access_token=token,
    requests=requests
)
```

### Вариант 3: Создание нового документа с темой

```bash
# 1. Создать документ из Markdown
python3 gdocs_cli.py import-md templates/cv.md \
  --name "My CV 2025"

# 2. Применить replacements (заполнить данные)
python3 gdocs_cli.py apply --doc "My CV 2025" \
  --data data/my_cv_data.json

# 3. Применить тему
python3 scripts/apply_cv_styles_themed.py \
  --doc "My CV 2025" \
  --theme hrd_standard
```

## Сравнение тем

### HRD Standard (hrd_standard.py)

**Характеристики:**
- Минималистичный подход
- Только черный текст (#000000)
- Типографическая иерархия
- Без цветных акцентов, фонов, рамок
- Извлечен из Stan Sobolev_HRD_2025

**Использование:**
- Консервативные компании
- Традиционные HR отделы
- Максимальная читаемость
- Печать в ч/б

**Ключевые элементы:**
```
H2: 17pt bold
H3: 13pt bold black
Role/duration: 10pt bold black
Company desc: 10pt italic
Tech stack: italic
Bullets: indent 18/36pt
```

### Minimalist (minimalist.py)

**Характеристики:**
- Чистый профессиональный вид
- Только типографика
- Стандартные отступы
- Фокус на контенте

**Отличия от HRD Standard:**
- Может иметь немного другие spacing'и
- Более гибкая типографика

### Colorful (colorful.py)

**Характеристики:**
- Синие акценты (#4A90E2)
- Серые фоны для секций
- Визуальная группировка
- Современный вид

**Цветовая палитра:**
```python
accent_blue: #4A90E2     # Акценты
text_dark: #1A1A1A       # Основной текст
text_gray: #666666       # Даты, метаданные
text_light_gray: #888888 # Tech stack
border_gray: #E0E0E0     # Разделители
bg_gray_1: #F8F9FA       # Skills фон (УБРАН)
bg_gray_2: #F5F5F5       # Education фон
```

**Ключевые элементы:**
```
Skills: синяя левая рамка (2pt)
Experience: серая верхняя рамка (0.5pt)
Company names: черный текст (переопределяет синие ссылки)
Tech stack: 9pt серый
Education: светло-серый фон
```

**Использование:**
- Креативные компании
- Стартапы
- Tech компании
- Онлайн презентация

## API Reference

### Helper Functions

```python
def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    """
    Создать RgbColor объект для Google Docs API.

    Args:
        r: Red компонент (0.0 - 1.0)
        g: Green компонент (0.0 - 1.0)
        b: Blue компонент (0.0 - 1.0)

    Returns:
        Google Docs API color объект
    """

def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    """
    Создать Dimension объект.

    Args:
        magnitude: Размер
        unit: Единица измерения ("PT", "IN", "MM")

    Returns:
        Google Docs API dimension объект
    """
```

### Element Style Functions (HRD Standard)

#### Skills Section

```python
apply_section_heading_style(start: int, end: int) -> list[dict[str, Any]]
apply_skill_category_style(start: int, end: int) -> list[dict[str, Any]]
apply_skill_description_style(start: int, end: int) -> list[dict[str, Any]]
```

#### Experience Section

```python
apply_company_name_style(start: int, end: int) -> list[dict[str, Any]]
apply_role_duration_style(start: int, end: int) -> list[dict[str, Any]]
apply_company_description_style(start: int, end: int) -> list[dict[str, Any]]
apply_website_link_style(start: int, end: int) -> list[dict[str, Any]]
apply_achievement_bullet_style(start: int, end: int) -> list[dict[str, Any]]
apply_tech_stack_style(start: int, end: int) -> list[dict[str, Any]]
```

#### Education Section

```python
apply_student_role_style(start: int, end: int) -> list[dict[str, Any]]
apply_publications_style(start: int, end: int) -> list[dict[str, Any]]
```

### Backward Compatibility Functions

Для совместимости с `apply_cv_styles_themed.py`:

```python
apply_skills_section_style(start: int, end: int) -> list[dict[str, Any]]
apply_experience_block_style(start: int, end: int) -> list[dict[str, Any]]
apply_education_section_style(start: int, end: int) -> list[dict[str, Any]]
```

## Расширенные примеры

### Создать CV с разными секциями в разных темах

```python
from scripts.themes import hrd_standard, colorful
from gdocs_cli import get_doc, docs_batch_update

doc = get_doc(document_id=doc_id, access_token=token)
requests = []

# Skills секция - colorful тема
skills_bullets = find_skills_bullets(doc)
for start, end in skills_bullets:
    requests.extend(colorful.apply_skills_section_style(start, end))

# Experience секция - HRD standard
exp_companies = find_experience_companies(doc)
for start, end in exp_companies:
    requests.extend(hrd_standard.apply_company_name_style(start, end))

# Применить
docs_batch_update(document_id=doc_id, access_token=token, requests=requests)
```

### Создать тему на основе нескольких существующих

```python
# scripts/themes/hybrid.py

from . import hrd_standard, colorful

def apply_section_heading_style(start, end):
    """Использовать HRD standard для заголовков."""
    return hrd_standard.apply_section_heading_style(start, end)

def apply_skills_section_style(start, end):
    """Использовать colorful для Skills."""
    return colorful.apply_skills_section_style(start, end)

def apply_company_name_style(start, end):
    """Использовать HRD standard для компаний."""
    return hrd_standard.apply_company_name_style(start, end)

THEME_INFO = {
    "name": "Hybrid",
    "description": "Комбинация HRD standard + colorful акцентов",
}
```

## Troubleshooting

### Стили не применяются

**Проблема:** Запустили скрипт, но стили не изменились.

**Решения:**
1. Проверьте OAuth scopes - нужен `https://www.googleapis.com/auth/documents`
2. Проверьте что document_id правильный
3. Используйте `--dry-run` для проверки requests

```bash
python3 scripts/apply_cv_styles_themed.py \
  --doc "ID" --theme hrd_standard --dry-run
```

### Ссылки остаются синими

**Проблема:** H3 названия компаний синие (цвет ссылок).

**Решение:** Тема должна переопределять `foregroundColor`:

```python
def company_name_text():
    return {
        "bold": True,
        "fontSize": dimension(13.0),
        "foregroundColor": rgb_color(0.0, 0.0, 0.0),  # Черный
    }
```

И в apply function использовать поле `foregroundColor`:

```python
"fields": "bold,fontSize,foregroundColor"  # Включить foregroundColor
```

### Неправильные ranges

**Проблема:** Стили применяются не к тем элементам.

**Решение:** Используйте `scripts/extract_styles.py` для проверки ranges:

```bash
python3 scripts/extract_styles.py --doc "ID" | grep "Example:"
```

## Best Practices

### 1. Извлечение стилей из существующих документов

Всегда начинайте с анализа:

```bash
python3 scripts/extract_styles.py --doc "Reference Doc"
```

### 2. Именование тем

- `company_name_standard` - для корпоративных стилей
- `creative_blue` - для креативных вариантов
- `minimal_print` - для печати

### 3. Документирование стилей

Всегда указывайте в docstring:
- Точный размер шрифта
- Цвета (hex + rgb)
- Spacing значения
- Когда использовать этот стиль

### 4. Тестирование

Создайте тестовый документ с всеми элементами:

```bash
python3 gdocs_cli.py import-md .tmp/test-cv.md --name "Theme Test"
python3 scripts/apply_cv_styles_themed.py --doc "Theme Test" --theme your_theme
```

### 5. Версионирование

Храните версии тем в Git:

```
scripts/themes/
  hrd_standard_v1.py
  hrd_standard_v2.py (current)
```

## См. также

- [Google Docs API - Format Text](https://developers.google.com/workspace/docs/api/how-tos/format-text)
- [Google Docs API - batchUpdate](https://developers.google.com/docs/api/reference/rest/v1/documents/batchUpdate)
- [CV_AUTO_GUIDE.md](../CV-AUTO-GUIDE.md) - общий guide по CV системе
- [TEMPLATE_USE.md](../TEMPLATE_USE.md) - использование templates
