"""
Conexión e inicialización de la base de datos SQLite.
Esta es la única pieza que sabe cómo conectarse físicamente a la BD;
los modelos (EmployeeModel, EnvioModel) la usan para ejecutar SQL.
"""

import sqlite3
import os

# nomina.db queda en la raíz del proyecto (un nivel arriba de /models)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "nomina.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            telefono TEXT,
            correo TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER,
            cedula TEXT,
            nombre TEXT,
            correo TEXT,
            periodo TEXT,
            monto TEXT,
            asunto TEXT,
            fecha_envio TEXT NOT NULL,
            estado TEXT NOT NULL,
            detalle TEXT,
            FOREIGN KEY (empleado_id) REFERENCES empleados(id)
        )
    """)
    conn.commit()
    conn.close()
