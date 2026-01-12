"""
Стандартная тема HRD на основе Stan Sobolev_HRD_2025.

Эта тема извлечена из реального документа и содержит переиспользуемые стили
для каждого элемента CV структуры.

СТРУКТУРА ЭЛЕМЕНТОВ:

## Skills Section
```
Skills                          # H2: section_heading
  {{SKILL_1_TITLE}}            # H3: skill_category_heading
  {skill_description1}         # Normal: skill_description
  {skill_description2}
```

## Experience Section
```
Experience                      # H2: section_heading
  {exp_company}                # H3: company_name (может быть ссылкой)
  {exp_range} {exp_duration}   # Normal: role_duration (bold, 10pt)
  {company_desc}               # Normal: company_description (italic, 10pt)
  {website}                    # Normal: website_link (10pt)
  {job_title}                  # Normal: job_title
  {bullet_item}                # Bullet: achievement_bullet
  {tech_stack}                 # Normal: tech_stack (italic)
```

## Education Section
```
Education                       # H2: section_heading
  {edu_title}                  # Normal: education_entry
  {student_role}               # Normal with bold: student_role
  {publications}               # Normal: publications
```

ИСПОЛЬЗОВАНИЕ:

```python
from themes import hrd_standard as theme

# Применить стиль к заголовку секции
requests = theme.apply_section_heading_style(start, end)

# Применить стиль к категории навыка
requests = theme.apply_skill_category_style(start, end)

# Применить стиль к роли и датам
requests = theme.apply_role_duration_style(start, end)
```
"""
from typing import Any


# === HELPER FUNCTIONS ===

def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    """Создать RgbColor объект для Google Docs API."""
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}


def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    """Создать Dimension объект."""
    return {"magnitude": magnitude, "unit": unit}


# === ЦВЕТА ===
# HRD тема использует только черный текст (минималистичный подход)
COLORS = {
    "text_black": (0.0, 0.0, 0.0),  # #000000 - все тексты
}


# === PARAGRAPH STYLES ===

def section_heading_paragraph() -> dict[str, Any]:
    """
    H2 заголовки секций: Summary, Skills, Experience, Education.

    Стиль:
    - namedStyleType: HEADING_2
    - spaceBelow: 4pt
    """
    return {
        "namedStyleType": "HEADING_2",
        "spaceBelow": dimension(4.0),
    }


def skill_category_paragraph() -> dict[str, Any]:
    """
    H3 категории навыков: {{SKILL_1_TITLE}}, {{SKILL_2_TITLE}}.

    Стиль:
    - namedStyleType: HEADING_3
    - spaceAbove: 14pt
    """
    return {
        "namedStyleType": "HEADING_3",
        "spaceAbove": dimension(14.0),
    }


def normal_paragraph() -> dict[str, Any]:
    """
    Обычный параграф: описания, тексты.

    Стиль:
    - namedStyleType: NORMAL_TEXT
    - spaceAbove: 12pt
    - spaceBelow: 12pt
    """
    return {
        "namedStyleType": "NORMAL_TEXT",
        "spaceAbove": dimension(12.0),
        "spaceBelow": dimension(12.0),
    }


def bullet_paragraph() -> dict[str, Any]:
    """
    Bullet list items: {bullet_item}.

    Стиль:
    - indentFirstLine: 18pt
    - indentStart: 36pt
    - namedStyleType: NORMAL_TEXT
    - spaceBelow: 12pt
    """
    return {
        "indentFirstLine": dimension(18.0),
        "indentStart": dimension(36.0),
        "namedStyleType": "NORMAL_TEXT",
        "spaceBelow": dimension(12.0),
    }


def compact_paragraph() -> dict[str, Any]:
    """
    Компактный параграф: publications, менее важные элементы.

    Стиль:
    - namedStyleType: NORMAL_TEXT
    - spaceBelow: 10pt
    """
    return {
        "namedStyleType": "NORMAL_TEXT",
        "spaceBelow": dimension(10.0),
    }


