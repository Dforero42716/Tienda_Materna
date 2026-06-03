import os
import sqlite3

from env_loader import load_env

load_env()

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")
DB_ENGINE = os.environ.get("MUNDO_MATERNO_DB_ENGINE", "sqlite").lower()
DATABASE_URL = os.environ.get("DATABASE_URL")


PRODUCTOS_INICIALES = [
    ("P001", "Blusa lactancia manga larga", "Blusas", "M", "Blanco", 28000, 55000, 12, "2025-05-01", "Textiles Mama"),
    ("P002", "Leggins embarazo cintura alta", "Leggins", "L", "Negro", 32000, 62000, 8, "2025-05-03", "ModaMater"),
    ("P003", "Vestido premama casual", "Vestidos", "S", "Rosado", 45000, 88000, 5, "2025-05-10", "Textiles Mama"),
    ("P004", "Camiseta algodon lactancia", "Camisetas", "M", "Gris", 22000, 42000, 20, "2025-05-12", "ModaMater"),
    ("P005", "Pijama maternidad dos piezas", "Pijamas", "XL", "Azul", 38000, 74000, 3, "2025-05-15", "BabyComfort"),
    ("P006", "Blusa lactancia botones", "Blusas", "S", "Beige", 26000, 52000, 15, "2025-05-01", "Textiles Mama"),
    ("P007", "Blusa premama estampada", "Blusas", "L", "Verde", 24000, 48000, 10, "2025-05-02", "ModaMater"),
    ("P008", "Blusa maternidad escote V", "Blusas", "M", "Negro", 27000, 53000, 7, "2025-05-03", "Textiles Mama"),
    ("P009", "Blusa algodon premama", "Blusas", "XL", "Blanco", 23000, 45000, 14, "2025-05-04", "BabyComfort"),
    ("P010", "Blusa lactancia cruzada", "Blusas", "S", "Rosado", 29000, 57000, 9, "2025-05-05", "ModaMater"),
    ("P011", "Leggins maternidad cortos", "Leggins", "M", "Gris", 30000, 58000, 11, "2025-05-06", "ModaMater"),
    ("P012", "Leggins premama termicos", "Leggins", "S", "Negro", 34000, 65000, 6, "2025-05-07", "Textiles Mama"),
    ("P013", "Leggins embarazo deportivos", "Leggins", "L", "Azul", 31000, 60000, 13, "2025-05-08", "BabyComfort"),
    ("P014", "Leggins maternidad largos", "Leggins", "XL", "Beige", 33000, 63000, 4, "2025-05-09", "ModaMater"),
    ("P015", "Leggins premama suaves", "Leggins", "M", "Rosado", 29000, 56000, 16, "2025-05-10", "Textiles Mama"),
    ("P016", "Vestido lactancia floral", "Vestidos", "M", "Floral", 47000, 92000, 7, "2025-05-11", "BabyComfort"),
    ("P017", "Vestido premama formal", "Vestidos", "L", "Negro", 50000, 98000, 4, "2025-05-12", "Textiles Mama"),
    ("P018", "Vestido maternidad playero", "Vestidos", "S", "Amarillo", 42000, 82000, 8, "2025-05-13", "ModaMater"),
    ("P019", "Vestido premama manga corta", "Vestidos", "XL", "Blanco", 44000, 86000, 5, "2025-05-14", "BabyComfort"),
    ("P020", "Vestido lactancia casual", "Vestidos", "M", "Verde", 46000, 90000, 6, "2025-05-15", "Textiles Mama"),
    ("P021", "Camiseta premama basica", "Camisetas", "S", "Blanco", 20000, 38000, 22, "2025-05-01", "ModaMater"),
    ("P022", "Camiseta maternidad rayas", "Camisetas", "M", "Azul", 21000, 40000, 18, "2025-05-02", "BabyComfort"),
    ("P023", "Camiseta lactancia sin mangas", "Camisetas", "L", "Negro", 19000, 37000, 25, "2025-05-03", "Textiles Mama"),
    ("P024", "Camiseta premama estampada", "Camisetas", "XL", "Rosado", 22000, 43000, 12, "2025-05-04", "ModaMater"),
    ("P025", "Camiseta algodon premama", "Camisetas", "S", "Gris", 20000, 39000, 20, "2025-05-05", "BabyComfort"),
    ("P026", "Pijama maternidad manga larga", "Pijamas", "M", "Rosado", 40000, 78000, 5, "2025-05-06", "BabyComfort"),
    ("P027", "Pijama lactancia botones", "Pijamas", "S", "Blanco", 37000, 72000, 7, "2025-05-07", "Textiles Mama"),
    ("P028", "Pijama premama algodon", "Pijamas", "L", "Azul", 39000, 76000, 4, "2025-05-08", "ModaMater"),
    ("P029", "Pijama maternidad corto", "Pijamas", "XL", "Beige", 36000, 70000, 6, "2025-05-09", "BabyComfort"),
    ("P030", "Pijama lactancia estampado", "Pijamas", "M", "Verde", 38000, 74000, 3, "2025-05-10", "Textiles Mama"),
    ("P031", "Sosten lactancia sin aros", "Ropa Interior", "M", "Beige", 25000, 48000, 15, "2025-05-01", "ModaMater"),
    ("P032", "Sosten maternidad deportivo", "Ropa Interior", "L", "Negro", 27000, 52000, 10, "2025-05-02", "BabyComfort"),
    ("P033", "Sosten lactancia encaje", "Ropa Interior", "S", "Blanco", 26000, 50000, 8, "2025-05-03", "Textiles Mama"),
    ("P034", "Sosten premama algodon", "Ropa Interior", "XL", "Rosado", 24000, 46000, 12, "2025-05-04", "ModaMater"),
    ("P035", "Faja postparto alta", "Ropa Interior", "M", "Beige", 35000, 68000, 9, "2025-05-05", "BabyComfort"),
    ("P036", "Panty maternidad algodon", "Ropa Interior", "L", "Negro", 18000, 35000, 20, "2025-05-06", "Textiles Mama"),
    ("P037", "Panty premama pack x3", "Ropa Interior", "M", "Surtido", 22000, 42000, 14, "2025-05-07", "ModaMater"),
    ("P038", "Faja embarazo soporte", "Ropa Interior", "S", "Beige", 33000, 65000, 6, "2025-05-08", "BabyComfort"),
    ("P039", "Sosten lactancia frontal", "Ropa Interior", "XL", "Blanco", 28000, 54000, 7, "2025-05-09", "Textiles Mama"),
    ("P040", "Panty postparto alta", "Ropa Interior", "L", "Negro", 20000, 38000, 16, "2025-05-10", "ModaMater"),
    ("P041", "Chaqueta maternidad polar", "Chaquetas", "M", "Gris", 55000, 108000, 4, "2025-05-11", "BabyComfort"),
    ("P042", "Chaqueta premama denim", "Chaquetas", "L", "Azul", 60000, 118000, 3, "2025-05-12", "Textiles Mama"),
    ("P043", "Cardigan maternidad largo", "Chaquetas", "S", "Beige", 48000, 94000, 6, "2025-05-13", "ModaMater"),
    ("P044", "Chaqueta lactancia botones", "Chaquetas", "XL", "Negro", 52000, 102000, 5, "2025-05-14", "BabyComfort"),
    ("P045", "Cardigan premama suave", "Chaquetas", "M", "Rosado", 46000, 90000, 7, "2025-05-15", "Textiles Mama"),
    ("P046", "Falda premama elastica", "Faldas", "M", "Negro", 28000, 54000, 10, "2025-05-01", "ModaMater"),
    ("P047", "Falda maternidad larga", "Faldas", "L", "Floral", 30000, 58000, 8, "2025-05-02", "BabyComfort"),
    ("P048", "Falda premama jean", "Faldas", "S", "Azul", 32000, 62000, 5, "2025-05-03", "Textiles Mama"),
    ("P049", "Falda maternidad casual", "Faldas", "XL", "Beige", 27000, 52000, 11, "2025-05-04", "ModaMater"),
    ("P050", "Falda premama plisada", "Faldas", "M", "Verde", 29000, 56000, 7, "2025-05-05", "BabyComfort"),
    ("P051", "Jean maternidad panel completo", "Jeans", "M", "Azul", 58000, 114000, 6, "2025-05-06", "Textiles Mama"),
    ("P052", "Jean premama skinny", "Jeans", "L", "Negro", 55000, 108000, 4, "2025-05-07", "ModaMater"),
    ("P053", "Jean maternidad wide leg", "Jeans", "S", "Azul claro", 60000, 118000, 3, "2025-05-08", "BabyComfort"),
    ("P054", "Jean premama panel bajo", "Jeans", "XL", "Gris", 52000, 102000, 7, "2025-05-09", "Textiles Mama"),
    ("P055", "Jean maternidad recto", "Jeans", "M", "Negro", 56000, 110000, 5, "2025-05-10", "ModaMater"),
    ("P056", "Conjunto lactancia blusa+leggins", "Conjuntos", "M", "Rosado", 62000, 122000, 4, "2025-05-11", "BabyComfort"),
    ("P057", "Conjunto premama casual", "Conjuntos", "L", "Verde", 58000, 114000, 5, "2025-05-12", "Textiles Mama"),
    ("P058", "Conjunto maternidad deportivo", "Conjuntos", "S", "Negro", 55000, 108000, 6, "2025-05-13", "ModaMater"),
    ("P059", "Conjunto premama verano", "Conjuntos", "XL", "Blanco", 60000, 118000, 3, "2025-05-14", "BabyComfort"),
    ("P060", "Conjunto lactancia pijama", "Conjuntos", "M", "Azul", 57000, 112000, 7, "2025-05-15", "Textiles Mama"),
    ("P061", "Blusa premama lino", "Blusas", "M", "Blanco", 25000, 49000, 13, "2025-05-16", "ModaMater"),
    ("P062", "Blusa maternidad tiras", "Blusas", "S", "Amarillo", 23000, 45000, 17, "2025-05-17", "BabyComfort"),
    ("P063", "Blusa lactancia rayas", "Blusas", "L", "Azul", 26000, 51000, 9, "2025-05-18", "Textiles Mama"),
    ("P064", "Blusa premama bohemia", "Blusas", "XL", "Floral", 28000, 54000, 6, "2025-05-19", "ModaMater"),
    ("P065", "Blusa maternidad casual", "Blusas", "M", "Gris", 24000, 47000, 11, "2025-05-20", "BabyComfort"),
    ("P066", "Leggins maternidad capri", "Leggins", "M", "Negro", 31000, 60000, 8, "2025-05-16", "Textiles Mama"),
    ("P067", "Leggins premama fitness", "Leggins", "S", "Morado", 33000, 64000, 5, "2025-05-17", "ModaMater"),
    ("P068", "Leggins maternidad estampados", "Leggins", "L", "Floral", 30000, 58000, 10, "2025-05-18", "BabyComfort"),
    ("P069", "Leggins embarazo suaves", "Leggins", "XL", "Gris", 32000, 62000, 7, "2025-05-19", "Textiles Mama"),
    ("P070", "Leggins premama control", "Leggins", "M", "Beige", 34000, 66000, 4, "2025-05-20", "ModaMater"),
    ("P071", "Vestido maternidad noche", "Vestidos", "M", "Negro", 52000, 102000, 3, "2025-05-16", "BabyComfort"),
    ("P072", "Vestido premama midi", "Vestidos", "L", "Rosado", 48000, 94000, 5, "2025-05-17", "Textiles Mama"),
    ("P073", "Vestido lactancia wrap", "Vestidos", "S", "Verde", 45000, 88000, 7, "2025-05-18", "ModaMater"),
    ("P074", "Vestido maternidad playa", "Vestidos", "XL", "Amarillo", 43000, 84000, 6, "2025-05-19", "BabyComfort"),
    ("P075", "Vestido premama lunares", "Vestidos", "M", "Blanco", 46000, 90000, 4, "2025-05-20", "Textiles Mama"),
    ("P076", "Camiseta maternidad polo", "Camisetas", "M", "Blanco", 21000, 41000, 19, "2025-05-16", "ModaMater"),
    ("P077", "Camiseta premama cuello V", "Camisetas", "S", "Negro", 20000, 39000, 23, "2025-05-17", "BabyComfort"),
    ("P078", "Camiseta lactancia bolsillo", "Camisetas", "L", "Gris", 22000, 43000, 15, "2025-05-18", "Textiles Mama"),
    ("P079", "Camiseta maternidad larga", "Camisetas", "XL", "Azul", 21000, 41000, 11, "2025-05-19", "ModaMater"),
    ("P080", "Camiseta premama tie-dye", "Camisetas", "M", "Surtido", 23000, 45000, 8, "2025-05-20", "BabyComfort"),
    ("P081", "Pijama maternidad verano", "Pijamas", "M", "Amarillo", 36000, 70000, 5, "2025-05-16", "Textiles Mama"),
    ("P082", "Pijama lactancia tirantes", "Pijamas", "S", "Rosado", 35000, 68000, 8, "2025-05-17", "ModaMater"),
    ("P083", "Pijama premama invierno", "Pijamas", "L", "Azul", 42000, 82000, 3, "2025-05-18", "BabyComfort"),
    ("P084", "Pijama maternidad polar", "Pijamas", "XL", "Gris", 44000, 86000, 2, "2025-05-19", "Textiles Mama"),
    ("P085", "Pijama lactancia flores", "Pijamas", "M", "Floral", 38000, 74000, 6, "2025-05-20", "ModaMater"),
    ("P086", "Sosten lactancia push-up", "Ropa Interior", "M", "Negro", 29000, 56000, 9, "2025-05-16", "BabyComfort"),
    ("P087", "Faja postparto completa", "Ropa Interior", "L", "Beige", 38000, 74000, 5, "2025-05-17", "Textiles Mama"),
    ("P088", "Panty maternidad encaje", "Ropa Interior", "S", "Blanco", 19000, 37000, 18, "2025-05-18", "ModaMater"),
    ("P089", "Sosten premama comodidad", "Ropa Interior", "XL", "Rosado", 25000, 48000, 10, "2025-05-19", "BabyComfort"),
    ("P090", "Faja embarazo lumbar", "Ropa Interior", "M", "Beige", 36000, 70000, 4, "2025-05-20", "Textiles Mama"),
]


