import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database


TABLES = ("Productos", "Ventas", "Historial_Mensual")


def fetch_rows(sqlite_path):
    source = sqlite3.connect(sqlite_path)
    try:
        rows = {}
        for table in TABLES:
            cursor = source.execute(f"SELECT * FROM {table}")
            rows[table] = cursor.fetchall()
        return rows
    finally:
        source.close()


def migrate(sqlite_path, truncate=False):
    if not database.using_postgres():
        raise RuntimeError("Configura DATABASE_URL antes de migrar a PostgreSQL.")

    rows = fetch_rows(sqlite_path)
    database.crear_base_de_datos()

    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        if truncate:
            cursor.execute("TRUNCATE TABLE Ventas, Historial_Mensual, Productos RESTART IDENTITY CASCADE")

        cursor.executemany(
            """INSERT INTO Productos VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (id_producto) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                categoria = EXCLUDED.categoria,
                talla = EXCLUDED.talla,
                color = EXCLUDED.color,
                precio_mayorista = EXCLUDED.precio_mayorista,
                precio_detal = EXCLUDED.precio_detal,
                stock = EXCLUDED.stock,
                fecha_ingreso = EXCLUDED.fecha_ingreso,
                proveedor = EXCLUDED.proveedor""",
            rows["Productos"],
        )

        cursor.executemany(
            """INSERT INTO Ventas (id_venta, id_producto, cantidad, fecha_venta, precio_venta, ganancia)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT (id_venta) DO UPDATE SET
                id_producto = EXCLUDED.id_producto,
                cantidad = EXCLUDED.cantidad,
                fecha_venta = EXCLUDED.fecha_venta,
                precio_venta = EXCLUDED.precio_venta,
                ganancia = EXCLUDED.ganancia""",
            rows["Ventas"],
        )

        cursor.executemany(
            """INSERT INTO Historial_Mensual VALUES (?,?,?,?,?,?,?)
            ON CONFLICT (mes) DO UPDATE SET
                ventas_totales = EXCLUDED.ventas_totales,
                ingresos = EXCLUDED.ingresos,
                ganancias = EXCLUDED.ganancias,
                producto_top = EXCLUDED.producto_top,
                producto_menos_vendido = EXCLUDED.producto_menos_vendido,
                capital_inmovilizado = EXCLUDED.capital_inmovilizado""",
            rows["Historial_Mensual"],
        )

        cursor.execute("""
            SELECT setval(
                pg_get_serial_sequence('ventas', 'id_venta'),
                CASE WHEN max_id IS NULL THEN 1 ELSE max_id END,
                max_id IS NOT NULL
            )
            FROM (SELECT MAX(id_venta) AS max_id FROM Ventas) AS venta_ids
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {table: len(table_rows) for table, table_rows in rows.items()}


def main():
    parser = argparse.ArgumentParser(description="Migrate Mundo Materno inventory data from SQLite to PostgreSQL.")
    parser.add_argument("--sqlite-path", default=os.path.join(ROOT, "inventario.db"))
    parser.add_argument("--truncate", action="store_true", help="Clear PostgreSQL tables before loading SQLite data.")
    args = parser.parse_args()

    counts = migrate(args.sqlite_path, truncate=args.truncate)
    print("Migracion completada:")
    for table, count in counts.items():
        print(f"- {table}: {count} fila(s)")


if __name__ == "__main__":
    main()
