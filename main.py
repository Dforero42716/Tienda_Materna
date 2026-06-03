import re
import sys
from datetime import date

from modules.ventas_service import registrar_venta, agregar_stock, buscar_similares
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
    iniciar_dia,
    cerrar_dia,
)
from openclaw_guard import require_openclaw_ready

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MENU = """
+==================================================+
|       AGENTE DE INVENTARIO - TIENDA MATERNA      |
+==================================================+
| INVENTARIO                                       |
|   - cuantos productos hay                        |
|   - categorias                                   |
|   - productos de la categoria [nombre]           |
|   - productos en talla [S/M/L/XL]                |
|   - productos en color [color]                   |
|   - productos entre [min] y [max]                |
|   - producto mas caro / mas barato               |
|   - top mas stock / top menos stock              |
|   - stock bajo / agotados                        |
|   - capital                                      |
|                                                  |
| PROVEEDORES                                      |
|   - proveedor principal                          |
|   - productos de proveedor [nombre]              |
|                                                  |
| VENTAS                                           |
|   - vender [cantidad] [producto]                 |
|   - agregar stock [cantidad] [producto]          |
|   - ventas de hoy                                |
|   - iniciar dia                                  |
|   - historial de ventas                          |
|   - cuanto he ganado                             |
|   - producto mas vendido                         |
|                                                  |
| ALERTAS                                          |
|   - alertas de reposicion                        |
|                                                  |
| Escribe 'salir' para terminar                    |
+==================================================+
"""

FORMATO_VENTA = (
    "Para registrar una venta necesito:\n"
    "  vender [cantidad] [nombre del producto]\n\n"
    "Ejemplo: vender 2 blusa lactancia manga larga"
)

MENSAJE_COMANDOS = (
    "Hola, soy Mundo Materno. Puedes escribirme:\n"
    "- cuantos productos hay\n"
    "- ventas de hoy\n"
    "- categorias\n"
    "- productos en talla M\n"
    "- productos en color negro\n"
    "- producto mas vendido\n"
    "- registrar venta\n"
    "- vender 2 blusa lactancia"
)

SALUDOS = {
    "hola",
    "buenas",
    "buenos dias",
    "buen dia",
    "buenas tardes",
    "buenas noches",
    "hey",
}


def _extraer_cantidad_y_nombre(texto, comandos, ejemplo):
    partes = texto
    for comando in comandos:
        if partes.startswith(comando):
            partes = partes[len(comando):].strip()
            break

    match = re.fullmatch(r"(\d+)\s+(.+)", partes)
    if not match:
        return None, None, ejemplo

    cantidad = int(match.group(1))
    nombre = match.group(2).strip()
    if cantidad <= 0:
        return None, None, "La cantidad debe ser mayor que cero."
    if not nombre:
        return None, None, ejemplo
    return cantidad, nombre, None


def _es_intencion_venta(texto):
    if texto.startswith("vender") or texto.startswith("registrar venta"):
        return True
    patrones = (
        r"\b(?:quiero\s+)?(?:registrar|hacer|anotar|crear)\s+(?:una\s+)?venta\b",
        r"\b(?:quiero\s+)?vender\b",
    )
    return any(re.search(patron, texto) for patron in patrones)


def _extraer_venta(texto):
    if texto.startswith("vender") or texto.startswith("registrar venta"):
        return _extraer_cantidad_y_nombre(
            texto,
            ("registrar venta", "vender"),
            FORMATO_VENTA,
        )

    match = re.search(
        r"\b(?:quiero\s+)?(?:(?:registrar|hacer|anotar|crear)\s+(?:una\s+)?venta|vender)\b",
        texto,
    )
    partes = texto[match.end():].strip() if match else ""
    if partes.startswith("de "):
        partes = partes[3:].strip()

    match_cantidad = re.fullmatch(r"(\d+)\s+(.+)", partes)
    if not match_cantidad:
        return None, None, FORMATO_VENTA

    cantidad = int(match_cantidad.group(1))
    nombre = match_cantidad.group(2).strip()
    if cantidad <= 0:
        return None, None, "La cantidad debe ser mayor que cero."
    if not nombre:
        return None, None, FORMATO_VENTA
    return cantidad, nombre, None


