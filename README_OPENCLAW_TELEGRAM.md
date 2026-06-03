# Mundo Materno Telegram Bot

This project can answer inventory questions from Telegram using `telegram_inventory_bot.py`.

The bot uses the same command router as the local CLI: `main.preguntar()`. It does **not** calculate totals from logs. Logs are only an audit trail. Inventory, sales, stock, day open/close, and totals come from the database.

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

## 2. Start The Bot

Run:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
python telegram_inventory_bot.py
```

Leave that terminal open while you want the bot to respond.

If you want to start it hidden/background from PowerShell:

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
Start-Process -FilePath python -ArgumentList "telegram_inventory_bot.py" -WorkingDirectory "D:\Coding\GestInvMundoMaterno\Tienda_Materna" -WindowStyle Hidden
```

## 3. Use It In Telegram

Open Telegram and message your bot. Example:

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

## 4. Read The Logs

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
- incoming Telegram messages
- chat/user/message IDs
- outgoing replies
- blocked write commands
- errors and tracebacks

## 5. Stop The Bot

Find the running bot:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "python.exe" -and $_.CommandLine -like "*telegram_inventory_bot.py*" } | Select-Object ProcessId,CommandLine
```

Stop it by PID:

```powershell
Stop-Process -Id YOUR_PID_HERE
```

## 6. Full Command List

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
cerrar día
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

## 7. Enable Write Commands

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

## 8. Initialize Or Repair The Database

SQLite is the default.

```powershell
cd D:\Coding\GestInvMundoMaterno\Tienda_Materna
python database.py
```

## 9. PostgreSQL Mode

SQLite remains the default. To use PostgreSQL, install the optional driver:

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

## 10. Optional OpenClaw Notes

OpenClaw is not required for the current working Telegram bot. The direct bot is simpler and uses:

```text
telegram_inventory_bot.py
```

If you later want to use OpenClaw again, the inventory bridge is:

```powershell
python openclaw_inventory_tool.py -- "ventas de hoy"
```

The OpenClaw skill files are in:

```text
openclaw/mundo-materno-inventory/SKILL.md
skills/mundo-materno-inventory/SKILL.md
```

## Safety Notes

- Rotate any Telegram bot token that was pasted into chat or committed accidentally.
- Keep `.env` private.
- Keep `MUNDO_MATERNO_ALLOW_MUTATIONS=0` for public bots.
- Back up `inventario.db` before migrating to PostgreSQL.
