"""
Controlador: Empleados.
Las vistas (main_window, employee_dialog) nunca llaman a EmployeeModel
directamente; siempre pasan por aquí. Esto permite, por ejemplo, agregar
validaciones o reglas de negocio sin tocar la interfaz ni el modelo.
"""

from models.employee_model import EmployeeModel


class EmployeeController:

    @staticmethod
    def listar_empleados():
        return EmployeeModel.get_all()

    @staticmethod
    def buscar_por_cedula(cedula):
        return EmployeeModel.get_by_cedula(cedula)

    @staticmethod
    def crear_empleado(cedula, nombre, telefono, correo):
        EmployeeModel.add(cedula, nombre, telefono, correo)

    @staticmethod
    def actualizar_empleado(emp_id, cedula, nombre, telefono, correo):
        EmployeeModel.update(emp_id, cedula, nombre, telefono, correo)

    @staticmethod
    def eliminar_empleado(emp_id):
        EmployeeModel.delete(emp_id)
