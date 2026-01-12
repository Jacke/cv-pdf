"""
Минималистичная тема для CV.

Основана на существующем документе Stan Sobolev_HRD_2025.
Использует только типографику без цветных фонов и рамок.

Характеристики:
- Чистый профессиональный вид
- Фокус на контенте, не на визуальных эффектах
- Типографическая иерархия через размеры шрифтов и bold/italic
- Стандартные отступы и spacing
"""
from typing import Any


# === ЦВЕТОВАЯ ПАЛИТРА ===
# Минималистичная тема использует только черный текст
COLORS = {
    "text_black": (0.0, 0.0, 0.0),          # #000000 - основной текст
    "text_dark": (0.102, 0.102, 0.102),     # #1A1A1A - немного мягче черного
}


# === HELPER FUNCTIONS ===

def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    """Создать RgbColor объект для Google Docs API."""
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}


def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    """Создать Dimension объект."""
    return {"magnitude": magnitude, "unit": unit}


# === PARAGRAPH STYLES ===

def heading_2_style() -> dict[str, Any]:
    """
    Стиль для H2 заголовков секций (Summary, Skills, Experience, Education).

    Характеристики:
    - namedStyleType: HEADING_2
    - spaceBelow: 4pt
    """
    return {
        "namedStyleType": "HEADING_2",
        "spaceBelow": dimension(4.0),
    }


def heading_3_style() -> dict[str, Any]:
    """
    Стиль для H3 подзаголовков (категории навыков, названия компаний).

    Характеристики:
    - namedStyleType: HEADING_3
    - spaceAbove: 14pt
    """
    return {
        "namedStyleType": "HEADING_3",
        "spaceAbove": dimension(14.0),
    }


def normal_paragraph_style() -> dict[str, Any]:
    """
    Стиль для обычных параграфов.

    Характеристики:
    - namedStyleType: NORMAL_TEXT
    - spaceAbove: 12pt
    - spaceBelow: 12pt
    """
    return {
        "namedStyleType": "NORMAL_TEXT",
        "spaceAbove": dimension(12.0),
        "spaceBelow": dimension(12.0),
    }


def bullet_list_style() -> dict[str, Any]:
    """
    Стиль для bullet list items.

    Характеристики:
    - indentFirstLine: 18pt
    - indentStart: 36pt
    - spaceBelow: 12pt
    """
    return {
        "indentFirstLine": dimension(18.0),
        "indentStart": dimension(36.0),
        "namedStyleType": "NORMAL_TEXT",
        "spaceBelow": dimension(12.0),
    }


def compact_paragraph_style() -> dict[str, Any]:
    """
    Компактный стиль для некоторых секций.

    Характеристики:
    - spaceBelow: 10pt (меньше чем обычный)
    """
    return {
        "namedStyleType": "NORMAL_TEXT",
        "spaceBelow": dimension(10.0),
    }


# === TEXT STYLES ===

def section_heading_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для заголовков секций (Summary, Skills, Experience).

    Характеристики:
    - bold: true
    - fontSize: 17pt
    """
    return {
        "bold": True,
        "fontSize": dimension(17.0),
    }


def subsection_heading_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для подзаголовков (категории навыков).

    Характеристики:
    - bold: true
    - fontSize: 13pt
    - foregroundColor: black
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
    }


def company_name_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для названий компаний (H3 в Experience).

    Характеристики:
    - bold: true
    - fontSize: 13pt
    - foregroundColor: black
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
    }


def role_duration_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для роли и дат работы.

    Характеристики:
    - bold: true
    - fontSize: 10pt
    - foregroundColor: black
    """
    return {
        "bold": True,
        "fontSize": dimension(10.0),
        "foregroundColor": rgb_color(*COLORS["text_black"]),
    }


def company_description_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для описания компании.

    Характеристики:
    - fontSize: 10pt
    - italic: true
    """
    return {
        "fontSize": dimension(10.0),
        "italic": True,
    }


def tech_stack_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для списка технологий.

    Характеристики:
    - italic: true
    """
    return {
        "italic": True,
    }


def normal_text_style() -> dict[str, Any]:
    """
    Обычный текст без особого форматирования.
    """
    return {}


# === THEME APPLICATION FUNCTIONS ===

def apply_skills_section_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к Skills секции.

    В минималистичной теме Skills bullets не имеют специального фона,
    только стандартные отступы списка.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": bullet_list_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "indentFirstLine,indentStart,namedStyleType,spaceBelow",
            }
        }
    ]


def apply_experience_block_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к блоку Experience.

    В минималистичной теме блоки опыта разделяются только spacing,
    без визуальных рамок.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": heading_3_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceAbove",
            }
        }
    ]


def apply_company_name_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к названию компании.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": company_name_text_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "bold,fontSize,foregroundColor",
            }
        }
    ]


def apply_role_duration_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к строке роли и дат.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": role_duration_text_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "bold,fontSize,foregroundColor",
            }
        }
    ]


def apply_company_description_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить italic к описанию компании.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": company_description_text_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "fontSize,italic",
            }
        }
    ]


def apply_tech_stack_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить italic к списку технологий.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": tech_stack_text_style(),
                "range": {"startIndex": start, "endIndex": end - 1},  # -1 чтобы не захватить \n
                "fields": "italic",
            }
        }
    ]


def apply_education_section_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к Education секции.

    В минималистичной теме просто компактные отступы.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": compact_paragraph_style(),
                "range": {"startIndex": start, "endIndex": end},
                "fields": "namedStyleType,spaceBelow",
            }
        }
    ]


# === THEME METADATA ===

THEME_INFO = {
    "name": "Minimalist",
    "description": "Чистый профессиональный стиль без цветных акцентов",
    "author": "Based on Stan Sobolev_HRD_2025",
    "features": [
        "Типографическая иерархия",
        "Стандартные отступы",
        "Только black текст",
        "Без фонов и рамок",
        "Фокус на контенте",
    ],
}