# === TEXT STYLES ===

def heading_1_text() -> dict[str, Any]:
    """
    Текст заголовка H1: Имя.

    Стиль:
    - fontSize: 23pt
    - weightedFontFamily: Arial
    """
    return {
        "fontSize": dimension(23.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def section_heading_text() -> dict[str, Any]:
    """
    Текст заголовков секций H2: Summary, Skills, Experience.

    Стиль:
    - bold: true
    - fontSize: 17pt
    - weightedFontFamily: Arial
    """
    return {
        "bold": True,
        "fontSize": dimension(17.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def skill_category_text() -> dict[str, Any]:
    """
    Текст категорий навыков H3: {{SKILL_1_TITLE}}.

    Стиль:
    - bold: true
    - fontSize: 13pt
    - foregroundColor: #000000
    - weightedFontFamily: Arial
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def company_name_text() -> dict[str, Any]:
    """
    Текст названия компании H3: {exp_company}.

    Стиль:
    - bold: true
    - fontSize: 13pt
    - foregroundColor: #000000 (переопределяет синий цвет ссылок)
    - weightedFontFamily: Arial
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def role_duration_text() -> dict[str, Any]:
    """
    Текст роли и дат: {exp_range} {exp_duration}.

    Стиль:
    - bold: true
    - fontSize: 10pt
    - foregroundColor: #000000
    - weightedFontFamily: Arial
    """
    return {
        "bold": True,
        "fontSize": dimension(10.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def company_description_text() -> dict[str, Any]:
    """
    Описание компании: {company_desc}.

    Стиль:
    - fontSize: 10pt
    - italic: true
    - weightedFontFamily: Arial
    """
    return {
        "fontSize": dimension(10.0),
        "italic": True,
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def website_link_text() -> dict[str, Any]:
    """
    Ссылка на вебсайт: {website}.

    Стиль:
    - fontSize: 10pt
    - weightedFontFamily: Arial
    """
    return {
        "fontSize": dimension(10.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def tech_stack_text() -> dict[str, Any]:
    """
    Список технологий: {tech_stack}.

    Стиль:
    - italic: true
    - fontSize: 11pt
    - weightedFontFamily: Arial
    """
    return {
        "italic": True,
        "fontSize": dimension(11.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def student_role_text() -> dict[str, Any]:
    """
    Роль студента/исследователя: {student_role}.

    Стиль:
    - bold: true
    - fontSize: 11pt
    - weightedFontFamily: Arial
    """
    return {
        "bold": True,
        "fontSize": dimension(11.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


def normal_text() -> dict[str, Any]:
    """
    Обычный текст: базовый стиль для всего документа.

    Стиль:
    - fontSize: 11pt
    - weightedFontFamily: Arial
    """
    return {
        "fontSize": dimension(11.0),
        "weightedFontFamily": {
            "fontFamily": "Arial",
            "weight": 400
        }
    }


# === APPLICATION FUNCTIONS ===
# Эти функции применяют стили к конкретным ranges в документе

def apply_heading_1_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к H1 заголовку (имя).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": {
                    "namedStyleType": "HEADING_1",
                },
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType",
            }
        },
        {
            "updateTextStyle": {
                "textStyle": heading_1_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "fontSize,weightedFontFamily",
            }
        }
    ]


def apply_section_heading_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к H2 заголовку секции (Summary, Skills, Experience, Education).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
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
                "fields": "bold,fontSize,weightedFontFamily",
            }
        }
    ]


def apply_skill_category_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к H3 категории навыка ({{SKILL_1_TITLE}}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": skill_category_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceAbove",
            }
        },
        {
            "updateTextStyle": {
                "textStyle": skill_category_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize,foregroundColor,weightedFontFamily",
            }
        }
    ]


def apply_skill_description_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к описанию навыка ({skill_description}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": normal_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceAbove,spaceBelow",
            }
        }
    ]


def apply_company_name_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к названию компании H3 ({exp_company}).

    ВАЖНО: Переопределяет синий цвет ссылок на черный.

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": skill_category_paragraph(),  # Same as skill category
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceAbove",
            }
        },
        {
            "updateTextStyle": {
                "textStyle": company_name_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize,foregroundColor,weightedFontFamily",
            }
        }
    ]


