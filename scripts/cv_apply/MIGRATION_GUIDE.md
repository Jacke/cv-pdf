# Migration Guide: cv_structured_apply.py → Refactored Version

## Быстрый старт

### Шаг 1: Тестирование нового скрипта

```bash
# Сравните вывод старого и нового скрипта
./scripts/cv_structured_apply.py --data data/cv.json --dry-run > old_output.txt
./scripts/cv_structured_apply_refactored.py --data data/cv.json --dry-run > new_output.txt

# Убедитесь, что выводы идентичны (или приемлемо похожи)
diff old_output.txt new_output.txt
```

### Шаг 2: Тестирование на реальных документах

```bash
# Сделайте резервную копию документа в Google Docs
# Затем протестируйте новый скрипт

./scripts/cv_structured_apply_refactored.py \
  --data data/cv.json \
  --doc "Test Resume" \
  --dry-run

# Если все хорошо, примените изменения
./scripts/cv_structured_apply_refactored.py \
  --data data/cv.json \
  --doc "Test Resume"
```

### Шаг 3: Финальная миграция

```bash
# Сохраните старую версию
mv scripts/cv_structured_apply.py scripts/cv_structured_apply_legacy.py

# Используйте новую версию как основную
cp scripts/cv_structured_apply_refactored.py scripts/cv_structured_apply.py
```

## Изменения в API

### Без изменений

Все команды работают точно так же:

```bash
# Старая версия
./cv_structured_apply.py --data cv.json --doc "Resume"

# Новая версия - ИДЕНТИЧНО
./cv_structured_apply_refactored.py --data cv.json --doc "Resume"
```

Все параметры сохранены:
- `--data` - путь к CV JSON
- `--doc` - имя документа
- `--out` - путь для сохранения JSON
- `--reset` - сброс документа
- `--dry-run` - тестовый запуск
- `--match-case` - учет регистра
- `--auto-auth` - автоматическая авторизация
- И все остальные параметры

### Внутренние изменения

Если вы импортировали функции из старого скрипта:

```python
# СТАРЫЙ КОД
from cv_structured_apply import format_summary, build_replacements

# НОВЫЙ КОД
from cv_apply.formatters import format_summary, build_replacements
```

## Программное использование

### Старый способ (монолитный)

```python
import sys
sys.path.insert(0, "scripts")
from cv_structured_apply import (
    build_replacements,
    format_summary,
    apply_block_styles
)

data = read_json("cv.json")
replacements = build_replacements(data)
```

### Новый способ (модульный)

```python
import sys
sys.path.insert(0, "scripts")

from cv_apply.formatters import build_replacements, format_summary
from cv_apply.styling import apply_block_styles
from cv_apply.utils import read_json

data = read_json("cv.json")
replacements = build_replacements(data)
```

## Преимущества миграции

### 1. Лучшая читаемость

**Было:**
```python
# Все в одном файле, сложно найти нужную функцию
def format_summary(...): ...  # строка 73
def apply_block_styles(...): ... # строка 295
def format_skills(...): ... # строка 88
```

**Стало:**
```python
# Логичная структура
from cv_apply.formatters import format_summary, format_skills
from cv_apply.styling import apply_block_styles
```

### 2. Легче тестировать

**Было:**
```python
# Сложно тестировать из-за зависимостей
def test_format_summary():
    # Нужно импортировать весь монолитный файл
    from cv_structured_apply import format_summary
    # Много побочных эффектов при импорте
```

**Стало:**
```python
# Чистое тестирование
def test_format_summary():
    from cv_apply.formatters import format_summary
    # Минимальные зависимости
    assert format_summary({"summary": "Test"}) == "Test"
```

### 3. Переиспользование кода

**Было:**
```python
# Если хотите использовать только форматирование,
# приходится импортировать весь файл с ~1500 строк
from cv_structured_apply import format_summary
```

**Стало:**
```python
# Импортируйте только то, что нужно
from cv_apply.formatters import format_summary  # ~230 строк
```

### 4. Независимое развитие модулей

```python
# Можно менять стилизацию, не трогая форматирование
from cv_apply.styling import apply_block_styles

# Или добавлять новые форматтеры
from cv_apply.formatters import format_certifications
```

## Обратная совместимость

### Что сохранено

✅ Все параметры командной строки
✅ Формат входных данных (CV JSON)
✅ Формат выходных данных
✅ Файл состояния (`.cv_apply_state.json`)
✅ Поведение при ошибках
✅ Логирование и вывод

