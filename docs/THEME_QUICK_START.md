# CV Theme System - Quick Start

## Быстрый старт

### 1. Список доступных тем

```bash
python3 scripts/apply_cv_styles_themed.py --list-themes
```

### 2. Применить тему к документу

```bash
# По имени документа (из GOOGLE_DOCS_LINKS.md)
python3 scripts/apply_cv_styles_themed.py \
  --doc "Stan Sobolev_HRD_2025" \
  --theme hrd_standard

# По document ID
python3 scripts/apply_cv_styles_themed.py \
  --doc "1zcyMjH4HyVPPvLq-D4oE8x7qTtES0RPGcruCdU8CbBA" \
  --theme hrd_standard
```

### 3. Создать новый CV с темой

```bash
# Шаг 1: Создать документ из Markdown
python3 gdocs_cli.py import-md templates/cv.md --name "My CV 2025"

# Шаг 2: Заполнить данные
python3 gdocs_cli.py apply --doc "My CV 2025" \
  --data data/my_cv_data.json

# Шаг 3: Применить тему
python3 scripts/apply_cv_styles_themed.py \
  --doc "My CV 2025" \
  --theme hrd_standard
```

## Доступные темы

### hrd_standard

**Для кого:** Консервативные компании, традиционные HR отделы
**Стиль:** Минималистичный, только типографика, черный текст

**Элементы:**
- H2 заголовки: 17pt bold
- H3 категории: 13pt bold black
- Роли/даты: 10pt bold
- Описания компаний: 10pt italic
- Tech stack: italic
- Bullets: indent 18/36pt

**Применить:**
```bash
--theme hrd_standard
```

### colorful

**Для кого:** Креативные компании, стартапы, tech компании
**Стиль:** Цветные акценты, визуальные разделители

**Элементы:**
- Skills: синяя левая рамка (#4A90E2)
- Experience: серая верхняя рамка-разделитель
- Company names: черный текст (переопределяет синий цвет ссылок)
- Tech stack: 9pt серый (#888888)
- Education: светло-серый фон (#F5F5F5)

**Применить:**
```bash
--theme colorful
```

### minimalist

**Для кого:** Универсальный профессиональный стиль
**Стиль:** Чистый, фокус на контенте

**Применить:**
```bash
--theme minimalist
```

## Структура CV для тем

Темы работают с следующей структурой документа:

```markdown
# {name}
{title}

## Summary
{summary_paragraph}

## Skills
### {{SKILL_1_TITLE}}
{skill_description1}
{skill_description2}

### {{SKILL_2_TITLE}}
{skill_description3}

## Experience
### {exp_company}
{exp_range} {exp_duration}
{company_desc}
{website}
{job_title}
- {bullet_item}
- {bullet_item}
{tech_stack}

## Education
{edu_title}
{student_role}
{publications}
```

## Элементы и их стили

### Skills Section

| Элемент | HRD Standard | Colorful |
|---------|--------------|----------|
| Section heading (H2) | 17pt bold | 17pt bold |
| Category (H3) | 13pt bold black | 13pt bold black |
| Description | Normal 12pt | Normal 12pt |
| **Визуальные акценты** | Нет | Синяя левая рамка |

### Experience Section

| Элемент | HRD Standard | Colorful |
|---------|--------------|----------|
| Section heading (H2) | 17pt bold | 17pt bold |
| Company name (H3) | 13pt bold black | 13pt bold black |
| Role/duration | 10pt bold | 10pt bold |
| Company desc | 10pt italic | 10pt italic |
| Website | 10pt | 10pt |
| Bullet items | indent 18/36pt | indent 18/36pt |
| Tech stack | italic | 9pt italic gray |
| **Визуальные акценты** | Нет | Серая верхняя рамка |

### Education Section

| Элемент | HRD Standard | Colorful |
|---------|--------------|----------|
| Section heading (H2) | 17pt bold | 17pt bold |
| Entry | Normal 12pt | Normal 12pt |
| Student role | bold | bold |
| Publications | compact 10pt | compact 10pt |
| **Визуальные акценты** | Нет | Светло-серый фон |

## Переиспользование стилей в коде

### Вариант 1: Автоматически (весь документ)

```python
from apply_cv_styles_themed import apply_cv_styles_with_theme

apply_cv_styles_with_theme(
    document_id="doc_id",
    access_token=token,
    theme_name="hrd_standard"
)
```

### Вариант 2: Вручную (точный контроль)

```python
from scripts.themes import hrd_standard as theme

# Стилизовать конкретный элемент
requests = theme.apply_company_name_style(start=300, end=310)
requests.extend(theme.apply_role_duration_style(start=311, end=350))
requests.extend(theme.apply_tech_stack_style(start=451, end=480))

# Применить
docs_batch_update(document_id=doc_id, access_token=token, requests=requests)
```

### Доступные функции (HRD Standard)

**Skills:**
- `apply_section_heading_style(start, end)`
- `apply_skill_category_style(start, end)`
- `apply_skill_description_style(start, end)`

**Experience:**
- `apply_company_name_style(start, end)`
- `apply_role_duration_style(start, end)`
- `apply_company_description_style(start, end)`
- `apply_website_link_style(start, end)`
- `apply_achievement_bullet_style(start, end)`
- `apply_tech_stack_style(start, end)`

**Education:**
- `apply_student_role_style(start, end)`
- `apply_publications_style(start, end)`
- `apply_education_section_style(start, end)`

## Извлечь стили из документа

```bash
# Показать все стили
python3 scripts/extract_styles.py --doc "Stan Sobolev_HRD_2025"

# Экспортировать в Python
python3 scripts/extract_styles.py \
  --doc "Stan Sobolev_HRD_2025" \
  --export .tmp/extracted.py
```

## Создать свою тему

1. Скопируйте `scripts/themes/hrd_standard.py`
2. Переименуйте: `scripts/themes/my_theme.py`
3. Измените стили и цвета
4. Обновите `THEME_INFO`
5. Используйте: `--theme my_theme`

Пример:

```python
# scripts/themes/my_theme.py

COLORS = {
    "primary": (0.2, 0.4, 0.8),  # Синий
}

def section_heading_text():
    return {
        "bold": True,
        "fontSize": dimension(18.0),
        "foregroundColor": rgb_color(*COLORS["primary"]),
    }

# ... остальные функции ...

THEME_INFO = {
    "name": "My Theme",
    "description": "Моя кастомная тема",
}
```

## Troubleshooting

### Стили не применились

```bash
# Проверьте OAuth scopes
python3 gdocs_cli.py auth --scopes \
  https://www.googleapis.com/auth/documents \
  https://www.googleapis.com/auth/drive

# Проверьте что будет применено (dry run)
python3 scripts/apply_cv_styles_themed.py \
  --doc "ID" --theme hrd_standard --dry-run
```

### Ссылки синие

Тема должна переопределять цвет через `foregroundColor`:

```python
"foregroundColor": rgb_color(0.0, 0.0, 0.0),  # Черный
"fields": "bold,fontSize,foregroundColor"      # Включить поле
```

## Полная документация

См. [CV_THEME_SYSTEM.md](CV_THEME_SYSTEM.md) для:
- Детальное описание архитектуры
- API reference всех функций
- Расширенные примеры
- Best practices