def apply_role_duration_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к роли и датам ({exp_range} {exp_duration}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": role_duration_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize,foregroundColor,weightedFontFamily",
            }
        }
    ]


def apply_company_description_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к описанию компании ({company_desc}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": company_description_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "fontSize,italic,weightedFontFamily",
            }
        }
    ]


def apply_website_link_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к ссылке на вебсайт ({website}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": website_link_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "fontSize,weightedFontFamily",
            }
        }
    ]


def apply_achievement_bullet_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к bullet item достижения ({bullet_item}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": bullet_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "indentFirstLine,indentStart,namedStyleType,spaceBelow",
            }
        },
        {
            "updateTextStyle": {
                "textStyle": normal_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "fontSize,weightedFontFamily",
            }
        }
    ]


def apply_tech_stack_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к списку технологий ({tech_stack}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": tech_stack_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "italic,fontSize,weightedFontFamily",
            }
        }
    ]


def apply_student_role_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к роли студента ({student_role}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": student_role_text(),
                "range": {"startIndex": start, "endIndex": end - 1},
                "fields": "bold,fontSize,weightedFontFamily",
            }
        }
    ]


def apply_publications_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к публикациям ({publications}).

    Args:
        start: startIndex параграфа
        end: endIndex параграфа

    Returns:
        Список requests для batchUpdate
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": compact_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceBelow",
            }
        }
    ]


# === BACKWARD COMPATIBILITY ===
# Функции для совместимости с apply_cv_styles_themed.py

def apply_skills_section_style(start: int, end: int) -> list[dict[str, Any]]:
    """Skills bullets - используем achievement_bullet_style."""
    return apply_achievement_bullet_style(start, end)


def apply_experience_block_style(start: int, end: int) -> list[dict[str, Any]]:
    """Experience block heading - используем company_name_style."""
    return apply_company_name_style(start, end)


def apply_education_section_style(start: int, end: int) -> list[dict[str, Any]]:
    """Education paragraphs - обычный paragraph."""
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": normal_paragraph(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceAbove,spaceBelow",
            }
        }
    ]


# === THEME METADATA ===

THEME_INFO = {
    "name": "HRD Standard",
    "description": "Стандартная тема на основе Stan Sobolev_HRD_2025",
    "author": "Extracted from production document",
    "source_document": "Stan Sobolev_HRD_2025",
    "features": [
        "Минималистичный подход - только типографика",
        "Черный текст (#000000) для всех элементов",
        "Четкая иерархия через размеры шрифтов",
        "Стандартные отступы и spacing",
        "Переиспользуемые стили для каждого элемента CV",
    ],
    "elements": {
        "Skills": {
            "section_heading": "H2, bold, 17pt",
            "skill_category": "H3, bold, 13pt, spaceAbove 14pt",
            "skill_description": "Normal, 12pt spacing",
        },
        "Experience": {
            "section_heading": "H2, bold, 17pt",
            "company_name": "H3, bold, 13pt, black (overrides link color)",
            "role_duration": "Bold, 10pt",
            "company_description": "Italic, 10pt",
            "website": "10pt",
            "achievement_bullet": "Bullet with indent 18/36pt",
            "tech_stack": "Italic",
        },
        "Education": {
            "section_heading": "H2, bold, 17pt",
            "education_entry": "Normal, 12pt spacing",
            "student_role": "Bold",
            "publications": "Compact, 10pt spaceBelow",
        }
    }
}
