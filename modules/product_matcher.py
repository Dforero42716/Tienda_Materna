import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_connection

def buscar_producto_inteligente(texto: str):
    conn = get_connection()
    c = conn.cursor()
    texto_limpio = texto.lower().strip()

    # 1. Buscar frase completa
    c.execute("""
        SELECT id_producto, nombre, stock, precio_detal, precio_mayorista
        FROM Productos
        WHERE LOWER(nombre) LIKE ?
        LIMIT 1
    """, (f"%{texto_limpio}%",))
    resultado = c.fetchone()
    if resultado:
        conn.close()
        return resultado

    # 2. Buscar por combinacion de dos palabras
    palabras = [p for p in texto_limpio.split() if len(p) >= 3]
    for i in range(len(palabras) - 1):
        par = f"%{palabras[i]}%{palabras[i+1]}%"
        c.execute("""
            SELECT id_producto, nombre, stock, precio_detal, precio_mayorista
            FROM Productos
            WHERE LOWER(nombre) LIKE ?
            LIMIT 1
        """, (par,))
        resultado = c.fetchone()
        if resultado:
            conn.close()
            return resultado

    # 3. Buscar por palabra individual mas larga
    palabras_ordenadas = sorted(palabras, key=len, reverse=True)
    for palabra in palabras_ordenadas:
        c.execute("""
            SELECT id_producto, nombre, stock, precio_detal, precio_mayorista
            FROM Productos
            WHERE LOWER(nombre) LIKE ?
            LIMIT 1
        """, (f"%{palabra}%",))
        resultado = c.fetchone()
        if resultado:
            conn.close()
            return resultado

    conn.close()
    return None