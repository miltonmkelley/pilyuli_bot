# Telegram Pill Reminder Bot --- Technical Specification (MVP)

## 1. Overview

Develop a multi-user Telegram bot that:

-   Allows users to add medicines
-   Configure intake schedules
-   Receive reminders
-   Mark doses as taken
-   View today's intake status

No AI. No monetization. No external integrations.

------------------------------------------------------------------------

## 2. Technology Stack

-   Python 3.11+
-   aiogram 3.x
-   APScheduler (AsyncIOScheduler)
-   SQLite (aiosqlite)
-   uv (dependency manager)

Database file: `pill_bot.db`

------------------------------------------------------------------------

## 3. Project Initialization

``` bash
uv init pill_bot
cd pill_bot
uv add aiogram apscheduler aiosqlite python-dotenv
```

### Project Structure

    app/
      bot.py
      config.py
      db.py
      scheduler.py
      keyboards.py
      services/
          medicine_service.py
          dose_service.py
      handlers/
          start.py
          add_medicine.py
          today.py
          callbacks.py
    main.py
    .env

------------------------------------------------------------------------

## 4. Configuration

`.env` file:

    BOT_TOKEN=your_token_here
    TIMEZONE=Europe/Moscow

-   Load via python-dotenv
-   Validate BOT_TOKEN exists
-   Raise error if missing

------------------------------------------------------------------------

## 5. Database Schema

### users

``` sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
```

### medicines

``` sql
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### schedules

``` sql
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);
```

### doses

``` sql
CREATE TABLE IF NOT EXISTS doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    scheduled_datetime TEXT NOT NULL,
    status TEXT NOT NULL,
    taken_at TEXT,
    reminder_sent INTEGER DEFAULT 0,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);
```

------------------------------------------------------------------------

## 6. Business Logic

### 6.1 Daily Dose Generation

Every day at 00:01:

-   For each schedule
-   Create dose if not already created
-   status = "scheduled"

Must avoid duplicates.

------------------------------------------------------------------------

### 6.2 Reminder Processing

Every minute:

Find doses where:

-   status = scheduled
-   scheduled_datetime \<= now
-   reminder_sent = 0

Send reminder message with inline buttons:

-   ✅ Taken
-   ⏰ Snooze (10 minutes)

Then set `reminder_sent = 1`.

------------------------------------------------------------------------

### 6.3 Snooze Logic

When snoozed:

-   scheduled_datetime += 10 minutes
-   reminder_sent = 0

------------------------------------------------------------------------

### 6.4 Auto Missed

If:

-   now \> scheduled_datetime + 2 hours
-   status = scheduled

Then:

-   status = missed

------------------------------------------------------------------------

## 7. Commands

### /start

-   Register user if not exists
-   Send greeting

------------------------------------------------------------------------

### /add

FSM flow:

1.  Enter name
2.  Enter dosage
3.  Enter time (HH:MM or comma-separated)

Validate time format:

Regex: \^(\[01\]`\d|`{=tex}2\[0-3\]):(\[0-5\]`\d)`{=tex}\$

Create medicine and schedule entries.

------------------------------------------------------------------------

### /today

Display today's doses grouped and sorted by time.

Status mapping:

-   taken → ✅
-   missed → ❌
-   future scheduled → ⏳

Example:

    📅 Today:

    ✅ Omeprazole — 08:00 (taken at 08:03)
    ❌ Vitamin D — 09:00 (missed)
    ⏳ Magnesium — 22:00 (not yet)

------------------------------------------------------------------------

## 8. Dose State Machine

Allowed transitions:

scheduled → taken\
scheduled → missed\
scheduled → scheduled (snooze)

Forbidden:

taken → scheduled\
missed → taken

------------------------------------------------------------------------

## 9. Scheduler Jobs

-   00:01 daily → generate_daily_doses
-   Every minute → process_due_reminders
-   Every minute → process_missed_doses

Must not block event loop.

------------------------------------------------------------------------

## 10. Acceptance Criteria

Scenario 1: - User adds medicine - Dose created - Reminder arrives

Scenario 2: - User marks taken - /today shows taken

Scenario 3: - User ignores reminder - After 2 hours → missed

Scenario 4: - User snoozes - Reminder reappears after 10 minutes

------------------------------------------------------------------------

## 11. Non-Functional Requirements

-   Fully async
-   No global mutable state
-   Clean module separation
-   No circular imports
-   Type annotations required
-   Proper error handling
-   Scheduler must not crash on exception

------------------------------------------------------------------------

## 12. Definition of Done

Project is complete when:

-   Runs via `uv run main.py`
-   Multi-user safe
-   No duplicate daily doses
-   All acceptance scenarios pass
