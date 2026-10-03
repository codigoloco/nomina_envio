"""
Constructor de esquema independiente del motor.
Las migraciones describen las tablas con tipos lógicos (id, entero, cadena, texto)
y este módulo genera el CREATE TABLE correcto para SQLite, MySQL, PostgreSQL o SQL Server.
"""


class Columna:
    def __init__(self, nombre, tipo, longitud=None, nulo=True, unico=False, defecto=None):
        self.nombre = nombre
        self.tipo = tipo            # 'id' | 'entero' | 'cadena' | 'texto'
        self.longitud = longitud
        self.nulo = nulo
        self.unico = unico
        self.defecto = defecto

    @classmethod
    def id_autoincremental(cls, nombre="id"):
        return cls(nombre, "id", nulo=False)


class Esquema:
    def __init__(self, conexion):
        self._conexion = conexion
        self._driver = conexion.driver

    @property
    def conexion(self):
        return self._conexion

    def existe_tabla(self, nombre: str) -> bool:
        sql, params = self._driver.sql_existe_tabla(nombre)
        return self._conexion.execute(sql, params).fetchone() is not None

    def _definicion_columna(self, columna: Columna) -> str:
        if columna.tipo == "id":
            return f"{columna.nombre} {self._driver.sql_id()}"
        partes = [columna.nombre, self._driver.tipo_sql(columna.tipo, columna.longitud)]
        if not columna.nulo:
            partes.append("NOT NULL")
        if columna.unico:
            partes.append("UNIQUE")
        if columna.defecto is not None:
            partes.append(f"DEFAULT {columna.defecto}")
        return " ".join(partes)

    def crear_tabla(self, nombre: str, columnas: list, foraneas: list = None):
        """
        Crea la tabla solo si todavía no existe.
        @param foraneas lista de tuplas (columna, tabla_referenciada, columna_referenciada)
        """
        if self.existe_tabla(nombre):
            return
        definiciones = [self._definicion_columna(c) for c in columnas]
        for columna, tabla_ref, columna_ref in (foraneas or []):
            definiciones.append(f"FOREIGN KEY ({columna}) REFERENCES {tabla_ref}({columna_ref})")
        sufijo = self._driver.sufijo_tabla()
        sql = f"CREATE TABLE {nombre} ({', '.join(definiciones)}) {sufijo}".strip()
        self._conexion.execute(sql)
        self._conexion.commit()
