"""
Controlador: Mensajes Masivos.
Orquesta la consulta de destinatarios (desde el historial de envíos o desde la lista de empleados)
para la vista de Mensajes Masivos, respetando la arquitectura MVC.
"""

from models.envio_model import EnvioModel
from models.employee_model import EmployeeModel


class MassMailController:

    @staticmethod
    def obtener_ultimos_destinatarios():
        """Retorna los destinatarios únicos del último lote registrado en el historial."""
        return EnvioModel.get_latest_recipients()

    @staticmethod
    def obtener_todos_los_empleados():
        """Retorna todos los empleados registrados en la base de datos."""
        return EmployeeModel.get_all()