def _normalizar_comandos(texto):
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto


def _parsear_precio(texto):
    return float(texto.replace(".", "").replace(",", ""))


def _formatear_productos(productos, plantilla, vacio):
    if not productos:
        return vacio
    return "\n".join(plantilla(*producto) for producto in productos)


def _responder_no_encontrado(nombre, con_precio=False):
    similares = buscar_similares(nombre)
    if similares:
        if con_precio:
            lineas = [f"- {n} (Talla {t}, {c}): {s} uds - ${p:,.0f}" for n, t, c, s, p in similares]
        else:
            lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n, t, c, s, p in similares]
        return f"No encontre '{nombre}'. Opciones similares:\n" + "\n".join(lineas)
    return f"No encontre '{nombre}' en el inventario."


def preguntar(mensaje):
    require_openclaw_ready()

    texto = _normalizar_comandos(mensaje.lower().strip())

    if not texto:
        return "Escribe una pregunta o comando."

    if texto in SALUDOS or texto in {"menu", "ayuda", "comandos"}:
        return MENSAJE_COMANDOS

    # AGREGAR STOCK
    if texto.startswith("agregar stock") or texto.startswith("agregar unidades"):
        cantidad, nombre, error = _extraer_cantidad_y_nombre(
            texto,
            ("agregar stock", "agregar unidades"),
            "Formato: agregar stock 10 blusa lactancia",
        )
        if error:
            return error

        producto = buscar_producto_inteligente(nombre)
        if not producto:
            return _responder_no_encontrado(nombre)

        id_producto, nombre_db, stock, _, _ = producto
        try:
            agregar_stock(id_producto, cantidad)
        except ValueError as exc:
            return str(exc)

        return (
            f"Stock actualizado.\n"
            f"Producto: {nombre_db}\n"
            f"Stock anterior: {stock}\n"
            f"Stock nuevo: {stock + cantidad}"
        )

    # VENTAS
    if _es_intencion_venta(texto):
        cantidad, nombre, error = _extraer_venta(texto)
        if error:
            return error

        producto = buscar_producto_inteligente(nombre)
        if not producto:
            return _responder_no_encontrado(nombre, con_precio=True)

        id_producto = producto[0]
        try:
            venta = registrar_venta(id_producto, cantidad)
        except ValueError as exc:
            return str(exc)

        return (
            f"Venta registrada.\n"
            f"Producto: {venta['nombre']}\n"
            f"Cantidad: {cantidad}\n"
            f"Stock restante: {venta['stock_restante']}\n"
            f"Ganancia: ${venta['ganancia']:,.0f}"
        )

    # TOP STOCK
    if "mas stock" in texto or "mayor stock" in texto or "mas unidades" in texto:
        productos = top_mas_stock()
        lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n, t, c, s in productos]
        return "Top 10 productos con mas stock:\n" + "\n".join(lineas)

    if "menos stock" in texto or "poco stock" in texto or "menor stock" in texto:
        productos = top_menos_stock()
        lineas = [f"- {n} (Talla {t}, {c}): {s} uds" for n, t, c, s in productos]
        return "Top 10 productos con menos stock:\n" + "\n".join(lineas)

    # STOCK BAJO Y AGOTADOS
    if "stock bajo" in texto:
        productos = stock_bajo()
        if not productos:
            return "No hay productos con stock bajo."
        lineas = [f"- {p[1]} ({p[2]} uds)" for p in productos]
        return "Productos con stock bajo:\n" + "\n".join(lineas)

    if "agotado" in texto:
        productos = productos_agotados()
        return "\n".join([f"- {p[1]}" for p in productos]) if productos else "No hay productos agotados."

    # PRECIO
    if "mas caro" in texto or "mas costoso" in texto:
        nombre, precio = producto_mas_caro()
        return f"Producto mas caro: {nombre} (${precio:,.0f})"

    if "mas barato" in texto or "menor precio" in texto:
        nombre, precio = producto_mas_barato()
        return f"Producto mas barato: {nombre} (${precio:,.0f})"

    if "productos entre" in texto:
        match = re.search(r"productos entre\s+([\d.,]+)\s+y\s+([\d.,]+)", texto)
        if not match:
            return "Formato: productos entre 40000 y 60000"
        minimo = _parsear_precio(match.group(1))
        maximo = _parsear_precio(match.group(2))
        if minimo > maximo:
            minimo, maximo = maximo, minimo
        productos = productos_por_rango_precio(minimo, maximo)
        lineas = _formatear_productos(
            productos,
            lambda n, cat, t, c, s, p: f"- {n} ({cat}, Talla {t}, {c}): {s} uds - ${p:,.0f}",
            "No hay productos en ese rango de precio.",
        )
        return f"Productos entre ${minimo:,.0f} y ${maximo:,.0f}:\n" + lineas

    # CAPITAL
    if "capital" in texto or "valor inventario" in texto:
        return f"Capital inmovilizado en inventario: ${valor_total_inventario():,.0f} COP"

    # CATEGORIAS
    if texto == "categorias" or "lista de categorias" in texto or "ver categorias" in texto:
        cats = productos_por_categoria()
        if not cats:
            return "No hay categorias registradas."
        lineas = [f"- {cat}: {cant} producto(s)" for cat, cant in cats]
        return "Categorias:\n" + "\n".join(lineas)

    if "productos de la categoria" in texto or "productos de categoria" in texto:
        cat = texto.replace("productos de la categoria", "").replace("productos de categoria", "").strip()
        if not cat:
            return "Indica la categoria. Ejemplo: productos de la categoria vestidos"
        productos = productos_por_categoria_detalle(cat)
        if not productos:
            return f"No hay productos en la categoria '{cat}'."
        lineas = [f"- {n} (Talla {t}, {c}): {s} uds - ${p:,.0f}" for n, t, c, s, p in productos]
        return f"Productos en '{cat}':\n" + "\n".join(lineas)

    if "productos en talla" in texto:
        talla = texto.replace("productos en talla", "").strip()
        if not talla:
            return "Indica la talla. Ejemplo: productos en talla M"
        productos = buscar_por_talla(talla)
        lineas = _formatear_productos(
            productos,
            lambda n, cat, c, s, p: f"- {n} ({cat}, {c}): {s} uds - ${p:,.0f}",
            f"No hay productos en talla '{talla}'.",
        )
        return f"Productos en talla '{talla.upper()}':\n" + lineas

    if "productos en color" in texto:
        color = texto.replace("productos en color", "").strip()
        if not color:
            return "Indica el color. Ejemplo: productos en color negro"
        productos = buscar_por_color(color)
        lineas = _formatear_productos(
            productos,
            lambda n, cat, t, s, p: f"- {n} ({cat}, Talla {t}): {s} uds - ${p:,.0f}",
            f"No hay productos en color '{color}'.",
        )
        return f"Productos en color '{color}':\n" + lineas

    # PROVEEDORES
    if "proveedor principal" in texto:
        proveedor, cantidad = proveedor_con_mas_productos()
        return f"Proveedor principal: {proveedor} ({cantidad} producto(s))"

    if "productos de proveedor" in texto:
        proveedor = texto.replace("productos de proveedor", "").strip()
        if not proveedor:
            return "Indica el proveedor. Ejemplo: productos de proveedor ModaMater"
        productos = buscar_por_proveedor(proveedor)
        lineas = _formatear_productos(
            productos,
            lambda n, cat, t, c, s, p: f"- {n} ({cat}, Talla {t}, {c}): {s} uds - ${p:,.0f}",
            f"No hay productos del proveedor '{proveedor}'.",
        )
        return f"Productos del proveedor '{proveedor}':\n" + lineas

    # TOTAL PRODUCTOS
    if "cuantos" in texto or "total productos" in texto:
        return f"Total productos: {total_productos()}"

    # VENTAS DEL DIA
    if "ventas de hoy" in texto:
        hoy = date.today().isoformat()
        ventas = ventas_del_dia(hoy)
        if not ventas:
            return f"No hay ventas registradas hoy ({hoy})."
        lineas = [f"- {n}: {cant} uds - ${pv:,.0f} (ganancia ${g:,.0f})" for n, cant, pv, g, _ in ventas]
        return f"Ventas de hoy ({hoy}):\n" + "\n".join(lineas)

    if "iniciar dia" in texto or "abrir dia" in texto or "empezar dia" in texto:
        r = iniciar_dia()
        prefijo = "El dia ya estaba iniciado." if r["ya_existia"] else "Dia iniciado."
        return (
            f"{prefijo}\n"
            f"Fecha: {r['fecha']}\n"
            f"Inicio: {r['inicio']}\n"
            f"Estado: {r['estado']}\n"
            f"Ventas al inicio: {r['ventas_iniciales']}\n"
            f"Capital inicial: ${r['capital_inicial']:,.0f} COP"
        )

    if "cuanto he ganado" in texto or "ganancias" in texto or "ingresos" in texto:
        r = ganancias_totales()
        return (
            "Resumen de ventas:\n"
            f"- Ventas registradas: {r['ventas']}\n"
            f"- Ingresos: ${r['ingresos']:,.0f} COP\n"
            f"- Ganancias: ${r['ganancias']:,.0f} COP"
        )

    if "producto mas vendido" in texto:
        nombre, cantidad = producto_mas_vendido()
        return f"Producto mas vendido: {nombre} ({cantidad} uds)"

    # HISTORIAL
    if "historial" in texto:
        fechas = historial_semana()
        return "\n".join(fechas) if fechas else "No hay historial."

    # ALERTAS
    if "alerta" in texto or "reposicion" in texto:
        hoy, semana, sin_ventas = alertas_reposicion()
        lineas = [
            f"Alta demanda hoy: {len(hoy)} producto(s)",
            f"Alta demanda semanal: {len(semana)} producto(s)",
            f"Con stock alto y sin ventas: {len(sin_ventas)} producto(s)",
        ]
        if hoy:
            lineas.append("Hoy: " + ", ".join(f"{n} ({total} uds)" for n, _, total in hoy))
        if semana:
            lineas.append("Semana: " + ", ".join(f"{n} ({total} uds)" for n, _, total in semana))
        if sin_ventas:
            lineas.append("Sin ventas: " + ", ".join(f"{n} ({stock} uds)" for n, _, _, stock in sin_ventas))
        return "Alertas de reposicion:\n" + "\n".join(lineas)

    # CERRAR DIA
    if "cerrar dia" in texto:
        r = cerrar_dia()
        return (
            f"Dia cerrado y guardado.\n"
            f"Fecha: {r['fecha']}\n"
            f"Ventas realizadas: {r['ventas']}\n"
            f"Ingresos del dia: ${r['ingresos']:,.0f} COP\n"
            f"Ganancias del dia: ${r['ganancias']:,.0f} COP\n"
            f"Producto top: {r['producto_top']}\n"
            f"Menos vendido: {r['producto_menos']}\n"
            f"Capital inmovilizado: ${r['capital']:,.0f} COP"
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
        return "\n".join([f"- {n}" for n, _, _, _, _ in similares])

    return "No encontrado."


if __name__ == "__main__":
    print(MENU)
    print(f"Hoy es {date.today().isoformat()}")

    while True:
        pregunta = input("Tu: ").strip()
        if pregunta.lower() == "salir":
            break
        if pregunta.lower() == "menu":
            print(MENU)
            continue
        print(preguntar(pregunta))
