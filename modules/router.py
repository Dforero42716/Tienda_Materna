from modules.analisis import stock_total, productos_bajo_stock, capital_inmovilizado, inventario_completo
from modules.ventas import ventas_del_dia, resumen_ventas

def enrutar(pregunta: str) -> str:
    p = pregunta.lower().strip()

    # Stock total
    if any(x in p for x in ["cuánto stock", "cuanto stock", "total de stock", "stock total"]):
        total = stock_total()
        return f"El stock total en inventario es {total} unidades."

    # Productos con poco stock
    if any(x in p for x in ["poco stock", "bajo stock", "quedan pocos", "reabastecer", "reponer"]):
        productos = productos_bajo_stock()
        if not productos:
            return "No hay productos con stock bajo en este momento."
        lineas = [f"- {nombre} (Talla {talla}, {color}): {stock} unidades" for nombre, talla, color, stock in productos]
        return "Productos con stock bajo:\n" + "\n".join(lineas)

    # Capital inmovilizado
    if any(x in p for x in ["capital", "inmovilizado", "invertido", "dinero en inventario"]):
        capital = capital_inmovilizado()
        return f"El capital inmovilizado en inventario es ${capital:,.0f} COP."

    # Inventario completo
    if any(x in p for x in ["inventario", "todos los productos", "lista de productos", "qué hay"]):
        productos = inventario_completo()
        if not productos:
            return "No hay productos en inventario."
        lineas = [f"- [{id_p}] {nombre} (Talla {talla}, {color}): {stock} uds — ${precio:,.0f}" for id_p, nombre, talla, color, stock, precio in productos]
        return "Inventario actual:\n" + "\n".join(lineas)

    # Ventas del día
    if any(x in p for x in ["ventas de hoy", "vendí hoy", "vendi hoy", "ventas del día", "ventas del dia"]):
        ventas = ventas_del_dia()
        if not ventas:
            return "No hay ventas registradas hoy."
        lineas = [f"- {nombre}: {cantidad} uds — ${precio:,.0f} (ganancia ${ganancia:,.0f})" for nombre, cantidad, precio, ganancia in ventas]
        return "Ventas de hoy:\n" + "\n".join(lineas)

    # Resumen general de ventas
    if any(x in p for x in ["resumen", "ganancias", "ingresos", "cuánto he ganado", "cuanto he ganado"]):
        r = resumen_ventas()
        return (f"Resumen de ventas:\n"
                f"- Ingresos totales: ${r['ingresos_totales']:,.0f} COP\n"
                f"- Ganancias totales: ${r['ganancias_totales']:,.0f} COP\n"
                f"- Número de ventas: {r['numero_ventas']}")

    # No reconocido
    return "no entendí"