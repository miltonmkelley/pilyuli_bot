# 💊 Pill Reminder Bot

Telegram-бот для напоминаний о приёме лекарств.

## Возможности

- Добавление лекарств с расписанием приёма
- Автоматические напоминания в назначенное время
- Отметка о приёме или отложение на 10 минут
- Просмотр расписания на сегодня
- Автоматическая пометка пропущенных приёмов (через 2 часа)

## Установка

```bash
uv sync
```

## Настройка

Создайте файл `.env` на основе `.env.example`:

```
BOT_TOKEN=your_telegram_bot_token
TIMEZONE=Europe/Moscow
```

## Запуск

### Локально
```bash
uv run main.py
```

### Через Docker Compose
Убедитесь, что у вас установлен Docker и docker-compose.
Запуск в фоновом режиме:
```bash
docker-compose up -d
```

Логи бота:
```bash
docker-compose logs -f bot
```

Перезапуск бота (например, после обновления кода):
```bash
docker-compose restart bot
```
или полная пересборка и перезапуск:
```bash
docker-compose up -d --build
```

Остановка бота:
```bash
docker-compose down
```

## Команды бота

| Команда   | Описание                          |
|-----------|-----------------------------------|
| `/start`    | Регистрация и приветствие               |
| `/add`      | Добавить лекарство (FSM-диалог)         |
| `/today`    | Расписание на сегодня                   |
| `/settings` | Настройки уведомлений (кол-во, интервал)|

## Тесты

```bash
uv run pytest tests/ -v
```

## Структура проекта

```
app/
  bot.py              # Bot и Dispatcher factory
  config.py           # Загрузка конфигурации из .env
  db.py               # SQLite схема и подключение
  keyboards.py        # Inline-клавиатуры
  scheduler.py        # APScheduler задачи
  handlers/
    start.py          # /start
    add_medicine.py   # /add (FSM)
    today.py          # /today
    settings.py       # /settings (FSM)
    callbacks.py      # Обработка inline-кнопок
  services/
    medicine_service.py  # Логика лекарств
    dose_service.py      # Логика доз и напоминаний
main.py               # Точка входа
tests/                 # Юнит-тесты
```
