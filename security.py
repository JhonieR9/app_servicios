"""
security.py — Módulo centralizado de seguridad para TalentHub

Cubre los tres pilares CID:
  Confidencialidad : rate limiting para bloquear fuerza bruta en logins
  Integridad       : validación MIME real de archivos subidos
  Disponibilidad   : logging de eventos para detectar ataques y auditar accesos
"""

import time
import logging
import struct
import io
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse

# ────────────────────────────────────────────────────────────────
# LOGGING DE SEGURIDAD
# ────────────────────────────────────────────────────────────────

# Logger dedicado exclusivamente a eventos de seguridad.
# Escribe en stdout (Railway lo captura) y en archivo local si es posible.
security_logger = logging.getLogger("talenthub.security")
security_logger.setLevel(logging.INFO)

_fmt = logging.Formatter(
    "[SECURITY] %(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler de consola (siempre disponible en Railway)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_fmt)
security_logger.addHandler(_console_handler)

# Handler de archivo (opcional — falla silenciosamente si no hay disco)
try:
    _file_handler = logging.FileHandler("security.log", encoding="utf-8")
    _file_handler.setFormatter(_fmt)
    security_logger.addHandler(_file_handler)
except Exception:
    pass


def log_login_ok(ip: str, tipo: str, identificador: str):
    security_logger.info(f"LOGIN_OK     tipo={tipo!r} id={identificador!r} ip={ip}")

def log_login_fail(ip: str, tipo: str, identificador: str, motivo: str = ""):
    security_logger.warning(f"LOGIN_FAIL   tipo={tipo!r} id={identificador!r} ip={ip} motivo={motivo!r}")

def log_rate_blocked(ip: str, path: str):
    security_logger.warning(f"RATE_BLOCK   ip={ip} path={path!r}")

def log_upload_blocked(ip: str, filename: str, motivo: str):
    security_logger.warning(f"UPLOAD_BLOCK ip={ip} file={filename!r} motivo={motivo!r}")

def log_upload_ok(ip: str, filename: str, mime: str):
    security_logger.info(f"UPLOAD_OK    ip={ip} file={filename!r} mime={mime!r}")

def log_session_invalid(ip: str, path: str):
    security_logger.warning(f"SESSION_BAD  ip={ip} path={path!r}")


# ────────────────────────────────────────────────────────────────
# RATE LIMITING  (en memoria, sin dependencias externas)
# ────────────────────────────────────────────────────────────────
#
# Estrategia: ventana deslizante por IP.
# Solo se cuentan intentos FALLIDOS (login_fail), no los exitosos.
# Así un usuario legítimo que ya tiene sesión activa no queda bloqueado.
#
# Valores conservadores para producción:
#   - 8 intentos fallidos en 15 minutos → bloqueo temporal
#   - admin: 5 intentos en 15 minutos (umbral más estricto)

_failed_attempts: dict[str, list[float]] = defaultdict(list)

WINDOW_SECONDS     = 900   # 15 minutos
LIMIT_NORMAL       = 8     # usuarios normales
LIMIT_ADMIN        = 5     # admin y psicóloga (umbral más estricto)
LOCKOUT_MESSAGE    = "Demasiados intentos fallidos. Espera 15 minutos e intenta de nuevo."


def _get_ip(request: Request) -> str:
    """Extrae la IP real teniendo en cuenta proxies (Railway usa X-Forwarded-For)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def registrar_fallo(ip: str, tipo: str = "normal") -> bool:
    """
    Registra un intento fallido para la IP dada.
    Retorna True si la IP queda bloqueada tras este intento.
    """
    ahora = time.time()
    key = f"{tipo}:{ip}"
    # Purgar intentos fuera de la ventana
    _failed_attempts[key] = [t for t in _failed_attempts[key] if ahora - t < WINDOW_SECONDS]
    _failed_attempts[key].append(ahora)
    limite = LIMIT_ADMIN if tipo == "admin" else LIMIT_NORMAL
    return len(_failed_attempts[key]) >= limite


def esta_bloqueado(ip: str, tipo: str = "normal") -> bool:
    """Comprueba si la IP tiene demasiados intentos fallidos recientes."""
    ahora = time.time()
    key = f"{tipo}:{ip}"
    recientes = [t for t in _failed_attempts.get(key, []) if ahora - t < WINDOW_SECONDS]
    _failed_attempts[key] = recientes
    limite = LIMIT_ADMIN if tipo == "admin" else LIMIT_NORMAL
    return len(recientes) >= limite


def limpiar_bloqueo(ip: str, tipo: str = "normal"):
    """Limpia el contador de intentos fallidos tras un login exitoso."""
    key = f"{tipo}:{ip}"
    _failed_attempts.pop(key, None)


def respuesta_bloqueado() -> JSONResponse:
    return JSONResponse(
        {"error": LOCKOUT_MESSAGE},
        status_code=429,
        headers={"Retry-After": str(WINDOW_SECONDS)}
    )


# ────────────────────────────────────────────────────────────────
# VALIDACIÓN MIME REAL (magic bytes — sin librerías externas)
# ────────────────────────────────────────────────────────────────
#
# Lee los primeros bytes del archivo y comprueba las firmas conocidas.
# Esto es más robusto que confiar en content_type o la extensión del nombre,
# que un atacante puede falsificar fácilmente.

# Mapa: tipo_lógico → [(offset, bytes_firma)]
_MAGIC: dict[str, list[tuple[int, bytes]]] = {
    "image/jpeg": [(0, b"\xFF\xD8\xFF")],
    "image/png":  [(0, b"\x89PNG\r\n\x1a\n")],
    "image/webp": [(0, b"RIFF"), (8, b"WEBP")],  # RIFF....WEBP
    "image/gif":  [(0, b"GIF87a"), (0, b"GIF89a")],
    "application/pdf": [(0, b"%PDF")],
}

# Tipos permitidos por categoría de documento
MIME_PERMITIDOS = {
    "imagen":    {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "documento": {"application/pdf", "image/jpeg", "image/png"},
    "perfil":    {"image/jpeg", "image/png", "image/webp"},
}

# Límites de tamaño por categoría (bytes)
MAX_SIZE = {
    "imagen":    10 * 1024 * 1024,   # 10 MB
    "documento": 20 * 1024 * 1024,   # 20 MB
    "perfil":     5 * 1024 * 1024,   #  5 MB
}


def detectar_mime(data: bytes) -> str | None:
    """
    Detecta el tipo MIME real leyendo las firmas (magic bytes) del archivo.
    Retorna el tipo MIME detectado, o None si no coincide con ninguno conocido.
    """
    for mime, firmas in _MAGIC.items():
        if mime == "image/webp":
            # WEBP necesita dos firmas en posiciones distintas
            if (len(data) >= 12
                    and data[0:4] == b"RIFF"
                    and data[8:12] == b"WEBP"):
                return mime
            continue
        for offset, firma in firmas:
            if data[offset: offset + len(firma)] == firma:
                return mime
    return None


def validar_archivo(
    data: bytes,
    filename: str,
    categoria: str = "imagen"
) -> tuple[bool, str, str]:
    """
    Valida un archivo subido.

    Args:
        data      : contenido del archivo en bytes
        filename  : nombre original del archivo (para extensión)
        categoria : 'imagen', 'documento' o 'perfil'

    Returns:
        (valido, mime_detectado, mensaje_error)
        Si es válido, mensaje_error es vacío.
    """
    # 1. Tamaño
    max_bytes = MAX_SIZE.get(categoria, 10 * 1024 * 1024)
    if len(data) == 0:
        return False, "", "El archivo está vacío"
    if len(data) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return False, "", f"El archivo supera el tamaño máximo permitido ({mb} MB)"

    # 2. Detección MIME por magic bytes
    mime_real = detectar_mime(data[:32])   # solo necesitamos los primeros bytes
    if mime_real is None:
        return False, "", "Formato de archivo no reconocido o no permitido"

    # 3. Tipo permitido para esta categoría
    permitidos = MIME_PERMITIDOS.get(categoria, set())
    if mime_real not in permitidos:
        return False, mime_real, f"Tipo de archivo no permitido ({mime_real})"

    # 4. Extensión coherente con el contenido (no bloquea, solo advierte en log)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_esperadas = {
        "image/jpeg": {"jpg", "jpeg"},
        "image/png":  {"png"},
        "image/webp": {"webp"},
        "image/gif":  {"gif"},
        "application/pdf": {"pdf"},
    }
    if ext not in ext_esperadas.get(mime_real, {ext}):
        # Extensión engañosa — puede ser un intento de bypass; lo registramos
        security_logger.warning(
            f"MIME_MISMATCH file={filename!r} ext={ext!r} mime_real={mime_real!r}"
        )

    return True, mime_real, ""
