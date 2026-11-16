"""
Datos legales de TalentHub: identificación del responsable, versiones de los documentos,
registro de aceptaciones (Ley 1581 de 2012, art. 9: la autorización debe poder probarse)
y canal de peticiones, quejas y reclamos con número de radicado (Ley 1480 de 2011, art. 50).
"""

import os
import re
import secrets
import threading
import time
from datetime import datetime

from config import conectar_bd

# Se cambia cada vez que se modifica el texto de los documentos.
VERSION_TERMINOS = "2026-11"
VERSION_PRIVACIDAD = "2026-11"
FECHA_VIGENCIA = "noviembre de 2026"

SIC_URL = "https://www.sic.gov.co"

TIPOS_PQRS = {
    "peticion": "Petición",
    "queja": "Queja",
    "reclamo": "Reclamo",
    "sugerencia": "Sugerencia",
    "retracto": "Retracto o devolución",
    "datos_personales": "Datos personales (consulta o reclamo)",
}
ESTADOS_PQRS = {"recibido": "Recibido", "en_tramite": "En trámite", "resuelto": "Resuelto"}


def datos_legales() -> dict:
    """Identificación del responsable. Se configura con variables de entorno (ver .env.example)."""
    return {
        "razon_social": os.getenv("LEGAL_RAZON_SOCIAL", "").strip() or "TalentHub",
        "nit": os.getenv("LEGAL_NIT", "").strip(),
        "direccion": os.getenv("LEGAL_DIRECCION", "").strip(),
        "ciudad": os.getenv("LEGAL_CIUDAD", "").strip(),
        "email": os.getenv("LEGAL_EMAIL", "").strip() or "jhoniercespedes32@gmail.com",
        "telefono": os.getenv("LEGAL_TELEFONO", "").strip(),
        "sic_url": SIC_URL,
        "version_terminos": VERSION_TERMINOS,
        "version_privacidad": VERSION_PRIVACIDAD,
        "fecha_vigencia": FECHA_VIGENCIA,
    }


def datos_legales_faltantes() -> list:
    """Variables que aún no se han configurado (para avisar al administrador)."""
    faltan = []
    for var, etiqueta in (("LEGAL_RAZON_SOCIAL", "razón social"), ("LEGAL_NIT", "NIT o documento"),
                          ("LEGAL_DIRECCION", "dirección"), ("LEGAL_EMAIL", "correo de contacto legal"),
                          ("LEGAL_TELEFONO", "teléfono")):
        if not os.getenv(var, "").strip():
            faltan.append(f"{var} ({etiqueta})")
    return faltan


# ============================================
# TABLAS
# ============================================

_tablas_listas = False


