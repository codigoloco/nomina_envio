"""
Controlador: Empleados.
Las vistas nunca llaman a EmployeeModel directamente; siempre pasan por aqui.
"""

from models.employee_model import EmployeeModel
from services.excel_reader import ExcelReader
from services.template_generator import TemplateGenerator


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

    @staticmethod
    def generar_plantilla(dest_path):
        """
        Genera el archivo .xlsx de plantilla para carga masiva de empleados.
        @param dest_path ruta donde se guardara el archivo
        """
        TemplateGenerator.generate_employee_template(dest_path)

    @staticmethod
    def importar_masivo(path):
        """
        Lee una plantilla de empleados y la inserta en la BD ignorando duplicados.
        @param path ruta al archivo .xlsx con los empleados
        @return tupla (insertados, duplicados)
        """
        registros = ExcelReader.read_employees_template(path)
        return EmployeeModel.bulk_insert(registros)
