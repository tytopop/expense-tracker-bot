# 💰 Expense Tracker Bot

> [🇷🇺 Русский](#-русский) | [🇬🇧 English](#-english) | [🇨🇳 中文](#-中文)

---

## 🇷🇺 Русский

Telegram-бот для учёта личных расходов по системе **«4 конверта»** с синхронизацией в Notion.

### Возможности

- **Система 4 конвертов** — месячный бюджет делится на 4 недели, каждую неделю свой лимит
- **9 категорий расходов** — еда, транспорт, быт, здоровье, одежда, связь, развлечения, подарки, другое
- **Быстрый ввод** — текстовые команды (`еда 15.5 обед`) и алиасы (`е 15.5`)
- **Inline-кнопки** — полноценное меню без необходимости печатать
- **Учёт доходов** — дополнительные доходы (`+500 премия`) увеличивают конверт недели
- **Notion sync** — автоматическая синхронизация в Notion-базу
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
| `/config` | Текущие настройки |
| `/undo` | Отменить последнюю запись |
| `/help` | Справка |

### Быстрый ввод
```
еда 12.5 обед        — расход 12.5 BYN в категорию «Еда»
е 25                  — то же через алиас
+500 премия           — доход 500 BYN
```

**Алиасы:** `е` (еда), `т` (транспорт), `б` (быт), `з` (здоровье), `о` (одежда), `с` (связь), `р` (развлечения), `д` (другое). Также: `продукты`, `обед`, `метро`, `такси`, `аптека`, `кино` и др.

### Установка
```bash
git clone https://github.com/tytopop/expense-tracker-bot.git
cd expense-tracker-bot
pip install python-dotenv requests
cp .env.example .env
nano .env  # заполни токены
python3 bot.py
```

### Настройка .env
```env
BOT_TOKEN=токен_от_BotFather
NOTION_TOKEN=токен_интеграции_Notion
NOTION_DB=id_базы_данных_Notion
ALLOWED_USER=твой_telegram_user_id
```

`ALLOWED_USER=0` — доступ для всех.

### Systemd (автозапуск)
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
sudo systemctl enable expense-bot && sudo systemctl start expense-bot
```

### Notion

1. Создай [интеграцию Notion](https://www.notion.so/my-integrations)
2. Создай базу данных со свойствами:

| Свойство | Тип |
|----------|-----|
| Комментарий | Title |
| Date | Date |
| Категория | Select |
| Сумма | Number |
| Неделя | Number |

3. Поделись базой с интеграцией
4. Скопируй Database ID в `.env`

### Стек

Python 3 · Telegram Bot API (long polling) · SQLite · Notion API · python-dotenv

---

## 🇬🇧 English

A personal Telegram bot for expense tracking using the **"4 envelopes"** budgeting method with Notion sync.

### Features

- **4 Envelopes system** — monthly budget split into 4 weekly spending limits
- **9 expense categories** with emoji icons and quick text aliases
- **Inline keyboard UI** — full menu navigation without typing commands
- **Income tracking** — extra income increases the weekly envelope
- **Notion integration** — automatic cloud sync of all transactions
- **SQLite storage** — local backup of all data
- **Budget wizard** — step-by-step setup: salary, spouse income, freelance, utilities, up to 3 loans, deposits, reserve %
- **Statistics** — daily, weekly, monthly breakdowns by category
- **Undo** — remove last entry with one tap

### Commands

| Command | Description |
|---------|-------------|
| `/menu` | Main menu with inline buttons |
| `/budget` | Weekly envelope — remaining balance and daily limit |
| `/today` | Today's expenses and income |
| `/week` | Weekly stats by category |
| `/month` | Monthly stats |
| `/setup` | Step-by-step budget configuration |
| `/config` | Current budget settings |
| `/undo` | Undo last entry |
| `/help` | Help |

### Quick Input
```
еда 12.5 lunch        — expense 12.5 BYN in "Food" category
е 25                   — same using alias
+500 bonus             — income 500 BYN
```

### Installation
```bash
git clone https://github.com/tytopop/expense-tracker-bot.git
cd expense-tracker-bot
pip install python-dotenv requests
cp .env.example .env
nano .env  # fill in your tokens
python3 bot.py
```

### .env Configuration
```env
BOT_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_integration_secret
NOTION_DB=your_notion_database_id
ALLOWED_USER=your_telegram_user_id
```

Set `ALLOWED_USER=0` for unrestricted access.

### Systemd (autostart)
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

### Notion Setup

1. Create a [Notion integration](https://www.notion.so/my-integrations)
2. Create a database with properties:

| Property | Type |
|----------|------|
| Комментарий | Title |
| Date | Date |
| Категория | Select |
| Сумма | Number |
| Неделя | Number |

3. Share the database with your integration
4. Copy the Database ID into `.env`

### Tech Stack

Python 3 · Telegram Bot API (long polling) · SQLite · Notion API · python-dotenv

---

## 🇨🇳 中文

基于**"四信封"**预算法的 Telegram 个人记账机器人，支持 Notion 同步。

### 功能特点

- **四信封系统** — 月预算分为4周，每周独立限额
- **9个支出类别** — 餐饮、交通、家居、医疗、服装、通讯、娱乐、礼物、其他
- **快捷输入** — 文字命令和缩写别名快速记账
- **内联按钮** — 完整菜单导航，无需输入命令
- **收入记录** — 额外收入自动增加本周信封额度
- **Notion 同步** — 所有交易自动同步到 Notion 数据库
- **SQLite 备份** — 本地数据备份
- **预算向导** — 分步设置：工资、配偶收入、自由职业、水电费、最多3笔贷款、存款、储备金比例
- **统计报表** — 按日、周、月分类统计
- **撤销操作** — 一键删除最后一笔记录

### 命令列表

| 命令 | 说明 |
|------|------|
| `/menu` | 主菜单（内联按钮） |
| `/budget` | 本周信封 — 余额和每日限额 |
| `/today` | 今日收支 |
| `/week` | 本周按类别统计 |
| `/month` | 本月统计 |
| `/setup` | 分步预算设置 |
| `/config` | 当前预算配置 |
| `/undo` | 撤销上一笔 |
| `/help` | 帮助 |

### 快捷记账
```
еда 12.5 午餐         — 记录12.5 BYN到"餐饮"类别
е 25                   — 使用缩写别名
+500 奖金              — 记录收入500 BYN
```

### 安装部署
```bash
git clone https://github.com/tytopop/expense-tracker-bot.git
cd expense-tracker-bot
pip install python-dotenv requests
cp .env.example .env
nano .env  # 填写你的令牌
python3 bot.py
```

### .env 配置
```env
BOT_TOKEN=你的Telegram机器人令牌
NOTION_TOKEN=你的Notion集成令牌
NOTION_DB=你的Notion数据库ID
ALLOWED_USER=你的Telegram用户ID
```

设置 `ALLOWED_USER=0` 允许所有人访问。

### Notion 配置

1. 创建 [Notion 集成](https://www.notion.so/my-integrations)
2. 创建数据库，包含以下属性：

| 属性 | 类型 |
|------|------|
| Комментарий | Title |
| Date | Date |
| Категория | Select |
| Сумма | Number |
| Неделя | Number |

3. 将数据库共享给集成
4. 将数据库ID复制到 `.env`

### 技术栈

Python 3 · Telegram Bot API（长轮询）· SQLite · Notion API · python-dotenv

---

## 📄 License

MIT

## 👤 Author

**tytopop** — [GitHub](https://github.com/tytopop)
