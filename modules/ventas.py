import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_connection

def registrar_venta(id_producto, cantidad):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT precio_detal, precio_mayorista, stock FROM Productos WHERE id_producto = ?", (id_producto,))
    producto = c.fetchone()

    if not producto:
        conn.close()
        return None, "Producto no encontrado"

    precio_detal, precio_mayorista, stock = producto

    if stock < cantidad:
        conn.close()
        return None, f"Stock insuficiente. Disponible: {stock}"

    ganancia = (precio_detal - precio_mayorista) * cantidad
    precio_venta = precio_detal * cantidad

    from datetime import date
    fecha_hoy = date.today().isoformat()

    c.execute("""
        INSERT INTO Ventas (id_producto, cantidad, fecha_venta, precio_venta, ganancia)
        VALUES (?, ?, ?, ?, ?)
    """, (id_producto, cantidad, fecha_hoy, precio_venta, ganancia))

    c.execute("UPDATE Productos SET stock = stock - ? WHERE id_producto = ?", (cantidad, id_producto))

    conn.commit()
    conn.close()
    return precio_venta, ganancia

def ventas_del_dia():
    conn = get_connection()
    c = conn.cursor()
    from datetime import date
    hoy = date.today().isoformat()
    c.execute("""
        SELECT p.nombre, v.cantidad, v.precio_venta, v.ganancia
        FROM Ventas v
        JOIN Productos p ON v.id_producto = p.id_producto
        WHERE v.fecha_venta = ?
    """, (hoy,))
    resultados = c.fetchall()
    conn.close()
    return resultados

def resumen_ventas():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT SUM(precio_venta), SUM(ganancia), COUNT(*)
        FROM Ventas
    """)
    resultado = c.fetchone()
    conn.close()
    return {
        "ingresos_totales": resultado[0] or 0.0,
        "ganancias_totales": resultado[1] or 0.0,
        "numero_ventas": resultado[2] or 0
    }