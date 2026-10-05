"""
Script de compilación automatizada para NominaApp usando PyInstaller.
Limpia carpetas previas de compilación, asegura la presencia de directorios de trabajo
y genera el paquete ejecutable distribuible.
"""

import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def verificar_e_instalar_pyinstaller():
    """Verifica si PyInstaller está instalado en el entorno actual. Si no, lo instala."""
    try:
        import PyInstaller
    except ImportError:
        print(" PyInstaller no está instalado en el entorno actual. Instalando...")
        cmd_install = [sys.executable, "-m", "pip", "install", "pyinstaller"]
        try:
            subprocess.run(cmd_install, check=True)
            print(" PyInstaller instalado correctamente.\n")
        except subprocess.CalledProcessError as e:
            print(f" Error al instalar PyInstaller: {e}")
            sys.exit(1)


def limpiar_cache_proyecto():
    """Elimina recursivamente todas las carpetas __pycache__ y archivos .pyc del proyecto (excepto .venv)."""
    print("Limpiando caché de bytecode Python (__pycache__ y *.pyc)...")
    for raiz, directorios, archivos in os.walk(BASE_DIR):
        if ".venv" in raiz or ".git" in raiz:
            continue
        for d in directorios:
            if d == "__pycache__":
                ruta_dir = os.path.join(raiz, d)
                try:
                    shutil.rmtree(ruta_dir, ignore_errors=True)
                except Exception:
                    pass
        for a in archivos:
            if a.endswith((".pyc", ".pyo")):
                try:
                    os.remove(os.path.join(raiz, a))
                except Exception:
                    pass


def preparar_directorios_trabajo():
    """Limpia y recrea las carpetas build/main y dist necesarias para PyInstaller."""
    for carpeta in ["build", "dist"]:
        path = os.path.join(BASE_DIR, carpeta)
        if os.path.exists(path):
            print(f"Limpiando directorio anterior: {carpeta}...")
            try:
                shutil.rmtree(path, ignore_errors=True)
            except Exception:
                pass

    os.makedirs(os.path.join(BASE_DIR, "build", "main"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "dist"), exist_ok=True)


def compilar():
    """Ejecuta PyInstaller nativamente desde el intérprete Python."""
    spec_path = os.path.join(BASE_DIR, "main.spec")
    if not os.path.exists(spec_path):
        print(f"Error: No se encontró el archivo {spec_path}")
        sys.exit(1)

    print("Iniciando proceso de compilación limpia con PyInstaller...")

    try:
        import PyInstaller.__main__

        PyInstaller.__main__.run([
            spec_path,
            "--noconfirm",
            "--clean",
        ])

        dist_path = os.path.join(BASE_DIR, "dist", "NominaApp")
        if os.path.exists(dist_path):
            print("\n" + "=" * 50)
            print(" ¡Compilación completada con éxito!")
            print(f" El ejecutable se encuentra en: {dist_path}")
            print("=" * 50 + "\n")
        else:
            print("\n Error: La compilación no pudo generar los archivos ejecutables correctamente.")
            sys.exit(1)

    except Exception as e:
        print(f"\n Error durante la compilación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verificar_e_instalar_pyinstaller()
    limpiar_cache_proyecto()
    preparar_directorios_trabajo()
    compilar()
