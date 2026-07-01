"""
Configuración de la aplicación
Maneja variables de entorno para desarrollo local y producción
"""
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

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

# ============================================
# CONNECTION POOL — reutiliza conexiones TCP
# Evita abrir una nueva conexión en cada request
# ============================================
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="talenthub_pool",
                pool_size=10,
                pool_reset_session=True,
                **DB_CONFIG
            )
            print("✅ Connection pool MySQL creado (size=10)")
        except Exception as e:
            print(f"⚠️ No se pudo crear pool MySQL: {e}")
    return _pool

def conectar_bd():
    """
    Obtiene una conexión del pool (rápido) o crea una nueva como fallback.
    """
    pool = get_pool()
    if pool:
        try:
            return pool.get_connection()
        except Exception:
            pass
    # Fallback: conexión directa si el pool falla
    return mysql.connector.connect(**DB_CONFIG)

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
