"""
Configuración de la aplicación
Maneja variables de entorno para desarrollo local y producción
"""
import os
from dotenv import load_dotenv
import mysql.connector

# Cargar variables de entorno desde .env (solo en desarrollo local)
load_dotenv()

# Configuración de Base de Datos
DB_CONFIG = {
    "host":             os.getenv("DB_HOST", "localhost"),
    "user":             os.getenv("DB_USER", "root"),
    "password":         os.getenv("DB_PASSWORD", "Jhonier18."),
    "database":         os.getenv("DB_NAME", "profiles_cv_db"),
    "port":             int(os.getenv("DB_PORT", "3306")),
    "connection_timeout": 10,        # falla rápido si no hay BD
    "autocommit":       False,
}

def conectar_bd():
    """Abre una conexión MySQL con timeout. Simple y confiable en Railway."""
    return mysql.connector.connect(**DB_CONFIG)

# Configuración de la aplicación
APP_CONFIG = {
    "debug":       os.getenv("DEBUG", "False").lower() == "true",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "port":        int(os.getenv("PORT", "8000"))
}

IS_PRODUCTION = APP_CONFIG["environment"] == "production"

print(f"🔧 Config: entorno={APP_CONFIG['environment']} "
      f"bd={DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
