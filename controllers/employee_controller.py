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

    @staticmethod
    def detectar_no_registrados(filas_excel: list) -> list:
        """
        Dada una lista de filas leídas del Excel, compara contra las cédulas registradas
        en la base de datos y retorna los empleados con cédula válida que no constan en la BD.
        @return lista de dicts: [{'cedula': ..., 'nombre': ...}] sin duplicados.
        """
        if not filas_excel:
            return []

        try:
            cedulas_bd = EmployeeModel.obtener_cedulas_registradas()
        except Exception:
            return []

        no_registrados = []
        cedulas_vistas = set()

        for fila in filas_excel:
            if not isinstance(fila, dict):
                continue

            # Localizar valor de cédula
            cedula_raw = ""
            for k in ("cedula", "Cedula", "ci", "CI", "c_i", "documento"):
                if k in fila and fila[k]:
                    cedula_raw = str(fila[k]).strip()
                    break

            if not cedula_raw or cedula_raw.upper() in ("N/A", "NAN", "NONE", "0"):
                continue

            # Limpiar dígitos si aplica
            cedula_limpia = "".join(c for c in cedula_raw if c.isdigit())
            if not cedula_limpia:
                cedula_limpia = cedula_raw

            if cedula_limpia in cedulas_vistas:
                continue

            # Verificar si existe en la BD
            if cedula_limpia not in cedulas_bd and cedula_raw not in cedulas_bd:
                # Obtener nombre / encargado
                nombre = ""
                for k in ("nombre", "Encargado", "encargado", "nombre_encargado", "Nombre"):
                    if k in fila and fila[k]:
                        nombre = str(fila[k]).strip()
                        break

                cedulas_vistas.add(cedula_limpia)
                no_registrados.append({
                    "cedula": cedula_limpia,
                    "nombre": nombre or "Desconocido"
                })

        return no_registrados
