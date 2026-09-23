"""
Configuración global de pytest.
Asegura que el directorio raíz del proyecto esté en sys.path
para que los tests puedan importar 'app'.
"""
import os
import sys

# Añadir el directorio del proyecto al sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))