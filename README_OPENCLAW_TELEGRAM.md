# Mundo Materno Telegram Bot With Required OpenClaw

OpenClaw is now mandatory for this project. If OpenClaw is not installed, its config is invalid, the `mundo-materno-inventory` skill is missing, or the gateway is not running, the inventory program refuses to answer.

The Telegram messages are still handled by `telegram_inventory_bot.py`, but every inventory request goes through the OpenClaw readiness gate before `main.preguntar()` runs.

## 1. Configure `.env`

From the project folder:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
notepad .env
```

Set at least:

```env
TELEGRAM_BOT_TOKEN=your_botfather_token
MUNDO_MATERNO_ALLOW_MUTATIONS=0
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Keep this value at `0` while the bot is public:

```env
MUNDO_MATERNO_ALLOW_MUTATIONS=0
```

That lets users ask inventory questions, but blocks commands that change data, like sales, stock updates, `iniciar dia`, and `cerrar dia`.

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

## 2. Check OpenClaw

Run these from any PowerShell terminal:

```powershell
openclaw --version
openclaw config validate
openclaw skills list --eligible
```

The skills list must include:

```text
mundo-materno-inventory
```

If `openclaw` is not recognized, install it first:

```powershell
npm install -g openclaw
```

## 3. Start OpenClaw

Start the gateway before starting the bot:

```powershell
openclaw gateway run
```

Leave that terminal open. The current project expects the gateway to listen locally, usually on:

```text
127.0.0.1:30000
```

Check status in another terminal:

```powershell
openclaw gateway status
```

Important: if OpenClaw is configured with its own Telegram channel using the same bot token, do not run both Telegram pollers at the same time. For this setup, OpenClaw should be running as the required gateway, while `telegram_inventory_bot.py` handles Telegram.

## 4. Start The Telegram Bot

Open a second PowerShell terminal:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
python telegram_inventory_bot.py
```

The bot starts only if OpenClaw passes all checks. If OpenClaw is stopped later, the bot replies with an OpenClaw error instead of answering inventory commands.

Start it hidden/background from PowerShell:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
Start-Process -FilePath python -ArgumentList "telegram_inventory_bot.py" -WorkingDirectory "D:\Coding\GestInvMundoMaterno\Tienda_Materna" -WindowStyle Hidden
```

## 5. Use It In Telegram

Open Telegram and message your bot:

```text
/start
```

Then try:

```text
cuantos productos hay
ventas de hoy
productos en talla M
productos en color negro
producto mas vendido
alertas de reposicion
```

## 6. Read The Logs

The log file is:

```text
D:\Coding\GestInvMundoMaterno\Tienda_Materna\logs\telegram_bot.log
```

Watch it live:

```powershell
Get-Content D:\Coding\GestInvMundoMaterno\Tienda_Materna\logs\telegram_bot.log -Wait
```

The log records:

- bot startup
- OpenClaw readiness status
- incoming Telegram messages
- chat/user/message IDs
- outgoing replies
- blocked write commands
- OpenClaw dependency failures
- errors and tracebacks

## 7. Stop The Bot

Find the running bot:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "python.exe" -and $_.CommandLine -like "*telegram_inventory_bot.py*" } | Select-Object ProcessId,CommandLine
```

Stop it by PID:

```powershell
Stop-Process -Id YOUR_PID_HERE
```

Stop OpenClaw by pressing `Ctrl+C` in the terminal running:

```powershell
openclaw gateway run
```

## 8. Full Command List

General:

```text
/start
/help
```

Inventory:

```text
cuantos productos hay
total productos
categorias
lista de categorias
ver categorias
productos de la categoria vestidos
productos de categoria blusas
productos en talla M
productos en color negro
productos entre 40000 y 60000
producto mas caro
producto mas barato
top mas stock
top menos stock
stock bajo
agotados
capital
valor inventario
```

Providers:

```text
proveedor principal
productos de proveedor ModaMater
```

Sales reports:

```text
ventas de hoy
historial de ventas
cuanto he ganado
ganancias
ingresos
producto mas vendido
```

Day operations:

```text
iniciar dia
abrir dia
empezar dia
cerrar dia
cerrar dia
```

Stock and sales writes:

```text
vender 1 blusa lactancia manga larga
registrar venta 2 vestido lactancia
agregar stock 5 blusa lactancia
agregar unidades 3 leggins embarazo
```

Direct product lookup:

```text
blusa lactancia
vestido premama
sosten lactancia
leggins embarazo
pijama maternidad
```

## 9. Enable Write Commands

Only do this if you trust who can message the bot.

In `.env`:

```env
MUNDO_MATERNO_ALLOW_MUTATIONS=1
```

Restart the bot after changing `.env`.

With mutations enabled, these commands can change the database:

```text
vender ...
agregar stock ...
iniciar dia
cerrar dia
```

## 10. Initialize Or Repair The Database

Choose one database path.

### Option A: SQLite

SQLite is the simplest option for one local machine.

In `.env`:

```env
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Initialize or repair it:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
python database.py
```

### Option B: PostgreSQL

PostgreSQL is better for shared/server use. Install the optional driver:

```powershell
pip install "psycopg[binary]"
```

Then set in `.env`:

```env
MUNDO_MATERNO_DB_ENGINE=postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mundo_materno
```

Create the schema:

```powershell
python database.py
```

Migrate existing SQLite data:

```powershell
python scripts/migrate_sqlite_to_postgres.py --truncate
```

## 11. Manual OpenClaw Bridge Test

You can test the inventory bridge directly:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
python openclaw_inventory_tool.py -- "ventas de hoy"
```

This also fails if OpenClaw is not ready.

## Safety Notes

- Rotate any Telegram bot token or API key that was pasted into chat or exposed in logs.
- Keep `.env` private.
- Keep `MUNDO_MATERNO_ALLOW_MUTATIONS=0` for public bots.
- Back up `inventario.db` before migrating to PostgreSQL.
