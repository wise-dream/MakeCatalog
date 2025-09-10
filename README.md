# MakeCatalog

**MakeCatalog** — это система для автоматической генерации профессиональных каталогов продукции в форматах HTML и PDF на основе структурированных данных в JSON формате.

## Назначение программы

Программа предназначена для создания печатных и электронных каталогов продукции со следующими возможностями:

- **Автоматическая генерация** каталогов из структурированных данных
- **Профессиональное оформление** с поддержкой брендинга компании
- **Многоформатный вывод**: HTML для веб-просмотра и PDF для печати
- **Гибкая структура** с разделами, сериями и моделями продукции
- **Технические характеристики** в виде таблиц и графиков
- **Автоматическое оглавление** с навигацией
- **Адаптивная верстка** для различных устройств

## Установка и настройка

### Требования

- Python 3.8+
- Зависимости из `requirements.txt`

### Установка зависимостей

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка браузеров для Chromium (требуется для PDF генерации)
playwright install chromium
```

### Структура проекта

```
MakeCatalog/
├── cli.py                 # Основной интерфейс командной строки
├── catalog.json          # Пример входного файла с данными
├── requirements.txt      # Зависимости Python
├── core/                 # Основная логика
│   ├── models.py        # Модели данных
│   ├── json_loader.py   # Загрузка JSON
│   ├── render.py        # Рендеринг шаблонов
│   ├── export.py        # Экспорт в PDF
│   └── utils.py         # Утилиты
├── stages/              # Этапы генерации
│   ├── cover.py         # Обложка
│   ├── toc.py           # Оглавление
│   ├── products.py      # Продукты
│   ├── backcover.py     # Задняя обложка
│   └── ...
├── templates/           # HTML шаблоны
│   ├── base.html.j2     # Базовый шаблон
│   ├── cover.html.j2    # Шаблон обложки
│   ├── products.html.j2 # Шаблон продуктов
│   └── ...
└── output/              # Выходные файлы
    └── images/          # Изображения и ассеты
```

## Использование

### Базовое использование

```bash
python cli.py catalog.json
```

Эта команда создаст:
- `output/catalog.html` — HTML версия каталога
- `output/catalog.pdf` — PDF версия каталога

### Расширенные параметры

```bash
python cli.py catalog.json \
  --out-html output/my_catalog.html \
  --out-pdf output/my_catalog.pdf \
  --templates custom_templates \
  --engine chromium \
  --no-cover
```

#### Параметры командной строки:

- `json` — путь к JSON файлу с данными каталога (обязательный)
- `--out-html` — путь для HTML вывода (по умолчанию: `output/catalog.html`)
- `--out-pdf` — путь для PDF вывода (по умолчанию: `output/catalog.pdf`)
- `--templates` — папка с шаблонами (по умолчанию: `templates`)
- `--engine` — движок для PDF: `chromium` (по умолчанию) или `weasyprint`
- `--no-cover` — не добавлять обложку и заднюю обложку

### Движки PDF генерации

1. **Chromium** (рекомендуется) — использует Playwright + Paged.js
   - Поддержка сложной верстки
   - Корректные переносы страниц
   - Полная поддержка CSS
   - Автоматическая нумерация страниц

2. **WeasyPrint** — альтернативный движок
   - Быстрее для простых документов
   - Меньше зависимостей

## Ассеты и изображения

### Размещение файлов

Все изображения и ассеты должны быть размещены в папке **`output/images/`**:

```
output/
├── catalog.html
├── catalog.pdf
└── images/              # ← Все изображения здесь
    ├── cover_bg.jpg     # Фон обложки
    ├── artek.svg        # Логотип компании
    ├── ROUND.jpg        # Фон раздела "ROUND"
    ├── SDCXL.png        # Фото серии SDCXL
    ├── model1.jpg       # Фото модели
    └── ...
