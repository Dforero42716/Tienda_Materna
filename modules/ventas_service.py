import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_connection
from datetime import date

def buscar_producto_por_nombre(nombre: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id_producto, nombre, stock, precio_detal, precio_mayorista
        FROM Productos
        WHERE LOWER(nombre) LIKE ?
        LIMIT 1
    """, (f"%{nombre.lower()}%",))
    resultado = c.fetchone()
    conn.close()
    return resultado

def actualizar_stock(id_producto: str, nuevo_stock: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE Productos SET stock = ? WHERE id_producto = ?", (nuevo_stock, id_producto))
    conn.commit()
    conn.close()

def agregar_stock(id_producto: str, cantidad: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE Productos SET stock = stock + ? WHERE id_producto = ?", (cantidad, id_producto))
    conn.commit()
    conn.close()

def registrar_venta(id_producto: str, cantidad: int, precio_detal: float, precio_mayorista: float):
    conn = get_connection()
    c = conn.cursor()
    precio_venta = precio_detal * cantidad
    ganancia = (precio_detal - precio_mayorista) * cantidad
    c.execute("""
        INSERT INTO Ventas (id_producto, cantidad, fecha_venta, precio_venta, ganancia)
        VALUES (?, ?, ?, ?, ?)
    """, (id_producto, cantidad, date.today().isoformat(), precio_venta, ganancia))
    conn.commit()
    conn.close()
    return ganancia

def buscar_similares(texto: str):
    conn = get_connection()
    c = conn.cursor()
    palabras = [p for p in texto.lower().split() if len(p) >= 3]
    resultados = []
    for palabra in palabras:
        c.execute("""
            SELECT nombre, talla, color, stock, precio_detal
            FROM Productos
            WHERE LOWER(nombre) LIKE ?
            LIMIT 5
        """, (f"%{palabra}%",))
        filas = c.fetchall()
        for fila in filas:
            if fila not in resultados:
                resultados.append(fila)
    conn.close()
    return resultados[:5]