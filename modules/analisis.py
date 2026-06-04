import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_connection
from datetime import date, datetime, timedelta

ROTACION_NIVELES = (
    ("Alta", 6, 30),
    ("Media alta", 4, 20),
    ("Media", 2, 10),
    ("Media baja", 1, 4),
    ("Baja", 0, 1),
)

def stock_total():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(stock) FROM Productos")
    resultado = c.fetchone()[0]
    conn.close()
    return resultado or 0

def productos_bajo_stock(limite=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id_producto, nombre, stock
        FROM Productos
        WHERE stock <= ?
        ORDER BY stock ASC
    """, (limite,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def capital_inmovilizado():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(stock * precio_mayorista) FROM Productos")
    resultado = c.fetchone()[0]
    conn.close()
    return resultado or 0.0

def inventario_completo():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id_producto, nombre, talla, color, stock, precio_detal
        FROM Productos
        ORDER BY nombre ASC
    """)
    resultados = c.fetchall()
    conn.close()
    return resultados

def total_productos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Productos")
    resultado = c.fetchone()[0]
    conn.close()
    return resultado or 0

def stock_bajo(limite=2):
    return productos_bajo_stock(limite)

def categorias_disponibles():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT categoria FROM Productos ORDER BY categoria ASC")
    resultados = [row[0] for row in c.fetchall()]
    conn.close()
    return resultados

def productos_agotados():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id_producto, nombre FROM Productos WHERE stock = 0")
    resultados = c.fetchall()
    conn.close()
    return resultados

def producto_mas_caro():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT nombre, precio_detal FROM Productos ORDER BY precio_detal DESC LIMIT 1")
    resultado = c.fetchone()
    conn.close()
    return resultado or ("Ninguno", 0)

def producto_mas_barato():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT nombre, precio_detal FROM Productos ORDER BY precio_detal ASC LIMIT 1")
    resultado = c.fetchone()
    conn.close()
    return resultado or ("Ninguno", 0)

def valor_total_inventario():
    return capital_inmovilizado()

def productos_por_categoria():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT categoria, COUNT(*) as cantidad
        FROM Productos
        GROUP BY categoria
        ORDER BY cantidad DESC
    """)
    resultados = c.fetchall()
    conn.close()
    return resultados

def proveedor_con_mas_productos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT proveedor, COUNT(*) as cantidad
        FROM Productos
        GROUP BY proveedor
        ORDER BY cantidad DESC
        LIMIT 1
    """)
    resultado = c.fetchone()
    conn.close()
    return resultado or ("Ninguno", 0)