```

### Поддерживаемые форматы

- **Изображения**: JPG, PNG, SVG, WebP
- **Документы**: PDF (для вложений)
- **Видео**: MP4, WebM (для веб-версии)

### Пути в JSON

В JSON файле указывайте пути относительно папки `output/images/`:

```json
{
  "settings": {
    "cover_bg": "images/cover_bg.jpg",
    "cover_logo": "images/artek.svg"
  },
  "sections": [{
    "series": [{
      "hero": {
        "photo": "images/SDCXL.png"
      }
    }]
  }]
}
```

## Формат входного JSON

### Структура каталога

```json
{
  "settings": {
    "year": "2025",
    "title": "Вентиляционный каталог",
    "theme_color": "#E53935",
    "currency": "₸",
    "cover_bg": "images/cover_bg.jpg",
    "cover_logo": "images/artek.svg",
    "company": {
      "name": "ТОО «ARTEK»",
      "address": "Алматы, ул. Аптечная 37а",
      "contacts": "+7 700 000 00 00, info@artek.kz"
    }
  },
  "sections": [
    {
      "code": "ROUND",
      "title": "ВЕНТИЛЯЦИОННОЕ ОБОРУДОВАНИЕ ДЛЯ КРУГЛЫХ КАНАЛОВ",
      "intro_md": "Описание раздела в **Markdown**",
      "series": [
        {
          "code": "SDCXL",
          "name": "Круглые канальные вентиляторы SDC XL",
          "summary_md": "Описание серии",
          "hero": {
            "photo": "images/SDCXL.png"
          },
          "tables": [
            {
              "type": "technical",
              "title": "Технические характеристики",
              "columns": [
                {"key": "model", "title": "Модель"},
                {"key": "power", "title": "Мощность, Вт"}
              ],
              "rows": [
                {"model": "SDCXL-100", "power": "25"},
                {"model": "SDCXL-125", "power": "30"}
              ]
            }
          ],
          "models": [
            {
              "sku": "SDCXL-100",
              "name": "Вентилятор SDCXL-100",
              "price": 15000,
              "image": "images/model1.jpg",
              "description_md": "Описание модели"
            }
          ]
        }
      ]
    }
  ]
}
```

### Основные элементы

#### Settings (настройки)
- `year` — год каталога
- `title` — название каталога
- `theme_color` — основной цвет темы
- `currency` — валюта
- `cover_bg` — фон обложки
- `cover_logo` — логотип на обложке
- `company` — информация о компании

#### Sections (разделы)
- `code` — код раздела
- `title` — название раздела
- `intro_md` — описание раздела (Markdown)
- `series` — список серий в разделе

#### Series (серии)
- `code` — код серии
- `name` — название серии
- `summary_md` — краткое описание
- `hero.photo` — главное фото серии
- `tables` — таблицы характеристик
- `models` — модели в серии

#### Models (модели)
- `sku` — артикул
- `name` — название модели
- `price` — цена
- `image` — фото модели
- `description_md` — описание (Markdown)

## Выходные форматы

### HTML
- Полнофункциональная веб-версия каталога
- Адаптивная верстка
- Интерактивные элементы
- Навигация по разделам

### PDF
- Оптимизирован для печати формата A4
- Автоматическая нумерация страниц
- Корректные переносы страниц
- Высокое качество изображений

## Примеры использования

### Создание каталога вентиляционного оборудования

```bash
# Базовое создание каталога
python cli.py catalog.json

# Создание каталога без обложки
python cli.py catalog.json --no-cover

# Использование кастомных шаблонов
python cli.py catalog.json --templates my_templates

# Только HTML без PDF
python cli.py catalog.json --out-pdf ""
```

### Автоматизация в скриптах

```bash
#!/bin/bash
# Скрипт для регулярного обновления каталога

# Обновление данных
python update_catalog_data.py

# Генерация каталога
python cli.py catalog.json \
  --out-html output/catalog_$(date +%Y%m%d).html \
  --out-pdf output/catalog_$(date +%Y%m%d).pdf

echo "Каталог обновлен: $(date)"
```

## Поддержка и развитие

Программа активно развивается и поддерживает:

- Расширение функциональности через кастомные шаблоны
- Добавление новых типов контента
- Интеграцию с внешними системами
- Автоматизацию процессов генерации

Для получения помощи или предложений по улучшению создайте issue в репозитории проекта.