### Что изменилось

⚠️ Импорты (если используете как библиотеку)
⚠️ Внутренняя структура (но это не влияет на внешний API)

### Миграция импортов

```python
# mapping.py - для помощи в миграции
OLD_TO_NEW = {
    "cv_structured_apply.format_summary": "cv_apply.formatters.format_summary",
    "cv_structured_apply.format_skills": "cv_apply.formatters.format_skills",
    "cv_structured_apply.format_experiences": "cv_apply.formatters.format_experiences",
    "cv_structured_apply.format_education": "cv_apply.formatters.format_education",
    "cv_structured_apply.format_publications": "cv_apply.formatters.format_publications",
    "cv_structured_apply.build_replacements": "cv_apply.formatters.build_replacements",
    "cv_structured_apply.apply_block_styles": "cv_apply.styling.apply_block_styles",
    "cv_structured_apply.find_doc_info": "cv_apply.document.find_doc_info",
    "cv_structured_apply.read_json": "cv_apply.utils.read_json",
    "cv_structured_apply.write_json": "cv_apply.utils.write_json",
    "cv_structured_apply.log_line": "cv_apply.utils.log_line",
}
```

## Частые вопросы

### Q: Нужно ли менять мои CV JSON файлы?

**A:** Нет, формат данных остался прежним.

### Q: Работает ли новая версия с моими существующими документами?

**A:** Да, полностью совместима.

### Q: Будет ли работать файл состояния `.cv_apply_state.json`?

**A:** Да, формат файла состояния не изменился.

### Q: Могу ли я использовать оба скрипта параллельно?

**A:** Да, они могут работать параллельно без конфликтов.

### Q: Что если я найду баг в новой версии?

**A:** Вернитесь к старой версии (`cv_structured_apply_legacy.py`) и создайте issue.

### Q: Нужно ли переучиваться?

**A:** Нет, если вы используете CLI. Если программируете - нужно обновить импорты.

### Q: Работает ли reset функция?

**A:** Да, `--reset` работает идентично.

### Q: Улучшилась ли производительность?

**A:** Производительность осталась прежней (разница <100ms при запуске).

## План постепенной миграции

### Неделя 1: Тестирование
```bash
# Используйте новую версию для тестов
alias cv_apply_new='./scripts/cv_structured_apply_refactored.py'
cv_apply_new --data cv.json --doc "Test" --dry-run
```

### Неделя 2: Параллельное использование
```bash
# Используйте обе версии
./scripts/cv_structured_apply.py --data cv.json --doc "Production"
./scripts/cv_structured_apply_refactored.py --data cv.json --doc "Staging"
```

### Неделя 3: Переход на новую версию
```bash
# Начните использовать новую версию по умолчанию
alias cv_apply='./scripts/cv_structured_apply_refactored.py'
```

### Неделя 4: Финальная миграция
```bash
# Замените старый скрипт
mv scripts/cv_structured_apply.py scripts/cv_structured_apply_legacy.py
cp scripts/cv_structured_apply_refactored.py scripts/cv_structured_apply.py
```

## Откат (Rollback)

Если что-то пошло не так:

```bash
# Быстрый откат
mv scripts/cv_structured_apply_legacy.py scripts/cv_structured_apply.py

# Или используйте git
git checkout scripts/cv_structured_apply.py
```

## Поддержка

- **Документация**: См. `cv_apply/README.md`
- **Архитектура**: См. `cv_apply/ARCHITECTURE.md`
- **Тесты**: Запустите `python scripts/cv_apply/test_formatters.py`
- **Issues**: Создайте issue в репозитории

## Чек-лист миграции

- [ ] Прочитал документацию
- [ ] Запустил тесты (`test_formatters.py`)
- [ ] Протестировал на тестовом документе
- [ ] Сравнил вывод старой и новой версии
- [ ] Создал резервную копию важных документов
- [ ] Протестировал `--reset` функцию
- [ ] Обновил импорты в своих скриптах (если есть)
- [ ] Проверил работу в production
- [ ] Сохранил старую версию как `_legacy`
- [ ] Обновил документацию проекта

## Заключение

Миграция безопасна и обратима. Новая версия полностью совместима по API, но предоставляет лучшую структуру кода для будущего развития.

**Рекомендуемая стратегия**: Постепенный переход с параллельным использованием обеих версий в течение 2-4 недель.
