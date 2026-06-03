import re
from datetime import date
from modules.ventas_service import actualizar_stock, registrar_venta, agregar_stock, buscar_similares
from modules.product_matcher import buscar_producto_inteligente
from modules.analisis import (
    total_productos,
    stock_bajo,
    productos_agotados,
    producto_mas_caro,
    producto_mas_barato,
    valor_total_inventario,
    productos_por_categoria,
    productos_por_categoria_detalle,
    proveedor_con_mas_productos,
    top_mas_stock,
    top_menos_stock,
    buscar_por_talla,
    buscar_por_color,
    buscar_por_proveedor,
    productos_por_rango_precio,
    ventas_del_dia,
    ganancias_totales,
    producto_mas_vendido,
    historial_semana,
    alertas_reposicion,
    cerrar_dia
)

CATEGORIAS = ["ropa interior","vestidos","pijamas","leggins","camisetas","blusas","jeans","faldas","conjuntos","chaquetas"]

MENU = """
╔══════════════════════════════════════════════════╗
║       AGENTE DE INVENTARIO — TIENDA MATERNA      ║
╠══════════════════════════════════════════════════╣
║  📦 INVENTARIO                                   ║
║   • cuantos productos hay                        ║
║   • categorias                                   ║
║   • productos de la categoria [nombre]           ║
║   • productos en talla [S/M/L/XL]               ║
║   • productos en color [color]                   ║
║   • productos entre [min] y [max]                ║
║   • producto mas caro / mas barato               ║
║   • top mas stock / top menos stock              ║
║   • stock bajo / agotados                        ║
║   • capital                                      ║
║                                                  ║
║  🏷️ PROVEEDORES                                  ║
║   • proveedor principal                          ║
║   • productos de proveedor [nombre]              ║
║                                                  ║
║  💰 VENTAS                                       ║
║   • vender [cantidad] [producto]                 ║
║   • agregar stock [cantidad] [producto]          ║
║   • ventas de hoy                                ║
║   • historial de ventas                          ║
║   • cuanto he ganado                             ║
║   • producto mas vendido                         ║
║                                                  ║
║  🚨 ALERTAS                                      ║
║   • alertas de reposicion                        ║
║                                                  ║
║  Escribe 'salir' para terminar                   ║
╚══════════════════════════════════════════════════╝
"""