def ensure_tablas():
    global _tablas_listas
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aceptaciones_legales (
            id_aceptacion INT AUTO_INCREMENT PRIMARY KEY,
            tipo_usuario VARCHAR(20) NOT NULL,
            id_usuario INT NOT NULL,
            documento VARCHAR(30) NOT NULL,
            version VARCHAR(20) NOT NULL,
            fecha DATETIME NOT NULL,
            ip VARCHAR(64) NULL,
            user_agent VARCHAR(255) NULL,
            INDEX idx_acept_usuario (tipo_usuario, id_usuario)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pqrs (
            id_pqrs INT AUTO_INCREMENT PRIMARY KEY,
            radicado VARCHAR(40) NOT NULL UNIQUE,
            tipo VARCHAR(20) NOT NULL,
            nombre VARCHAR(150) NOT NULL,
            correo VARCHAR(150) NOT NULL,
            telefono VARCHAR(30) NULL,
            id_solicitud INT NULL,
            mensaje TEXT NOT NULL,
            estado VARCHAR(20) NOT NULL DEFAULT 'recibido',
            respuesta TEXT NULL,
            fecha_creacion DATETIME NOT NULL,
            fecha_respuesta DATETIME NULL,
            ip VARCHAR(64) NULL,
            INDEX idx_pqrs_correo (correo)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    _tablas_listas = True


def _asegurar():
    if not _tablas_listas:
        ensure_tablas()


# ============================================
# ACEPTACIONES
# ============================================

def registrar_aceptacion(tipo_usuario: str, id_usuario: int, documentos, ip: str = None, user_agent: str = None):
    """
    Guarda la evidencia de que el usuario aceptó cada documento (con versión, fecha, IP).
    documentos: lista de claves: 'terminos', 'privacidad', 'datos_sensibles', 'ubicacion'.
    No interrumpe el registro si falla: se escribe en el log.
    """
    versiones = {"terminos": VERSION_TERMINOS, "privacidad": VERSION_PRIVACIDAD,
                 "datos_sensibles": VERSION_PRIVACIDAD, "ubicacion": VERSION_PRIVACIDAD}
    try:
        _asegurar()
        conn = conectar_bd()
        cur = conn.cursor()
        ahora = datetime.now()
        for doc in documentos:
            cur.execute(
                "INSERT INTO aceptaciones_legales (tipo_usuario, id_usuario, documento, version, fecha, ip, user_agent) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (tipo_usuario, int(id_usuario), doc, versiones.get(doc, VERSION_TERMINOS), ahora,
                 (ip or "")[:64], (user_agent or "")[:255]))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[LEGAL] No se pudo registrar la aceptación de {tipo_usuario} {id_usuario}: {e}")
        return False


# ============================================
# PQRS (peticiones, quejas y reclamos)
# ============================================

_RE_CORREO = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
_envios = {}
_lock = threading.Lock()
MAX_ENVIOS_HORA = 5


def _limite_ok(ip: str) -> bool:
    ahora = time.time()
    with _lock:
        lst = [t for t in _envios.get(ip, []) if ahora - t < 3600]
        if len(lst) >= MAX_ENVIOS_HORA:
            _envios[ip] = lst
            return False
        lst.append(ahora)
        _envios[ip] = lst
        return True


def crear_pqrs(tipo, nombre, correo, telefono, id_solicitud, mensaje, ip):
    """Devuelve (radicado, fecha, error). Valida y limita envíos por IP."""
    tipo = (tipo or "").strip()
    nombre = (nombre or "").strip()
    correo = (correo or "").strip().lower()
    telefono = (telefono or "").strip()
    mensaje = (mensaje or "").strip()
    if tipo not in TIPOS_PQRS:
        return None, None, "Elige el tipo de solicitud."
    if not (2 <= len(nombre) <= 150):
        return None, None, "Escribe tu nombre."
    if not _RE_CORREO.match(correo) or len(correo) > 150:
        return None, None, "Escribe un correo válido para enviarte la respuesta."
    if len(telefono) > 30:
        return None, None, "El teléfono es demasiado largo."
    if not (10 <= len(mensaje) <= 4000):
        return None, None, "Cuéntanos tu caso con al menos 10 caracteres (máximo 4000)."
    sol = None
    if id_solicitud not in (None, ""):
        try:
            sol = int(id_solicitud)
        except (TypeError, ValueError):
            return None, None, "El número de solicitud no es válido."
    if not _limite_ok(ip or "?"):
        return None, None, "Has enviado varias solicitudes seguidas. Intenta de nuevo en una hora."

    _asegurar()
    conn = conectar_bd()
    cur = conn.cursor()
    try:
        ahora = datetime.now()
        cur.execute(
            "INSERT INTO pqrs (radicado, tipo, nombre, correo, telefono, id_solicitud, mensaje, estado, fecha_creacion, ip) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, 'recibido', %s, %s)",
            ("TMP-" + secrets.token_hex(8), tipo, nombre, correo, telefono or None, sol, mensaje, ahora, (ip or "")[:64]))
        id_pqrs = cur.lastrowid
        radicado = "PQRS-%d-%06d" % (ahora.year, id_pqrs)
        cur.execute("UPDATE pqrs SET radicado = %s WHERE id_pqrs = %s", (radicado, id_pqrs))
        conn.commit()
        return radicado, ahora, None
    except Exception as e:
        conn.rollback()
        print(f"[PQRS] Error al crear: {e}")
        return None, None, "No pudimos registrar tu solicitud. Inténtalo de nuevo."
    finally:
        cur.close()
        conn.close()


def consultar_pqrs(radicado, correo):
    """Solo devuelve la solicitud si coinciden radicado y correo."""
    _asegurar()
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT radicado, tipo, estado, mensaje, respuesta, fecha_creacion, fecha_respuesta "
                "FROM pqrs WHERE radicado = %s AND correo = %s LIMIT 1",
                ((radicado or "").strip().upper(), (correo or "").strip().lower()))
    fila = cur.fetchone()
    cur.close()
    conn.close()
    return fila


def listar_pqrs(estado=None, limite=200):
    _asegurar()
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    if estado in ESTADOS_PQRS:
        cur.execute("SELECT * FROM pqrs WHERE estado = %s ORDER BY fecha_creacion DESC LIMIT %s", (estado, int(limite)))
    else:
        cur.execute("SELECT * FROM pqrs ORDER BY fecha_creacion DESC LIMIT %s", (int(limite),))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return filas


def responder_pqrs(id_pqrs, estado, respuesta):
    """Actualiza estado y respuesta. Devuelve la fila actualizada o None."""
    if estado not in ESTADOS_PQRS:
        return None
    _asegurar()
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    respuesta = (respuesta or "").strip()[:4000]
    cur.execute(
        "UPDATE pqrs SET estado = %s, respuesta = %s, fecha_respuesta = %s WHERE id_pqrs = %s",
        (estado, respuesta or None, datetime.now() if respuesta else None, int(id_pqrs)))
    conn.commit()
    cur.execute("SELECT * FROM pqrs WHERE id_pqrs = %s", (int(id_pqrs),))
    fila = cur.fetchone()
    cur.close()
    conn.close()
    return fila