class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        return self.cursor.execute(query.replace("?", "%s"), params)

    def executemany(self, query, params):
        return self.cursor.executemany(query.replace("?", "%s"), params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        return self.cursor.close()


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return PostgresCursor(self.connection.cursor())

    def commit(self):
        return self.connection.commit()

    def rollback(self):
        return self.connection.rollback()

    def close(self):
        return self.connection.close()


def using_postgres():
    return DB_ENGINE in {"postgres", "postgresql"} or bool(DATABASE_URL)


def get_connection():
    if using_postgres():
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Instala psycopg para usar PostgreSQL: pip install 'psycopg[binary]'") from exc

        if not DATABASE_URL:
            raise RuntimeError("Configura DATABASE_URL para usar PostgreSQL.")
        return PostgresConnection(psycopg.connect(DATABASE_URL))

    return sqlite3.connect(DB_PATH)


def crear_base_de_datos():
    conn = get_connection()
    c = conn.cursor()

    if using_postgres():
        c.execute("""CREATE TABLE IF NOT EXISTS Productos (
            id_producto TEXT PRIMARY KEY,
            nombre TEXT,
            categoria TEXT,
            talla TEXT,
            color TEXT,
            precio_mayorista DOUBLE PRECISION,
            precio_detal DOUBLE PRECISION,
            stock INTEGER,
            fecha_ingreso TEXT,
            proveedor TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Ventas (
            id_venta SERIAL PRIMARY KEY,
            id_producto TEXT REFERENCES Productos(id_producto),
            cantidad INTEGER,
            fecha_venta TEXT,
            precio_venta DOUBLE PRECISION,
            ganancia DOUBLE PRECISION
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Historial_Mensual (
            mes TEXT PRIMARY KEY,
            ventas_totales INTEGER,
            ingresos DOUBLE PRECISION,
            ganancias DOUBLE PRECISION,
            producto_top TEXT,
            producto_menos_vendido TEXT,
            capital_inmovilizado DOUBLE PRECISION
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Dia_Operativo (
            fecha TEXT PRIMARY KEY,
            inicio TEXT,
            cierre TEXT,
            capital_inicial DOUBLE PRECISION,
            capital_final DOUBLE PRECISION,
            ventas_iniciales INTEGER,
            ventas_finales INTEGER,
            estado TEXT
        )""")

        c.executemany("""INSERT INTO Productos VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_producto) DO NOTHING""", PRODUCTOS_INICIALES)
    else:
        c.execute("""CREATE TABLE IF NOT EXISTS Productos (
            id_producto TEXT PRIMARY KEY,
            nombre TEXT,
            categoria TEXT,
            talla TEXT,
            color TEXT,
            precio_mayorista REAL,
            precio_detal REAL,
            stock INTEGER,
            fecha_ingreso TEXT,
            proveedor TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto TEXT,
            cantidad INTEGER,
            fecha_venta TEXT,
            precio_venta REAL,
            ganancia REAL,
            FOREIGN KEY (id_producto) REFERENCES Productos(id_producto)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Historial_Mensual (
            mes TEXT PRIMARY KEY,
            ventas_totales INTEGER,
            ingresos REAL,
            ganancias REAL,
            producto_top TEXT,
            producto_menos_vendido TEXT,
            capital_inmovilizado REAL
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS Dia_Operativo (
            fecha TEXT PRIMARY KEY,
            inicio TEXT,
            cierre TEXT,
            capital_inicial REAL,
            capital_final REAL,
            ventas_iniciales INTEGER,
            ventas_finales INTEGER,
            estado TEXT
        )""")

        c.executemany("""INSERT OR IGNORE INTO Productos VALUES (?,?,?,?,?,?,?,?,?,?)""", PRODUCTOS_INICIALES)

    conn.commit()
    conn.close()
    print(f"Base de datos lista con {len(PRODUCTOS_INICIALES)} productos.")


if __name__ == "__main__":
    crear_base_de_datos()
