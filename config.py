"""
Configuración de la aplicación
Maneja variables de entorno para desarrollo local y producción
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (solo en desarrollo local)
load_dotenv()

# Configuración de Base de Datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Jhonier18."),
    "database": os.getenv("DB_NAME", "profiles_cv_db"),
    "port": int(os.getenv("DB_PORT", "3306"))
}

# Configuración de la aplicación
APP_CONFIG = {
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "port": int(os.getenv("PORT", "8000"))
}

# Verificar si estamos en producción
IS_PRODUCTION = APP_CONFIG["environment"] == "production"

print(f"🔧 Configuración cargada:")
print(f"   Entorno: {APP_CONFIG['environment']}")
print(f"   Base de datos: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"   Database: {DB_CONFIG['database']}")
