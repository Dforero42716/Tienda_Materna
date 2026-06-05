# Fresh Clone Setup

Use this guide when someone clones the repo on a new computer and wants to run the Mundo Materno Telegram inventory bot.

## 1. Install Required Software

Install these first:

```text
Git
Python 3.11+
Node.js
npm
OpenClaw
```

Install OpenClaw with npm:

```powershell
npm install -g openclaw
```

Confirm the commands work:

```powershell
git --version
python --version
node --version
npm --version
openclaw --version
```

## 2. Clone The Repo

```powershell
git clone https://github.com/Dforero42716/Tienda_Materna.git
cd Tienda_Materna
```

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

If the computer uses `py` instead of `python`, this is also fine:

```powershell
py -m pip install -r requirements.txt
```

## 4. Create `.env`

The real `.env` file is private and is not committed to GitHub.

Create it from the example:

```powershell
copy .env.example .env
notepad .env
```

Minimum required values:

```env
TELEGRAM_BOT_TOKEN=your_botfather_token
MUNDO_MATERNO_ALLOW_MUTATIONS=0
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Keep this value at `0` if the bot is public:

```env
MUNDO_MATERNO_ALLOW_MUTATIONS=0
```

Set it to `1` only if trusted users are allowed to run commands that change inventory, sales, or the day status.

Choose one database option in `.env`.

Option A, SQLite:

```env
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Option B, PostgreSQL:

```env
MUNDO_MATERNO_DB_ENGINE=postgres
DATABASE_URL=postgresql://user:password@localhost:5432/mundo_materno
```

## 5. Configure OpenClaw

OpenClaw is mandatory for this project. The app will not answer if OpenClaw is missing or stopped. Telegram messages are delegated to `openclaw agent`, and the `mundo-materno-inventory` skill calls the local Python bridge for inventory execution.

Check OpenClaw:

```powershell
openclaw --version
openclaw config validate
openclaw skills list --eligible
```

The skills list must include:

```text
mundo-materno-inventory
```

The project includes the skill files here:

```text
openclaw/mundo-materno-inventory/SKILL.md
skills/mundo-materno-inventory/SKILL.md
```

If OpenClaw does not see the skill, update the local OpenClaw config so its workspace points to this cloned repo.

## 6. Initialize The Database

Choose one path.

### Option A: SQLite

SQLite is the easiest local option. It stores data in `inventario.db`.

In `.env`:

```env
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Initialize it:

```powershell
python database.py
```

This creates or repairs:

```text
inventario.db
```

### Option B: PostgreSQL

PostgreSQL is better for a server, shared use, or future deployment.

Install the optional driver:

```powershell
pip install "psycopg[binary]"
```

Then set in `.env`:

```env
MUNDO_MATERNO_DB_ENGINE=postgres
DATABASE_URL=postgresql://user:password@localhost:5432/mundo_materno
```

Create the schema:

```powershell
python database.py
```

Optional SQLite-to-PostgreSQL migration:

```powershell
python scripts/migrate_sqlite_to_postgres.py --truncate
```

## 7. Run The Project

Open terminal 1 and start OpenClaw:

```powershell
openclaw gateway run
```

Leave terminal 1 open.

Open terminal 2 and start the Telegram bot:

```powershell
cd Tienda_Materna
python telegram_inventory_bot.py
```

The bot starts only if OpenClaw is ready. Each Telegram message is then routed through OpenClaw before any inventory command is executed.

## 8. Test In Telegram

Message the bot:

```text
/start
```

Then try:

```text
cuantos productos hay
ventas de hoy
productos en talla M
producto mas vendido
alertas de reposicion
```

## 9. Logs

Bot logs are written here:

```text
logs/telegram_bot.log
```

Watch the log live:

```powershell
Get-Content logs\telegram_bot.log -Wait
```

## Important Notes

- Rotate any Telegram or API key that was pasted into chat or exposed by accident.
- Never commit `.env`.
- Do not run OpenClaw's Telegram channel and `telegram_inventory_bot.py` with the same bot token at the same time.
- Back up `inventario.db` before migrating to PostgreSQL.