def productos_por_categoria_detalle(categoria: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, talla, color, stock, precio_detal, precio_mayorista
        FROM Productos
        WHERE LOWER(categoria) = ?
        ORDER BY nombre ASC
    """, (categoria.lower(),))
    resultados = c.fetchall()
    conn.close()
    return resultados

def categoria_existe(categoria: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT categoria FROM Productos WHERE LOWER(categoria) = ? LIMIT 1", (categoria.lower(),))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def top_mas_stock(limite=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, talla, color, stock
        FROM Productos
        ORDER BY stock DESC
        LIMIT ?
    """, (limite,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def top_menos_stock(limite=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, talla, color, stock
        FROM Productos
        WHERE stock > 0
        ORDER BY stock ASC
        LIMIT ?
    """, (limite,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def buscar_por_talla(talla: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, categoria, color, stock, precio_detal
        FROM Productos
        WHERE LOWER(talla) = ?
        ORDER BY categoria ASC
    """, (talla.lower(),))
    resultados = c.fetchall()
    conn.close()
    return resultados

def buscar_por_talla_categoria(talla: str, categoria: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, color, stock, precio_detal, precio_mayorista
        FROM Productos
        WHERE LOWER(talla) = ? AND LOWER(categoria) = ?
        ORDER BY nombre ASC
    """, (talla.lower(), categoria.lower()))
    resultados = c.fetchall()
    conn.close()
    return resultados

def buscar_por_color(color: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, categoria, talla, stock, precio_detal
        FROM Productos
        WHERE LOWER(color) LIKE ?
        ORDER BY categoria ASC
    """, (f"%{color.lower()}%",))
    resultados = c.fetchall()
    conn.close()
    return resultados

def buscar_por_color_categoria(color: str, categoria: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, talla, stock, precio_detal, precio_mayorista
        FROM Productos
        WHERE LOWER(color) LIKE ? AND LOWER(categoria) = ?
        ORDER BY nombre ASC
    """, (f"%{color.lower()}%", categoria.lower()))
    resultados = c.fetchall()
    conn.close()
    return resultados

def buscar_por_proveedor(proveedor: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, categoria, talla, color, stock, precio_detal
        FROM Productos
        WHERE LOWER(proveedor) LIKE ?
        ORDER BY nombre ASC
    """, (f"%{proveedor.lower()}%",))
    resultados = c.fetchall()
    conn.close()
    return resultados

def productos_por_rango_precio(minimo: float, maximo: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT nombre, categoria, talla, color, stock, precio_detal
        FROM Productos
        WHERE precio_detal BETWEEN ? AND ?
        ORDER BY precio_detal ASC
    """, (minimo, maximo))
    resultados = c.fetchall()
    conn.close()
    return resultados

def ventas_del_dia(fecha: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.nombre, v.cantidad, v.precio_venta, v.ganancia, v.fecha_venta
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
        ORDER BY v.id_venta ASC
    """, (fecha,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def venta_producto_por_fecha(fecha: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.nombre, v.cantidad, p.stock, v.ganancia
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
        ORDER BY v.id_venta ASC
    """, (fecha,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def ganancias_totales():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(ganancia), SUM(precio_venta), COUNT(*) FROM Ventas")
    resultado = c.fetchone()
    conn.close()
    return {
        "ganancias": resultado[0] or 0.0,
        "ingresos": resultado[1] or 0.0,
        "ventas": resultado[2] or 0
    }

def producto_mas_vendido():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.nombre, SUM(v.cantidad) as total
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        GROUP BY v.id_producto
        ORDER BY total DESC
        LIMIT 1
    """)
    resultado = c.fetchone()
    conn.close()
    return resultado or ("Sin ventas", 0)

def productos_vendidos_extremos(desc=True):
    orden = "DESC" if desc else "ASC"
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"""
        WITH totales AS (
            SELECT p.id_producto, p.nombre, p.categoria, COALESCE(SUM(v.cantidad), 0) AS total
            FROM Productos p
            LEFT JOIN Ventas v ON v.id_producto = p.id_producto
            GROUP BY p.id_producto, p.nombre, p.categoria
        )
        SELECT nombre, categoria, total
        FROM totales
        WHERE total = (SELECT {'MAX' if desc else 'MIN'}(total) FROM totales)
        ORDER BY nombre ASC
    """)
    globales = c.fetchall()

    c.execute(f"""
        WITH totales AS (
            SELECT p.id_producto, p.nombre, p.categoria, COALESCE(SUM(v.cantidad), 0) AS total
            FROM Productos p
            LEFT JOIN Ventas v ON v.id_producto = p.id_producto
            GROUP BY p.id_producto, p.nombre, p.categoria
        ),
        extremos AS (
            SELECT categoria, {'MAX' if desc else 'MIN'}(total) AS extremo
            FROM totales
            GROUP BY categoria
        )
        SELECT t.categoria, t.nombre, t.total
        FROM totales t
        JOIN extremos e ON e.categoria = t.categoria AND e.extremo = t.total
        ORDER BY t.categoria ASC, t.nombre ASC
    """)
    por_categoria = c.fetchall()
    conn.close()
    return globales, por_categoria

def historial_semana():
    conn = get_connection()
    c = conn.cursor()
    desde = (date.today() - timedelta(days=7)).isoformat()
    c.execute("""
        SELECT DISTINCT fecha_venta
        FROM Ventas
        WHERE fecha_venta >= ?
        ORDER BY fecha_venta DESC
    """, (desde,))
    fechas = [row[0] for row in c.fetchall()]
    conn.close()
    return fechas

def alertas_reposicion():
    conn = get_connection()
    c = conn.cursor()
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=7)).isoformat()

    c.execute("""
        SELECT p.nombre, p.id_producto, SUM(v.cantidad) as total_hoy
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
        GROUP BY v.id_producto
        HAVING total_hoy >= 3
    """, (hoy,))
    demanda_alta_hoy = c.fetchall()

    c.execute("""
        SELECT p.nombre, p.id_producto, SUM(v.cantidad) as total_semana
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta >= ?
        GROUP BY v.id_producto
        HAVING total_semana >= 10
    """, (desde,))
    demanda_alta_semana = c.fetchall()

    c.execute("""
        SELECT p.nombre, p.precio_detal, p.precio_mayorista, p.stock
        FROM Productos p
        WHERE p.id_producto NOT IN (SELECT DISTINCT id_producto FROM Ventas)
        AND p.stock > 5
        ORDER BY p.stock DESC
        LIMIT 5
    """)
    sin_ventas = c.fetchall()

    conn.close()
    return demanda_alta_hoy, demanda_alta_semana, sin_ventas

def recomendaciones_rotacion():
    conn = get_connection()
    c = conn.cursor()
    hoy = date.today()
    desde_semana = (hoy - timedelta(days=6)).isoformat()
    desde_estancado = (hoy - timedelta(days=3)).isoformat()

    c.execute("""
        SELECT p.nombre, p.stock, COALESCE(SUM(v.cantidad), 0) AS semana
        FROM Productos p
        LEFT JOIN Ventas v ON v.id_producto = p.id_producto AND v.fecha_venta >= ?
        GROUP BY p.id_producto, p.nombre, p.stock
        ORDER BY semana DESC, p.nombre ASC
    """, (desde_semana,))
    filas_semana = c.fetchall()

    c.execute("""
        SELECT p.nombre, p.precio_detal, p.precio_mayorista
        FROM Productos p
        WHERE NOT EXISTS (
            SELECT 1
            FROM Ventas v
            WHERE v.id_producto = p.id_producto AND v.fecha_venta >= ?
        )
        ORDER BY p.nombre ASC
    """, (desde_estancado,))
    estancados = c.fetchall()
    conn.close()

    reabastecer = []
    for nombre, stock, semana in filas_semana:
        por_dia = semana / 7
        nivel = "Baja"
        for nombre_nivel, diario_min, semanal_min in ROTACION_NIVELES:
            if por_dia >= diario_min or semana >= semanal_min:
                nivel = nombre_nivel
                break
        if nivel in {"Alta", "Media alta"}:
            reabastecer.append({
                "nombre": nombre,
                "stock_actual": stock,
                "vendidas": semana,
                "nivel": nivel,
                "pedir": semana,
            })

    bajar_precio = []
    for nombre, precio_detal, precio_mayorista in estancados:
        sugerido = max(precio_mayorista + 2000, precio_mayorista * 1.10)
        sugerido = min(precio_detal, sugerido)
        ganancia = sugerido - precio_mayorista
        bajar_precio.append({
            "nombre": nombre,
            "precio_actual": precio_detal,
            "costo": precio_mayorista,
            "sugerido": sugerido,
            "ganancia": ganancia,
        })

    return reabastecer, bajar_precio

def iniciar_dia():
    conn = get_connection()
    c = conn.cursor()
    hoy = date.today().isoformat()
    ahora = datetime.now().isoformat(timespec="seconds")

    c.execute("SELECT SUM(stock * precio_mayorista) FROM Productos")
    capital = c.fetchone()[0] or 0.0

    c.execute("SELECT COUNT(*) FROM Ventas WHERE fecha_venta = ?", (hoy,))
    ventas_iniciales = c.fetchone()[0] or 0

    c.execute("SELECT fecha, inicio, estado FROM Dia_Operativo WHERE fecha = ?", (hoy,))
    existe = c.fetchone()

    if existe:
        conn.close()
        return {
            "fecha": existe[0],
            "inicio": existe[1],
            "estado": existe[2],
            "capital_inicial": capital,
            "ventas_iniciales": ventas_iniciales,
            "ya_existia": True,
        }

    c.execute("""
        INSERT INTO Dia_Operativo (
            fecha, inicio, cierre, capital_inicial, capital_final,
            ventas_iniciales, ventas_finales, estado
        )
        VALUES (?, ?, NULL, ?, NULL, ?, NULL, ?)
    """, (hoy, ahora, capital, ventas_iniciales, "abierto"))

    conn.commit()
    conn.close()
    return {
        "fecha": hoy,
        "inicio": ahora,
        "estado": "abierto",
        "capital_inicial": capital,
        "ventas_iniciales": ventas_iniciales,
        "ya_existia": False,
    }

def cerrar_dia():
    conn = get_connection()
    c = conn.cursor()
    hoy = date.today().isoformat()
    ahora = datetime.now().isoformat(timespec="seconds")

    c.execute("""
        SELECT COUNT(*), SUM(precio_venta), SUM(ganancia)
        FROM Ventas
        WHERE fecha_venta = ?
    """, (hoy,))
    ventas, ingresos, ganancias = c.fetchone()
    ventas = ventas or 0
    ingresos = ingresos or 0.0
    ganancias = ganancias or 0.0

    c.execute("""
        SELECT p.nombre, SUM(v.cantidad) as total
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
        GROUP BY v.id_producto
        ORDER BY total DESC
        LIMIT 1
    """, (hoy,))
    top = c.fetchone()
    producto_top = top[0] if top else "Sin ventas"

    c.execute("""
        SELECT p.nombre, SUM(v.cantidad) as total
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
        GROUP BY v.id_producto
        ORDER BY total ASC
        LIMIT 1
    """, (hoy,))
    menos = c.fetchone()
    producto_menos = menos[0] if menos else "Sin ventas"

    c.execute("SELECT SUM(stock * precio_mayorista) FROM Productos")
    capital = c.fetchone()[0] or 0.0

    c.execute("SELECT mes FROM Historial_Mensual WHERE mes = ?", (hoy,))
    existe = c.fetchone()

    if existe:
        c.execute("""
            UPDATE Historial_Mensual
            SET ventas_totales=?, ingresos=?, ganancias=?,
                producto_top=?, producto_menos_vendido=?, capital_inmovilizado=?
            WHERE mes=?
        """, (ventas, ingresos, ganancias, producto_top, producto_menos, capital, hoy))
    else:
        c.execute("""
            INSERT INTO Historial_Mensual
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (hoy, ventas, ingresos, ganancias, producto_top, producto_menos, capital))

    c.execute("SELECT fecha FROM Dia_Operativo WHERE fecha = ?", (hoy,))
    dia_existe = c.fetchone()
    if dia_existe:
        c.execute("""
            UPDATE Dia_Operativo
            SET cierre=?, capital_final=?, ventas_finales=?, estado=?
            WHERE fecha=?
        """, (ahora, capital, ventas, "cerrado", hoy))
    else:
        c.execute("""
            INSERT INTO Dia_Operativo (
                fecha, inicio, cierre, capital_inicial, capital_final,
                ventas_iniciales, ventas_finales, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (hoy, ahora, ahora, capital, capital, 0, ventas, "cerrado"))

    conn.commit()
    conn.close()

    return {
        "fecha": hoy,
        "ventas": ventas,
        "ingresos": ingresos,
        "ganancias": ganancias,
        "producto_top": producto_top,
        "producto_menos": producto_menos,
        "capital": capital
    }
