"""
Modelo: Empleado.
Encapsula todo el SQL relacionado con la tabla 'empleados'.
No conoce nada de PyQt ni de la interfaz -> puede reutilizarse/testearse
de forma aislada.
"""

from models.database import get_connection


class EmployeeModel:

    @staticmethod
    def add(cedula, nombre, telefono, correo):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO empleados (cedula, nombre, telefono, correo) VALUES (?, ?, ?, ?)",
                (cedula.strip(), nombre.strip(), telefono.strip(), correo.strip())
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(emp_id, cedula, nombre, telefono, correo):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE empleados SET cedula=?, nombre=?, telefono=?, correo=? WHERE id=?",
                (cedula.strip(), nombre.strip(), telefono.strip(), correo.strip(), emp_id)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(emp_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM empleados WHERE id=?", (emp_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM empleados ORDER BY nombre").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_cedula(cedula):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM empleados WHERE cedula = ?", (str(cedula).strip(),)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
