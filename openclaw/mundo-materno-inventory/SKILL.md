---
name: mundo-materno-inventory
description: Use this skill for every Mundo Materno inventory, sales, stock, provider, category, price, daily close, or replenishment request.
user-invocable: true
---

# Mundo Materno Inventory

Use this skill for every Mundo Materno inventory, sales, stock, provider, category, price, daily close, or replenishment request.

## Tool Bridge

Call the local Python bridge from the project root:

```powershell
python openclaw_inventory_tool.py -- "<user command>"
```

For commands that intentionally modify inventory or sales, require explicit user confirmation first, then call:

```powershell
python openclaw_inventory_tool.py --allow-mutations -- "<confirmed user command>"
```

Mutating commands include:

- `vender [cantidad] [producto]`
- `registrar venta [cantidad] [producto]`
- `agregar stock [cantidad] [producto]`
- `agregar unidades [cantidad] [producto]`
- `iniciar dia`
- `cerrar dia`

## Rules

- Never invent product names, prices, stock, providers, sales totals, or profit.
- Return the bridge output as the answer. Keep formatting readable in Telegram.
- Ask for confirmation before every mutating command, even if the sender is allowlisted.
- If a product match is ambiguous, show the options returned by the bridge and ask the user which one to use.
- Do not query or mutate the database directly from Telegram. Use the bridge.
- For PostgreSQL deployments, assume the bridge reads `DATABASE_URL` from the OpenClaw gateway environment.

## Useful Commands

- `cuantos productos hay`
- `categorias`
- `productos de la categoria vestidos`
- `productos en talla M`
- `productos en color negro`
- `productos entre 40000 y 60000`
- `proveedor principal`
- `productos de proveedor ModaMater`
- `ventas de hoy`
- `iniciar dia`
- `cuanto he ganado`
- `producto mas vendido`
- `alertas de reposicion`