def preguntar(mensaje):
    texto = mensaje.lower().strip()

    # AGREGAR STOCK
    if "agregar stock" in texto or "agregar unidades" in texto:
        match = re.search(r"(\d+)\s+(.+)", texto.replace("agregar stock","").replace("agregar unidades","").strip())
        if not match:
            return "Formato: agregar stock 10 blusa lactancia"
        cantidad = int(match.group(1))
        nombre = match.group(2)
        producto = buscar_producto_inteligente(nombre)
        if not producto:
            similares = buscar_similares(nombre)
            if similares:
                lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n,t,c,s,p in similares]
                return f"No encontré '{nombre}'. ¿Quisiste decir?\n" + "\n".join(lineas)
            return f"No encontré '{nombre}' en el inventario."
        id_producto, nombre_db, stock, _, _ = producto
        agregar_stock(id_producto, cantidad)
        return f"Stock actualizado.\nProducto: {nombre_db}\nStock anterior: {stock}\nStock nuevo: {stock + cantidad}"

    # VENTAS
    if "vender" in texto or "registrar venta" in texto:
        partes = texto.replace("vender","").replace("registrar venta","").strip()
        match = re.search(r"(\d+)\s+(.+)", partes)
        if not match:
            return (
                "Para registrar una venta necesito:\n"
                "  vender [cantidad] [nombre del producto]\n\n"
                "Ejemplo: vender 2 blusa lactancia manga larga"
            )
        cantidad = int(match.group(1))
        nombre = match.group(2)
        producto = buscar_producto_inteligente(nombre)
        if not producto:
            similares = buscar_similares(nombre)
            if similares:
                lineas = [f"- {n} (Talla {t}, {c}): {s} uds — ${p:,.0f}" for n,t,c,s,p in similares]
                return f"No encontré '{nombre}'. Opciones similares:\n" + "\n".join(lineas)
            return f"No encontré '{nombre}' en el inventario."
        id_producto, nombre_db, stock, precio_detal, precio_mayorista = producto
        if stock < cantidad:
            return f"Stock insuficiente. Solo hay {stock} unidades de {nombre_db}."
        actualizar_stock(id_producto, stock - cantidad)
        ganancia = registrar_venta(id_producto, cantidad, precio_detal, precio_mayorista)
        return (
            f"✅ Venta registrada.\n"
            f"Producto: {nombre_db}\n"
            f"Cantidad: {cantidad}\n"
            f"Stock restante: {stock - cantidad}\n"
            f"Ganancia: ${ganancia:,.0f}"
        )

    # TOP STOCK
    elif "mas stock" in texto or "mayor stock" in texto or "mas unidades" in texto:
        productos = top_mas_stock()
        lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n,t,c,s in productos]
        return "Top 10 productos con más stock:\n" + "\n".join(lineas)

    elif "menos stock" in texto or "poco stock" in texto or "menor stock" in texto:
        productos = top_menos_stock()
        lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n,t,c,s in productos]
        return "Top 10 productos con menos stock:\n" + "\n".join(lineas)

    # STOCK BAJO Y AGOTADOS
    elif "stock bajo" in texto:
        productos = stock_bajo()
        if not productos:
            return "No hay productos con stock bajo."
        lineas = [f"- {p[1]} ({p[2]} uds)" for p in productos]
        return "Productos con stock bajo:\n" + "\n".join(lineas)

    elif "agotado" in texto:
        productos = productos_agotados()
        return "\n".join([f"- {p[1]}" for p in productos]) if productos else "No hay productos agotados."

    # PRECIO
    elif "mas caro" in texto or "más caro" in texto:
        nombre, precio = producto_mas_caro()
        return f"Producto más caro: {nombre} (${precio:,.0f})"

    elif "mas barato" in texto or "más barato" in texto:
        nombre, precio = producto_mas_barato()
        return f"Producto más barato: {nombre} (${precio:,.0f})"

    # CAPITAL
    elif "capital" in texto or "valor inventario" in texto:
        return f"Capital inmovilizado en inventario: ${valor_total_inventario():,.0f} COP"

    # TOTAL PRODUCTOS
    elif "cuantos" in texto or "total productos" in texto:
        return f"Total productos: {total_productos()}"

    # VENTAS DEL DIA
    elif "ventas de hoy" in texto:
        hoy = date.today().isoformat()
        ventas = ventas_del_dia(hoy)
        if not ventas:
            return f"No hay ventas registradas hoy ({hoy})."
        lineas = [f"- {n}: {cant} uds — ${pv:,.0f} (ganancia ${g:,.0f})" for n,cant,pv,g,f in ventas]
        return f"Ventas de hoy ({hoy}):\n" + "\n".join(lineas)

    # HISTORIAL
    elif "historial" in texto:
        fechas = historial_semana()
        return "\n".join(fechas) if fechas else "No hay historial."

    # ALERTAS
    elif "alerta" in texto or "reposicion" in texto:
        hoy, semana, sin_ventas = alertas_reposicion()
        return f"Alertas: hoy={len(hoy)}, semana={len(semana)}, sin ventas={len(sin_ventas)}"

    # CERRAR DÍA (AGREGADO)
    elif "cerrar dia" in texto or "cerrar día" in texto:
        r = cerrar_dia()
        return (
            f"✅ Día cerrado y guardado.\n"
            f"📅 Fecha: {r['fecha']}\n"
            f"🛍️ Ventas realizadas: {r['ventas']}\n"
            f"💵 Ingresos del día: ${r['ingresos']:,.0f} COP\n"
            f"💰 Ganancias del día: ${r['ganancias']:,.0f} COP\n"
            f"⭐ Producto top: {r['producto_top']}\n"
            f"📉 Menos vendido: {r['producto_menos']}\n"
            f"🏦 Capital inmovilizado: ${r['capital']:,.0f} COP"
        )

    # BUSCAR PRODUCTO
    producto = buscar_producto_inteligente(texto)
    if producto:
        _, nombre, stock, precio_detal, _ = producto
        return (
            f"Producto: {nombre}\n"
            f"Stock: {stock}\n"
            f"Precio: ${precio_detal:,.0f}"
        )

    similares = buscar_similares(texto)
    if similares:
        return "\n".join([f"- {n}" for n,_,_,_,_ in similares])

    return "No encontrado."

if __name__ == "__main__":
    print(MENU)
    print(f"📅 Hoy es {date.today().isoformat()}")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() == "salir":
            break
        if pregunta.lower() == "menu":
            print(MENU)
            continue
        print(preguntar(pregunta))