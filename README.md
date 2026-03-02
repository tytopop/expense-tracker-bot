# 💰 Expense Tracker Bot

Telegram-бот для учёта расходов по системе «4 конверта» с синхронизацией в Notion.

**Telegram bot for personal expense tracking using the "4 envelopes" budgeting method with Notion sync.**

---

## 🇷🇺 Описание

Бот помогает контролировать личные финансы: считает недельный бюджет на основе доходов и обязательных расходов, отслеживает траты по категориям и синхронизирует данные в Notion.

### Возможности

- **Система 4 конвертов** — месячный бюджет делится на 4 недели, каждую неделю свой лимит
- **9 категорий расходов** — еда, транспорт, быт, здоровье, одежда, связь, развлечения, подарки, другое
- **Быстрый ввод** — текстовые команды (`еда 15.5 обед`) и алиасы (`е 15.5`)
- **Inline-кнопки** — полноценное меню без необходимости печатать команды
- **Учёт доходов** — дополнительные доходы (`+500 премия`) увеличивают конверт недели
- **Notion sync** — расходы и доходы автоматически отправляются в Notion-базу
- **SQLite backup** — все данные дублируются локально
- **Настройка бюджета** — пошаговый мастер: зарплата, кредиты, депозиты, коммуналка, резерв
- **Статистика** — за день, неделю, месяц с разбивкой по категориям
- **Отмена** — последняя запись удаляется одной кнопкой

### Команды

| Команда | Описание |
|---------|----------|
| `/menu` | Главное меню с inline-кнопками |
| `/budget` | Конверт недели — остаток и лимит в день |
| `/today` | Расходы и доходы за сегодня |
| `/week` | Статистика за неделю по категориям |
| `/month` | Статистика за месяц |
| `/setup` | Пошаговая настройка бюджета |
| `/config` | Текущие настройки бюджета |
| `/undo` | Отменить последнюю запись |
| `/help` | Справка |

### Быстрый ввод

```
еда 12.5 обед        — расход 12.5 BYN в категорию "Еда"
е 25                  — то же самое через алиас
+500 премия           — доход 500 BYN
```

**Алиасы категорий:** `е` (еда), `т` (транспорт), `б` (быт), `з` (здоровье), `о` (одежда), `с` (связь), `р` (развлечения), `д` (другое). Также работают слова: `продукты`, `обед`, `метро`, `такси`, `аптека`, `кино` и другие.

---

## 🇬🇧 Description

A personal Telegram bot for expense tracking using the "4 envelopes" budgeting system. The bot calculates a weekly spending limit based on income, fixed costs, loan payments, savings, and a reserve percentage. All transactions sync to a Notion database with local SQLite backup.

### Features

- **4 Envelopes system** — monthly budget split into 4 weekly limits
- **9 expense categories** with emoji icons and text aliases for quick input
- **Inline keyboard UI** — full menu navigation without typing commands
- **Income tracking** — extra income increases the weekly envelope
- **Notion integration** — automatic sync of all transactions
- **SQLite storage** — local backup of all data
- **Budget wizard** — step-by-step setup: salary, spouse income, freelance, utilities, up to 3 loans, deposits, reserve %
- **Statistics** — daily, weekly, monthly breakdowns by category
- **Undo** — remove last entry with one tap

---

## ⚙️ Installation

### Requirements

- Python 3.10+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Notion Integration Token + Database ID (optional)

### Setup

```bash
# Clone
git clone https://github.com/tytopop/expense-tracker-bot.git
cd expense-tracker-bot

# Install dependencies
pip install python-dotenv requests

# Configure
cp .env.example .env
nano .env  # fill in your tokens
```

### .env file

```env
BOT_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_internal_integration_secret
NOTION_DB=your_notion_database_id
ALLOWED_USER=your_telegram_user_id
```

`ALLOWED_USER` — your Telegram user ID to restrict access. Set `0` to allow anyone.

### Run

```bash
python3 bot.py
```

### Systemd service (optional)

```bash
sudo nano /etc/systemd/system/expense-bot.service
```

```ini
[Unit]
Description=Expense Tracker Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/expense-bot
ExecStart=/usr/bin/python3 /opt/expense-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable expense-bot
sudo systemctl start expense-bot
```

---

## 📊 Notion Setup

1. Create a [Notion integration](https://www.notion.so/my-integrations)
2. Create a database with these properties:

| Property | Type |
|----------|------|
| Комментарий | Title |
| Date | Date |
| Категория | Select |
| Сумма | Number |
| Неделя | Number |

3. Share the database with your integration
4. Copy the database ID into `.env`

---

## 🛠 Tech Stack

- **Python 3** — single file, no frameworks
- **Telegram Bot API** — long polling via `requests`
- **SQLite** — local storage
- **Notion API** — cloud sync
- **python-dotenv** — environment configuration

---

## 📄 License

MIT

---

## 👤 Author

**tytopop** — [GitHub](https://github.com/tytopop)
