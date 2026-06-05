import re
import sys
import unicodedata
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
    buscar_por_talla_categoria,
    buscar_por_color_categoria,
    buscar_por_proveedor,
    productos_por_rango_precio,
    ventas_del_dia,
    venta_producto_por_fecha,
    ganancias_totales,
    producto_mas_vendido,
    productos_vendidos_extremos,
    historial_semana,
    alertas_reposicion,
    categorias_disponibles,
    categoria_existe,
    recomendaciones_rotacion,
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

MENSAJE_BIENVENIDA = "👋 Hola Yaneth, soy tu asistente personal. Dime que quieres hacer:"

COMANDOS_DISPONIBLES = (
    "📋 Comandos disponibles:\n"
    "📦 cuantos productos hay - te digo cuantos productos por categoria y total\n"
    "🧾 ventas de hoy - te muestro todo lo vendido hoy\n"
    "🏷️ [nombre de categoria] - para ver todos los productos de ese tipo (ej: Vestidos)\n"
    "📏 productos en talla [S, M, L o XL] - te muestro que hay disponible en esa talla\n"
    "🎨 productos en color [color] - te muestro que hay disponible en ese color\n"
    "🏆 producto mas vendido - te digo cual producto se ha vendido mas y cuantas unidades\n"
    "📉 producto menos vendido - te digo cual producto se ha vendido menos\n"
    "💰 registrar venta - escribelo asi: vender 2 blusa lactancia\n"
    "📅 ventas de un dia especifico - escribelo asi: ventas del 3 de junio de 2026\n"
    "🔒 cerrar dia - guarda el resumen del dia y cierra la jornada\n"
    "💡 recomendaciones - consejos sobre que productos pedir mas y cuales bajar de precio"
)

