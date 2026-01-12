# CV Theme System - Summary

## Что было реализовано

### 1. Извлечены стили из Stan Sobolev_HRD_2025

Проанализирован существующий документ и извлечены точные стили для каждого элемента:

**Skills Section:**
- H2 заголовок: 17pt bold, spaceBelow 4pt
- H3 категории: 13pt bold black, spaceAbove 14pt
- Описания: Normal, spaceAbove/Below 12pt

**Experience Section:**
- H3 названия компаний: 13pt bold black (переопределяет синий цвет ссылок)
- Роль/даты: 10pt bold black
- Описание компании: 10pt italic
- Website: 10pt
- Bullet items: indent 18/36pt, spaceBelow 12pt
- Tech stack: italic

**Education Section:**
- Normal paragraphs: spaceAbove/Below 12pt
- Student role: bold
- Publications: compact, spaceBelow 10pt

### 2. Создана тема hrd_standard

**Файл:** [scripts/themes/hrd_standard.py](../scripts/themes/hrd_standard.py)

**Характеристики:**
- 600+ строк кода
- Полностью документирована
- Переиспользуемые функции для каждого элемента
- Совместима с apply_cv_styles_themed.py

**Функции стилизации:**

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

**Backward Compatibility:**
- `apply_skills_section_style(start, end)`
- `apply_experience_block_style(start, end)`

### 3. Создана документация

**[docs/CV_THEME_SYSTEM.md](CV_THEME_SYSTEM.md)** (200+ строк)
- Полная документация системы
- Архитектура тем
- API Reference
- Расширенные примеры
- Troubleshooting
- Best practices

**[docs/THEME_QUICK_START.md](THEME_QUICK_START.md)** (150+ строк)
- Быстрый старт
- Сравнение тем
- Практические примеры
- Таблица стилей элементов

**Обновлен [CV-AUTO-GUIDE.md](../CV-AUTO-GUIDE.md)**
- Добавлена секция о системе стилизации
- Ссылки на документацию

### 4. Протестирована система

**Тестовые документы:**
- CV Style Test 20260102_162922 (1zcyMjH4HyVPPvLq-D4oE8x7qTtES0RPGcruCdU8CbBA)
- CV Theme Comparison 20260102_144653 (1C0sAkH3KNDcVrSBnGVdiZgu9hjEMLPkEZaUY7oulpwU)

**Результаты:**
✅ hrd_standard тема применена успешно (30 style requests)
✅ Все элементы стилизованы корректно
✅ Черный цвет для всех текстов (включая ссылки)
✅ Правильные spacing и индентация

## Структура файлов

```
CV/
├── scripts/
│   ├── themes/
│   │   ├── hrd_standard.py      # НОВЫЙ - Стандартная HRD тема
│   │   ├── minimalist.py        # Существующая минималистичная тема
│   │   └── colorful.py          # Существующая цветная тема
│   ├── apply_cv_styles_themed.py # Скрипт применения тем
│   ├── apply_cv_styles.py        # Базовая стилизация (устаревает)
│   └── extract_styles.py         # Извлечение стилей из документов
├── docs/
│   ├── CV_THEME_SYSTEM.md       # НОВЫЙ - Полная документация
│   ├── THEME_QUICK_START.md     # НОВЫЙ - Быстрый старт
│   └── THEME_SYSTEM_SUMMARY.md  # НОВЫЙ - Этот файл
└── CV-AUTO-GUIDE.md             # ОБНОВЛЕН - Добавлена секция о темах
```

## Использование

### Применить hrd_standard тему

```bash
# К существующему документу
python3 scripts/apply_cv_styles_themed.py \
  --doc "Stan Sobolev_HRD_2025" \
  --theme hrd_standard

# К новому документу
python3 gdocs_cli.py import-md templates/cv.md --name "My CV"
python3 gdocs_cli.py apply --doc "My CV" --data data/cv_data.json
python3 scripts/apply_cv_styles_themed.py --doc "My CV" --theme hrd_standard
```

### Переиспользовать стили в коде

```python
from scripts.themes import hrd_standard as theme

# Стилизовать конкретные элементы
requests = []
requests.extend(theme.apply_company_name_style(start=300, end=310))
requests.extend(theme.apply_role_duration_style(start=311, end=350))
requests.extend(theme.apply_tech_stack_style(start=451, end=480))

# Применить к документу
docs_batch_update(document_id=doc_id, access_token=token, requests=requests)
```

### Список доступных тем

```bash
python3 scripts/apply_cv_styles_themed.py --list-themes
```

Вывод:
```
Available themes:
  colorful        - Профессиональный стиль с цветными акцентами
  hrd_standard    - Стандартная тема на основе Stan Sobolev_HRD_2025
  minimalist      - Чистый профессиональный стиль без цветных акцентов
```

## Элементы CV и их стили

### Mapping элементов в документе

