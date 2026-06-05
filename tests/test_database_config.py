import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database


class DatabaseConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_env = {
            "MUNDO_MATERNO_DB_ENGINE": os.environ.get("MUNDO_MATERNO_DB_ENGINE"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "MUNDO_MATERNO_SQLITE_PATH": os.environ.get("MUNDO_MATERNO_SQLITE_PATH"),
        }

    def tearDown(self):
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_sqlite_engine_ignores_leftover_database_url(self):
        os.environ["MUNDO_MATERNO_DB_ENGINE"] = "sqlite"
        os.environ["DATABASE_URL"] = "postgresql://example.invalid/db"

        self.assertFalse(database.using_postgres())

    def test_relative_sqlite_path_resolves_from_project_root(self):
        os.environ["MUNDO_MATERNO_SQLITE_PATH"] = "inventario.db"

        self.assertEqual(database._sqlite_path(), Path(database.ROOT_DIR / "inventario.db").resolve())

    def test_missing_sqlite_database_fails_instead_of_creating_blank_file(self):
        os.environ["MUNDO_MATERNO_DB_ENGINE"] = "sqlite"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.db"
            os.environ["MUNDO_MATERNO_SQLITE_PATH"] = str(missing_path)

            with self.assertRaises(RuntimeError) as context:
                database.get_connection()

            self.assertFalse(missing_path.exists())
            self.assertIn("No encontre la base de datos SQLite", str(context.exception))

    def test_create_if_missing_allows_database_initialization(self):
        os.environ["MUNDO_MATERNO_DB_ENGINE"] = "sqlite"
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "new.db"
            os.environ["MUNDO_MATERNO_SQLITE_PATH"] = str(db_path)

            conn = database.get_connection(create_if_missing=True)
            conn.close()

            self.assertTrue(db_path.exists())


if __name__ == "__main__":
    unittest.main()