MENSAJE_COMANDOS = f"{MENSAJE_BIENVENIDA}\n\n{COMANDOS_DISPONIBLES}"

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
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    reemplazos = {
        "Ã¡": "a",
        "Ã©": "e",
        "Ã­": "i",
        "Ã³": "o",
        "Ãº": "u",
        "Ã¼": "u",
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


def _formato_cop(valor):
    return f"${valor:,.0f}".replace(",", ".")


def _alerta_stock_bajo():
    productos = stock_bajo()
    if not productos:
        return ""
    lineas = ["⚠️ Productos con stock bajo:"]
    lineas.extend(f"   {nombre}: {stock} unidades" for _, nombre, stock in productos)
    return "\n".join(lineas)


def mensaje_inicio():
    alerta = _alerta_stock_bajo()
    if alerta:
        return f"{alerta}\n\n{MENSAJE_COMANDOS}"
    return MENSAJE_COMANDOS


MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

MESES_POR_NUMERO = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def _fecha_larga(fecha_iso):
    anio, mes, dia = (int(parte) for parte in fecha_iso.split("-"))
    return f"{dia} de {MESES_POR_NUMERO[mes]} de {anio}"


def _parsear_fecha_ventas(texto):
    match = re.search(r"ventas\s+del\s+(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})", texto)
    if match:
        mes = MESES.get(match.group(2))
        if mes:
            return date(int(match.group(3)), mes, int(match.group(1))).isoformat()
    match = re.search(r"ventas\s+del\s+(\d{4}-\d{2}-\d{2})", texto)
    return match.group(1) if match else None


def _categorias_texto():
    return ", ".join(categorias_disponibles())


def _respuesta_extremos(desc=True):
    globales, por_categoria = productos_vendidos_extremos(desc=desc)
    titulo = "Productos mas vendidos:" if desc else "Productos menos vendidos:"
    lineas = [titulo]
    lineas.extend(
        f"   {nombre} - {total} unidades vendidas"
        for nombre, _, total in globales
    )
    if not globales:
        lineas.append("   Sin ventas - 0 unidades vendidas")
    lineas.append("")
    lineas.append("Por categoria:")
    lineas.extend(f"   {categoria}: {nombre} - {total} unidades" for categoria, nombre, total in por_categoria)
    return "\n".join(lineas)


def _respuesta_recomendaciones():
    reabastecer, bajar_precio = recomendaciones_rotacion()
    lineas = ["Productos que se estan vendiendo rapido - te recomiendo pedir mas:"]
    if reabastecer:
        for item in reabastecer:
            lineas.append(f"   {item['nombre']} ({item['nivel']}): se vendieron {item['vendidas']} unidades.")
            lineas.append(
                f"   Antes tenias {item['stock_actual'] + item['vendidas']}, "
                f"te recomiendo pedir al menos {item['pedir']} unidades mas."
            )
    else:
        lineas.append("No hay productos con ventas inusualmente altas por el momento.")

    lineas.append("")
    lineas.append("Productos sin ventas en los ultimos 4 dias - te recomiendo bajarles el precio:")
    if bajar_precio:
        for item in bajar_precio:
            lineas.append(f"   {item['nombre']}: precio actual {_formato_cop(item['precio_actual'])}.")
            lineas.append(
                f"   Costo al por mayor {_formato_cop(item['costo'])}. "
                f"Podrias bajarlo a {_formato_cop(item['sugerido'])}"
            )
            lineas.append(f"   y seguir ganando {_formato_cop(item['ganancia'])} por unidad.")
    else:
        lineas.append("Todos tus productos han tenido movimiento recientemente. Vas muy bien!")
    return "\n".join(lineas)


def _responder_comando(texto, permitir_pendientes=False):
    pendiente = None

    if not texto:
        return "Escribe una pregunta o comando.", pendiente

    if texto in SALUDOS or texto in {"menu", "ayuda", "comandos"}:
        return mensaje_inicio(), pendiente

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

        id_producto, nombre_db, stock, precio_detal, precio_mayorista = producto
        if stock < cantidad:
            return f"Stock insuficiente. Solo hay {stock} unidades de {nombre_db}."
        ganancia = (precio_detal - precio_mayorista) * cantidad
        respuesta = (
            "Confirmas esta venta?\n"
            f"Producto: {nombre_db}\n"
            f"Cantidad: {cantidad}\n"
            f"Stock actual: {stock} → quedara en {stock - cantidad}\n"
            f"Ganancia: {_formato_cop(ganancia)}\n"
            "Escribe sí para confirmar o no para cancelar."
        )
        if permitir_pendientes:
            pendiente = {"tipo": "venta", "id_producto": id_producto, "cantidad": cantidad}
            return respuesta, pendiente
        return respuesta

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
        categoria = categoria_existe(cat) or cat
        lineas = [
            f"   {n} (Talla {t}, {c}): {s} uds\n"
            f"   Precio detal: {_formato_cop(pd)} - Precio por mayor: {_formato_cop(pm)}"
            for n, t, c, s, pd, pm in productos
        ]
        return f"{categoria}\n" + "\n".join(lineas)

    categoria_directa = categoria_existe(texto)
    if categoria_directa:
        productos = productos_por_categoria_detalle(categoria_directa)
        lineas = [
            f"   {n} (Talla {t}, {c}): {s} uds\n"
            f"   Precio detal: {_formato_cop(pd)} - Precio por mayor: {_formato_cop(pm)}"
            for n, t, c, s, pd, pm in productos
        ]
        return f"{categoria_directa}\n" + "\n".join(lineas)

    if "productos en talla" in texto:
        talla = texto.replace("productos en talla", "").strip()
        if not talla:
            return "Indica la talla. Ejemplo: productos en talla M"
        pregunta_categoria = (
            f"En que categoria quieres buscar la talla {talla.upper()}? "
            f"Las categorias disponibles son: {_categorias_texto()}."
        )
        if permitir_pendientes:
            return pregunta_categoria, {"tipo": "talla", "valor": talla}
        return pregunta_categoria
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
        pregunta_categoria = (
            f"En que categoria quieres buscar el color {color}? "
            f"Las categorias disponibles son: {_categorias_texto()}."
        )
        if permitir_pendientes:
            return pregunta_categoria, {"tipo": "color", "valor": color}
        return pregunta_categoria
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
        cats = productos_por_categoria()
        lineas = [f"{cat}: {cant} productos" for cat, cant in cats]
        lineas.append(f"Total productos: {total_productos()}")
        return "\n".join(lineas)

    # VENTAS DEL DIA
    if "ventas de hoy" in texto:
        hoy = date.today().isoformat()
        ventas = ventas_del_dia(hoy)
        if not ventas:
            return f"No hay ventas registradas hoy ({_fecha_larga(hoy)})."
        lineas = [f"   {n}: {cant} uds - {_formato_cop(pv)} (ganancia {_formato_cop(g)})" for n, cant, pv, g, _ in ventas]
        return f"Ventas de hoy ({_fecha_larga(hoy)}):\n" + "\n".join(lineas)

    fecha_consulta = _parsear_fecha_ventas(texto)
    if fecha_consulta:
        ventas = venta_producto_por_fecha(fecha_consulta)
        if not ventas:
            return f"No se encontraron registros de ventas para el {_fecha_larga(fecha_consulta)}."
        total_ganancia = sum(g for _, _, _, g in ventas)
        lineas = [f"Ventas del dia {_fecha_larga(fecha_consulta)}:"]
        for nombre, cantidad, stock_restante, ganancia in ventas:
            lineas.extend([
                f"Producto: {nombre}",
                f"Cantidad vendida: {cantidad}",
                f"Stock restante: {stock_restante}",
                f"Ganancia: {_formato_cop(ganancia)}",
            ])
        if len(ventas) > 1:
            lineas.append(f"Total de ventas en este dia: {_formato_cop(total_ganancia)}")
        return "\n".join(lineas)

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
        return _respuesta_extremos(desc=True)

    if "producto menos vendido" in texto:
        return _respuesta_extremos(desc=False)

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

    if "recomendaciones" in texto or "recomendacion" in texto:
        return _respuesta_recomendaciones()

    # CERRAR DIA
    if "cerrar dia" in texto:
        r = cerrar_dia()
        respuesta = (
            f"Dia cerrado y guardado.\n"
            f"Fecha: {r['fecha']}\n"
            f"Ventas realizadas: {r['ventas']}\n"
            f"Ingresos del dia: {_formato_cop(r['ingresos'])} COP\n"
            f"Ganancias del dia: {_formato_cop(r['ganancias'])} COP\n"
            f"Producto top: {r['producto_top']}\n"
            f"Menos vendido: {r['producto_menos']}\n"
            f"Capital inmovilizado: {_formato_cop(r['capital'])} COP"
        )
        alerta = _alerta_stock_bajo()
        return f"{respuesta}\n\n{alerta}" if alerta else respuesta

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


class AsistenteInventario:
    def __init__(self):
        self.pendiente = None

    def responder(self, mensaje):
        require_openclaw_ready()
        texto = _normalizar_comandos(mensaje.lower().strip())

        if self.pendiente:
            respuesta = self._resolver_pendiente(texto)
            if respuesta is not None:
                return respuesta

        resultado = _responder_comando(texto, permitir_pendientes=True)
        if isinstance(resultado, tuple):
            respuesta, self.pendiente = resultado
            return respuesta
        self.pendiente = None
        return resultado

    def _resolver_pendiente(self, texto):
        pendiente = self.pendiente

        if pendiente["tipo"] == "venta":
            if texto in {"si", "sí", "s"}:
                self.pendiente = None
                try:
                    venta = registrar_venta(pendiente["id_producto"], pendiente["cantidad"])
                except ValueError as exc:
                    return str(exc)
                return (
                    "Venta registrada.\n"
                    f"Producto: {venta['nombre']}\n"
                    f"Cantidad: {venta['cantidad']}\n"
                    f"Stock restante: {venta['stock_restante']}\n"
                    f"Ganancia: {_formato_cop(venta['ganancia'])}"
                )
            if texto in {"no", "n", "cancelar"}:
                self.pendiente = None
                return "Venta cancelada."
            return "Escribe sí para confirmar o no para cancelar."

        if pendiente["tipo"] in {"talla", "color"}:
            categoria = categoria_existe(texto)
            if not categoria:
                return f"No encontre esa categoria. Las categorias disponibles son: {_categorias_texto()}."
            self.pendiente = None

            if pendiente["tipo"] == "talla":
                valor = pendiente["valor"]
                productos = buscar_por_talla_categoria(valor, categoria)
                if not productos:
                    return f"No hay productos de {categoria} en talla {valor.upper()}."
                lineas = [
                    f"   {n} ({c}): {s} uds\n"
                    f"   Precio detal: {_formato_cop(pd)} - Precio por mayor: {_formato_cop(pm)}"
                    for n, c, s, pd, pm in productos
                ]
                return f"{categoria} en talla {valor.upper()}\n" + "\n".join(lineas)

            valor = pendiente["valor"]
            productos = buscar_por_color_categoria(valor, categoria)
            if not productos:
                return f"No hay productos de {categoria} en color {valor}."
            lineas = [
                f"   {n} (Talla {t}): {s} uds\n"
                f"   Precio detal: {_formato_cop(pd)} - Precio por mayor: {_formato_cop(pm)}"
                for n, t, s, pd, pm in productos
            ]
            return f"{categoria} en color {valor}\n" + "\n".join(lineas)

        return None


_ASISTENTE_DEFAULT = AsistenteInventario()


def preguntar(mensaje):
    return _ASISTENTE_DEFAULT.responder(mensaje)


if __name__ == "__main__":
    openclaw_status = require_openclaw_ready()
    print(MENU)
    print(f"OpenClaw listo: {openclaw_status}")
    print(f"Hoy es {date.today().isoformat()}")

    while True:
        pregunta = input("Tu: ").strip()
        if pregunta.lower() == "salir":
            break
        if pregunta.lower() == "menu":
            print(MENU)
            continue
        print(preguntar(pregunta))
