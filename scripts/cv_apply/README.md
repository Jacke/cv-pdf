# CV Apply Package

Модульная система для применения структурированных CV данных к шаблонам Google Docs.

## Структура модулей

### `constants.py`
Константы, используемые в системе:
- Маркеры буллетов для разных секций
- Регулярные выражения для обнаружения URL, email, телефонов
- Заголовки секций и ландмарки блоков
- OAuth scope'ы для Google Docs API

### `utils.py`
Вспомогательные функции общего назначения:
- Чтение/запись JSON файлов
- Нормализация текста и списков
- Логирование с таймстампами
- Извлечение плейсхолдеров

### `formatters.py`
Форматирование секций CV:
- `format_summary()` - форматирование резюме
- `format_skills()` - форматирование навыков
- `format_experiences()` - форматирование опыта работы (разделяет обычный опыт и предпринимательство)
- `format_education()` - форматирование образования
- `format_publications()` - форматирование публикаций
- `build_replacements()` - построение полного словаря замен

### `document.py`
Операции с документами:
- Парсинг ссылок на Google Docs
- Извлечение ID документа из URL
- Итерация по параграфам документа
- Поиск секций по заголовкам
- Создание запросов для создания ссылок (auto-linkify)

### `styling.py`
Стилизация документов:
- `style_skills_section()` - стилизация секции навыков
- `style_experience_section()` - стилизация секций опыта
- `apply_block_styles()` - применение всех стилей к документу

### `state.py`
Управление состоянием:
- Чтение/запись файла состояния
- Обновление состояния после применения
- Инвертирование словаря замен для reset операций

### `cli.py`
CLI утилиты для взаимодействия с gdocs_cli:
- `apply_with_auto_auth()` - применение замен с авто-реаутентификацией
- `get_doc_text()` - получение текста документа
- `needs_reauth()` - проверка необходимости повторной аутентификации

### `reset.py`
Операции сброса документа:
- `reset_document()` - сброс документа к плейсхолдерам

## Использование

### Основной скрипт

```bash
# Применить CV данные к документу
./cv_structured_apply_refactored.py --data data/cv.json --doc "CV Template"

# Только сгенерировать JSON с заменами
./cv_structured_apply_refactored.py --data data/cv.json --out replacements.json

# Сбросить документ к плейсхолдерам
./cv_structured_apply_refactored.py --reset --doc "CV Template"

# Dry run (без изменения документа)
./cv_structured_apply_refactored.py --data data/cv.json --doc "CV Template" --dry-run
```

### Программное использование

```python
from cv_apply.formatters import build_replacements
from cv_apply.utils import read_json

# Загрузить и отформатировать CV данные
data = read_json("data/cv.json")
replacements = build_replacements(data)

# Использовать отдельные форматтеры
from cv_apply.formatters import format_skills, format_experiences

skills = format_skills(data)
exps, entrepreneurship = format_experiences(data)
```

## Преимущества рефакторинга

1. **Модульность**: Каждый модуль отвечает за конкретную функциональность
2. **Переиспользуемость**: Функции можно использовать независимо
3. **Тестируемость**: Легко писать unit-тесты для каждого модуля
4. **Читаемость**: Код разбит на логические блоки
5. **Поддерживаемость**: Легче находить и исправлять баги
6. **Документированность**: Каждая функция имеет docstring

## Миграция

Старый скрипт `cv_structured_apply.py` остается без изменений для обратной совместимости.
Новый рефакторенный скрипт доступен как `cv_structured_apply_refactored.py`.

После тестирования можно заменить старый скрипт новым:
```bash
mv scripts/cv_structured_apply.py scripts/cv_structured_apply_old.py
mv scripts/cv_structured_apply_refactored.py scripts/cv_structured_apply.py
```