| Элемент в документе | Тип | HRD Standard Style | Функция |
|---------------------|-----|-------------------|---------|
| Skills | H2 | 17pt bold, spaceBelow 4pt | `apply_section_heading_style()` |
| {{SKILL_1_TITLE}} | H3 | 13pt bold black, spaceAbove 14pt | `apply_skill_category_style()` |
| {skill_description} | Normal | 12pt spacing | `apply_skill_description_style()` |
| Experience | H2 | 17pt bold, spaceBelow 4pt | `apply_section_heading_style()` |
| {exp_company} | H3 | 13pt bold black | `apply_company_name_style()` |
| {exp_range} {exp_duration} | Normal | 10pt bold black | `apply_role_duration_style()` |
| {company_desc} | Normal | 10pt italic | `apply_company_description_style()` |
| {website} | Normal | 10pt | `apply_website_link_style()` |
| {bullet_item} | Bullet | indent 18/36pt | `apply_achievement_bullet_style()` |
| {tech_stack} | Normal | italic | `apply_tech_stack_style()` |
| Education | H2 | 17pt bold, spaceBelow 4pt | `apply_section_heading_style()` |
| {student_role} | Normal | bold | `apply_student_role_style()` |
| {publications} | Normal | compact 10pt | `apply_publications_style()` |

## Преимущества системы

✅ **Переиспользуемость** - Один раз извлечь стили, применять к любым документам

✅ **Консистентность** - Все CV выглядят одинаково в рамках одной темы

✅ **Документированность** - Каждая функция с docstring, примерами, точными размерами

✅ **Модульность** - Каждый элемент стилизуется отдельной функцией

✅ **Расширяемость** - Легко создавать новые темы на основе существующих

✅ **Автоматизация** - Применение темы = одна команда

✅ **API-driven** - Прямое использование Google Docs API, без Pandoc

## Что дальше

### Возможные улучшения

1. **Автоматическое определение элементов**
   - Парсить документ и автоматически находить {placeholders}
   - Применять соответствующие стили без ручного указания ranges

2. **Тема-конструктор**
   - Web UI для создания тем
   - Визуальный предпросмотр стилей

3. **Темы для разных отраслей**
   - `finance_standard` - для финансового сектора
   - `creative_design` - для дизайнеров/креативных ролей
   - `tech_startup` - для стартапов

4. **Экспорт в другие форматы**
   - PDF с сохранением стилей
   - HTML с соответствующим CSS

5. **A/B тестирование тем**
   - Статистика откликов по разным темам
   - Рекомендации какую тему использовать

## Команды для работы

```bash
# Список тем
python3 scripts/apply_cv_styles_themed.py --list-themes

# Применить тему
python3 scripts/apply_cv_styles_themed.py --doc "DOC_ID" --theme hrd_standard

# Извлечь стили из документа
python3 scripts/extract_styles.py --doc "DOC_ID"

# Экспортировать стили в Python
python3 scripts/extract_styles.py --doc "DOC_ID" --export .tmp/styles.py

# Создать новый CV с темой (full pipeline)
python3 gdocs_cli.py import-md templates/cv.md --name "New CV"
python3 gdocs_cli.py apply --doc "New CV" --data data/cv.json
python3 scripts/apply_cv_styles_themed.py --doc "New CV" --theme hrd_standard
```

## Примеры использования

### Сценарий 1: Создать CV для консервативной компании

```bash
# HRD Standard тема - минималистичная, черный текст
python3 scripts/apply_cv_styles_themed.py \
  --doc "Stan Sobolev_Finance_2025" \
  --theme hrd_standard
```

### Сценарий 2: Создать CV для стартапа

```bash
# Colorful тема - с акцентами и визуальными элементами
python3 scripts/apply_cv_styles_themed.py \
  --doc "Stan Sobolev_Startup_2025" \
  --theme colorful
```

### Сценарий 3: Применить разные темы к разным секциям

```python
from scripts.themes import hrd_standard, colorful

# Skills - colorful (с синей рамкой)
requests.extend(colorful.apply_skills_section_style(264, 790))

# Experience - hrd_standard (минималистично)
requests.extend(hrd_standard.apply_experience_block_style(790, 1912))

# Применить
docs_batch_update(document_id=doc_id, access_token=token, requests=requests)
```

## Ссылки

- [Quick Start Guide](THEME_QUICK_START.md)
- [Full Documentation](CV_THEME_SYSTEM.md)
- [CV Automation Guide](../CV-AUTO-GUIDE.md)
- [Google Docs API - Format Text](https://developers.google.com/workspace/docs/api/how-tos/format-text)

---

**Создано:** 2026-01-02
**Версия:** 1.0
**Источник:** Извлечено из Stan Sobolev_HRD_2025 (1v6w66RXuq4xVqQM1ZBGuB0siSLS7K3Betk_oHxvxG98)
