import os
import sys
import unicodedata
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_connection

PALABRAS_IGNORADAS = {
    "agregar",
    "anotar",
    "crear",
    "hacer",
    "quiero",
    "registrar",
    "stock",
    "una",
    "unidades",
    "venta",
    "vender",
}


def _normalizar(texto: str):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def buscar_producto_inteligente(texto: str):
    conn = get_connection()
    c = conn.cursor()
    texto_limpio = texto.lower().strip()
    texto_normalizado = _normalizar(texto_limpio)
    palabras = [
        p
        for p in texto_normalizado.split()
        if len(p) >= 3 and p not in PALABRAS_IGNORADAS
    ]

    if len(texto_limpio) < 3 or not palabras:
        conn.close()
        return None

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

    c.execute("""
        SELECT id_producto, nombre, stock, precio_detal, precio_mayorista
        FROM Productos
        ORDER BY nombre ASC
    """)
    productos = c.fetchall()
    for producto in productos:
        nombre_normalizado = _normalizar(producto[1])
        if texto_normalizado in nombre_normalizado:
            conn.close()
            return producto

    for i in range(len(palabras) - 1):
        par = (palabras[i], palabras[i + 1])
        for producto in productos:
            nombre_normalizado = _normalizar(producto[1])
            if par[0] in nombre_normalizado and par[1] in nombre_normalizado:
                conn.close()
                return producto

    # 3. Buscar por palabra individual mas larga
    palabras_ordenadas = sorted(palabras, key=len, reverse=True)
    for palabra in palabras_ordenadas:
        for producto in productos:
            if palabra in _normalizar(producto[1]):
                conn.close()
                return producto

    conn.close()
    return None
