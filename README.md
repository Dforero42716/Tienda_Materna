# Mundo Materno Inventory Assistant

Mundo Materno Inventory Assistant is a Telegram-based inventory and sales helper for a maternity clothing store. It lets the store owner ask natural Spanish commands about stock, categories, sizes, colors, prices, sales, daily closing, and product rotation without opening a spreadsheet or database tool.

The assistant is designed around Yaneth's daily workflow: checking what is available, answering customer questions quickly, registering confirmed sales, seeing what sold today, closing the business day, and receiving recommendations about products that may need restocking or price adjustments.

## What The Project Does

The bot responds to Telegram messages such as:

```text
hola
cuantos productos hay
Vestidos
productos en talla M
productos en color negro
ventas de hoy
vender 2 blusa lactancia
producto mas vendido
producto menos vendido
cerrar dia
recomendaciones
```

When the user sends `hola`, `/start`, `menu`, `ayuda`, or `comandos`, the assistant shows a friendly menu with emojis. If any product has fewer than 3 units, it first shows a low-stock alert.

For commands that need more context, the assistant continues the conversation. For example, `productos en talla M` asks which category to search before listing results. Sales are not saved immediately: `vender 2 blusa lactancia` first shows a confirmation with the product, quantity, current stock, projected remaining stock, and profit. The sale is only written after the user replies `si`.

## Main Features

- Telegram bot interface using the standard Telegram Bot API.
- Required OpenClaw readiness gate before inventory answers are served.
- SQLite database by default, with optional PostgreSQL support.
- Initial inventory seed with maternity clothing products across categories.
- Product lookup by category, size, color, provider, price range, and approximate product name.
- Category buttons in Telegram for quick browsing.
- Low-stock and out-of-stock reporting.
- Sales registration with confirmation before mutation.
- Daily sales reports and specific-date sales lookup.
- Daily business close summary with income, profit, top product, least-sold product, and capital held in inventory.
- Product rotation recommendations for restocking and price reduction decisions.
- Logs for Telegram activity, OpenClaw readiness, blocked write commands, and errors.

## Architecture

The project is intentionally small and local-first. The core components are:

```text
telegram_inventory_bot.py      Telegram polling loop, message handling, inline category buttons
main.py                        Assistant command parser, conversation state, menu text, response formatting
database.py                    Database schema, SQLite/PostgreSQL connection setup, initial product seed
modules/analisis.py            Inventory, sales, stock, category, rotation, and daily-close queries
modules/ventas_service.py      Stock updates and sale registration
modules/product_matcher.py     Product name matching and normalization
openclaw_guard.py              OpenClaw CLI/config/skill/gateway readiness checks
openclaw_inventory_tool.py     CLI bridge used by OpenClaw workflows
env_loader.py                  Local .env loading
scripts/migrate_sqlite_to_postgres.py
                               Optional migration helper
```

OpenClaw is mandatory for normal operation. If the CLI, configuration, required `mundo-materno-inventory` skill, or gateway is missing, the assistant refuses to answer inventory commands instead of silently bypassing the dependency.

## Data Model

The database contains four main tables:

- `Productos`: product ID, name, category, size, color, wholesale price, retail price, stock, entry date, and provider.
- `Ventas`: sale records with product, quantity, date, sale value, and profit.
- `Historial_Mensual`: saved daily/monthly-style summaries used by close-day operations.
- `Dia_Operativo`: business day open/close state, capital snapshots, and sales counters.

SQLite stores data in `inventario.db`. PostgreSQL can be enabled with `MUNDO_MATERNO_DB_ENGINE=postgres` and `DATABASE_URL`.

## Requirements

Install:

```text
Python 3.11+
Node.js
npm
OpenClaw
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Install OpenClaw if needed:

```powershell
npm install -g openclaw
```

## Environment Configuration

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
notepad .env
```

Minimum values:

```env
TELEGRAM_BOT_TOKEN=your_botfather_token
MUNDO_MATERNO_ALLOW_MUTATIONS=0
MUNDO_MATERNO_DB_ENGINE=sqlite
```

Keep `MUNDO_MATERNO_ALLOW_MUTATIONS=0` while the bot is exposed to untrusted users. Set it to `1` only when trusted users should be allowed to change inventory, register sales, start the day, or close the day.

## Running Locally

Initialize or repair the database:

```powershell
python database.py
```

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

Start the OpenClaw gateway:

```powershell
openclaw gateway run
```

In another terminal, start the Telegram bot:

```powershell
python telegram_inventory_bot.py
```

For a fresh-machine setup walkthrough, see `README_CLONE_SETUP.md`. For the full OpenClaw/Telegram operational guide, see `README_OPENCLAW_TELEGRAM.md`.

## Command Guide

General:

```text
/start
/help
hola
menu
ayuda
comandos
```

Inventory:

```text
cuantos productos hay
total productos
categorias
lista de categorias
ver categorias
Vestidos
productos de la categoria vestidos
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

Sales and reports:

```text
ventas de hoy
ventas del 3 de junio de 2026
historial de ventas
cuanto he ganado
ganancias
ingresos
producto mas vendido
producto menos vendido
recomendaciones
```

Mutating commands:

```text
vender 1 blusa lactancia manga larga
registrar venta 2 vestido lactancia
agregar stock 5 blusa lactancia
agregar unidades 3 leggins embarazo
iniciar dia
cerrar dia
```

## Safety Notes

- Keep `.env` private.
- Never commit real Telegram tokens, API keys, or production database credentials.
- Back up `inventario.db` before migrations or bulk changes.
- Do not run OpenClaw's Telegram channel and `telegram_inventory_bot.py` with the same bot token at the same time.
- Leave `MUNDO_MATERNO_ALLOW_MUTATIONS=0` unless the Telegram audience is trusted.

## Logs

Telegram logs are written to:

```text
logs/telegram_bot.log
```

Watch logs live:

```powershell
Get-Content logs\telegram_bot.log -Wait
```

The log records startup, OpenClaw readiness, incoming messages, outgoing replies, blocked mutating commands, callback handling, and exceptions.
