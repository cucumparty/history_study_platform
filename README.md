# Хроники России 📜

Учебный веб-проект по истории России — образовательный тренажёр для взрослых.

## О проекте

Многие взрослые хотят знать историю своей страны лучше, но традиционные учебники
кажутся скучными. Этот проект создан для тех, кто хочет учиться в своём темпе,
без давления и экзаменов. 

## Что реализовано

| Раздел | URL | Описание |
|---|---|---|
| Главная | `/` | Обзор эпох, избранные факты |
| О проекте | `/about/` | Описание проекта |
| Лекции | `/lectures/` | Список лекций по эпохам |
| Лекция | `/lectures/<slug>/` | Полный текст + боковая панель с датами |
| Тест | `/lectures/<slug>/test/` | Тест после лекции с разбором ответов |
| Карточки | `/cards/` | Flip-карточки с фильтром по эпохам, форма создания |
| Тренировка | `/cards/train/` | Anki-режим: знаю / повторить |
| Квиз | `/quiz/` | Настройки квиза (эпоха + количество вопросов) |
| Игра | `/quiz/play/` | Квиз с навигацией и разбором ответов |
| Факты | `/facts/` | Интересные исторические факты |
| Таймлайн | `/timeline/` | Параллельный таймлайн Россия vs мир |


## Технологии

- **Python 3.10+** / **Django 5.x**
- **SQLite** — база данных
- **HTML + CSS + JS** — без сторонних frontend-фреймворков

## Как запустить

```bash
# 1. Клонировать репозиторий
git clone <url>
cd historyapp

# 2. Виртуальное окружение
python -m venv venv
source venv/bin/activate      # Linux / macOS
# или
venv\Scripts\activate         # Windows

# 3. Зависимости
pip install -r requirements.txt

# 4. Миграции и тестовые данные
python manage.py migrate
python manage.py seed_data

# 5. Создать суперпользователя (для /admin/)
python manage.py createsuperuser

# 6. Запуск
python manage.py runserver
```

Открыть в браузере: **http://127.0.0.1:8000/**

Панель администратора: **http://127.0.0.1:8000/admin/**

## Структура проекта

```
historyapp/
├── core/
│   ├── management/commands/
│   │   └── seed_data.py        # Тестовые данные
│   ├── migrations/
│   ├── templatetags/
│   │   └── core_extras.py      # Кастомный фильтр get_item
│   ├── admin.py
│   ├── forms.py                # 3 формы с валидацией
│   ├── models.py               # 6 моделей
│   ├── urls.py
│   └── views.py
├── historyapp/
│   ├── settings.py
│   └── urls.py
├── templates/
│   ├── base.html               # Базовый шаблон с навигацией
│   └── core/                   # 11 шаблонов страниц
├── static/
│   ├── css/main.css            # ~600 строк CSS
│   └── js/main.js
├── .pylintrc
├── requirements.txt
└── README.md
```
