"""
Цветная тема для CV.

Использует цветные акценты для визуального выделения секций.

Характеристики:
- Серые фоны для Skills и Education секций
- Синие акцентные рамки для Skills
- Серые разделители для Experience блоков
- Типографическая иерархия + цветовые акценты
- Профессиональная цветовая палитра
"""
from typing import Any


# === ЦВЕТОВАЯ ПАЛИТРА ===
COLORS = {
    "accent_blue": (0.290, 0.565, 0.886),    # #4A90E2 - синий акцент
    "text_dark": (0.102, 0.102, 0.102),      # #1A1A1A - основной текст
    "text_gray": (0.400, 0.400, 0.400),      # #666666 - даты, метаданные
    "text_light_gray": (0.533, 0.533, 0.533),# #888888 - tech stack
    "border_gray": (0.878, 0.878, 0.878),    # #E0E0E0 - разделители
    "bg_gray_1": (0.973, 0.976, 0.980),      # #F8F9FA - Skills фон
    "bg_gray_2": (0.961, 0.961, 0.961),      # #F5F5F5 - Education фон
}


# === HELPER FUNCTIONS ===

def rgb_color(r: float, g: float, b: float) -> dict[str, Any]:
    """Создать RgbColor объект для Google Docs API."""
    return {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}


def dimension(magnitude: float, unit: str = "PT") -> dict[str, Any]:
    """Создать Dimension объект."""
    return {"magnitude": magnitude, "unit": unit}


def border(color_rgb: tuple[float, float, float], width: float = 2.0,
           padding: float = 8.0, dash_style: str = "SOLID") -> dict[str, Any]:
    """Создать ParagraphBorder объект."""
    return {
        "color": rgb_color(*color_rgb),
        "width": dimension(width),
        "padding": dimension(padding),
        "dashStyle": dash_style,
    }


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
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
    }


def company_name_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для названий компаний (H3 в Experience).

    Характеристики:
    - bold: true
    - fontSize: 13pt
    """
    return {
        "bold": True,
        "fontSize": dimension(13.0),
    }


def role_duration_text_style() -> dict[str, Any]:
    """
    Текстовый стиль для роли и дат работы.

    Характеристики:
    - bold: true
    - fontSize: 10pt
    """
    return {
        "bold": True,
        "fontSize": dimension(10.0),
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

    ОБНОВЛЕНО: Убран фон по запросу пользователя.
    Оставлена только синяя левая рамка для визуального акцента.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": {
                    "borderLeft": border(COLORS["accent_blue"], width=2.0),
                    "indentStart": dimension(12.0),
                    "spaceAbove": dimension(4.0),
                    "spaceBelow": dimension(4.0),
                },
                "range": {"startIndex": start, "endIndex": end},
                "fields": "borderLeft,indentStart,spaceAbove,spaceBelow",
            }
        }
    ]


def apply_experience_block_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к блоку Experience.

    В цветной теме блоки опыта имеют верхнюю серую рамку-разделитель.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": {
                    "borderTop": border(COLORS["border_gray"], width=0.5),
                    "spaceAbove": dimension(10.0),
                    "spaceBelow": dimension(6.0),
                },
                "range": {"startIndex": start, "endIndex": end},
                "fields": "borderTop,spaceAbove,spaceBelow",
            }
        }
    ]


def apply_company_name_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к названию компании.

    ВАЖНО: Сбрасываем синий цвет ссылок на черный.
    Google Docs по умолчанию красит ссылки в синий, но мы хотим черный текст.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": {
                    "bold": True,
                    "fontSize": dimension(13.0),
                    "foregroundColor": rgb_color(*COLORS["text_dark"]),  # Черный вместо синего
                },
                "range": {"startIndex": start, "endIndex": end - 1},
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
    Применить малый серый шрифт к списку технологий.

    В цветной теме tech stack выделен серым цветом и меньшим размером.
    """
    return [
        {
            "updateTextStyle": {
                "textStyle": {
                    "fontSize": dimension(9.0),
                    "foregroundColor": rgb_color(*COLORS["text_light_gray"]),
                },
                "range": {"startIndex": start, "endIndex": end - 1},  # -1 чтобы не захватить \n
                "fields": "fontSize,foregroundColor",
            }
        }
    ]


def apply_education_section_style(start: int, end: int) -> list[dict[str, Any]]:
    """
    Применить стиль к Education секции.

    В цветной теме Education имеет светлый серый фон.
    """
    return [
        {
            "updateParagraphStyle": {
                "paragraphStyle": {
                    "shading": {"backgroundColor": rgb_color(*COLORS["bg_gray_2"])},
                    "spaceAbove": dimension(5.0),
                    "spaceBelow": dimension(5.0),
                },
                "range": {"startIndex": start, "endIndex": end},
                "fields": "shading.backgroundColor,spaceAbove,spaceBelow",
            }
        }
    ]


# === THEME METADATA ===

THEME_INFO = {
    "name": "Colorful",
    "description": "Профессиональный стиль с цветными акцентами",
    "author": "Custom design",
    "features": [
        "Серые фоны для Skills и Education",
        "Синие акцентные рамки",
        "Серые разделители для Experience",
        "Цветовая иерархия",
        "Визуальная группировка секций",
    ],
}
