"""
Verificación en dos pasos (MFA) para TalentHub.

- TOTP (RFC 6238, SHA1, 6 dígitos, 30 s) compatible con Google Authenticator,
  Microsoft Authenticator, Authy, 1Password, etc.
- Secretos TOTP cifrados en la BD con Fernet (clave derivada de MFA_SECRET).
- Códigos de recuperación de un solo uso, guardados solo como hash HMAC.
- Tokens firmados (HMAC) para el paso intermedio del login y para las
  cookies de sesión de admin y psicóloga.

Roles: 'admin', 'psicologa' (id 0), 'trabajador', 'cliente'.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import threading
import time
from datetime import datetime
from urllib.parse import quote

from config import conectar_bd

ROLES = ("admin", "psicologa", "trabajador", "cliente")

PASO_SEG = 30
DIGITOS = 6
VENTANA = 1               # pasos de tolerancia hacia cada lado
MAX_FALLOS = 5            # fallos por cuenta antes de bloquear
BLOQUEO_SEG = 900
PENDIENTE_SEG = 300       # vigencia del token del paso intermedio del login
ISSUER = "TalentHub"
N_RECUPERACION = 10

_ALFABETO_REC = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_ADMIN_TOKEN_DEFAULT = "talenthub_admin_2026_secret"
_ALEATORIA = secrets.token_bytes(32)   # clave por proceso si no hay secreto configurado


# ============================================
# CLAVES Y TOKENS FIRMADOS
# ============================================

def mfa_configurado() -> bool:
    """True si MFA_SECRET está definido con longitud suficiente (requerido para dar de alta MFA)."""
    return len(os.getenv("MFA_SECRET", "")) >= 16


def _base() -> bytes:
    s = os.getenv("MFA_SECRET", "")
    if len(s) >= 16:
        return s.encode("utf-8")
    t = os.getenv("ADMIN_TOKEN", "")
    if len(t) >= 16 and t != _ADMIN_TOKEN_DEFAULT:
        return t.encode("utf-8")
    return _ALEATORIA


def _derivar(proposito: str) -> bytes:
    return hmac.new(_base(), ("talenthub|" + proposito).encode("utf-8"), hashlib.sha256).digest()


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def firmar(payload: dict, ttl_seg: int) -> str:
    datos = dict(payload)
    datos["exp"] = int(time.time()) + int(ttl_seg)
    datos["n"] = secrets.token_hex(8)
    cuerpo = _b64e(json.dumps(datos, separators=(",", ":")).encode("utf-8"))
    firma = _b64e(hmac.new(_derivar("token"), cuerpo.encode("ascii"), hashlib.sha256).digest())
    return cuerpo + "." + firma


def leer_token(token, ahora=None):
    """Devuelve el payload si la firma es válida y no expiró; si no, None."""
    try:
        if not token or token.count(".") != 1:
            return None
        cuerpo, firma = token.split(".")
        esperada = _b64e(hmac.new(_derivar("token"), cuerpo.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(firma, esperada):
            return None
        datos = json.loads(_b64d(cuerpo))
        if int(datos.get("exp", 0)) < (ahora if ahora is not None else time.time()):
            return None
        return datos
    except Exception:
        return None


def crear_token_pendiente(rol: str, id_usuario: int) -> str:
    return firmar({"k": "mfa", "r": rol, "i": int(id_usuario)}, PENDIENTE_SEG)


def leer_token_pendiente(token):
    d = leer_token(token)
    if not d or d.get("k") != "mfa" or d.get("r") not in ROLES:
        return None
    return d


def horas_sesion_rol() -> int:
    try:
        return max(1, min(int(os.getenv("ADMIN_SESION_HORAS", "12")), 168))
    except ValueError:
        return 12


def crear_cookie_rol(rol: str) -> str:
    """Cookie firmada y con vencimiento para admin / psicóloga."""
    return firmar({"k": "ses", "r": rol}, horas_sesion_rol() * 3600)


def cookie_rol_valida(token, rol: str) -> bool:
    d = leer_token(token)
    return bool(d and d.get("k") == "ses" and d.get("r") == rol)


def cookie_segura(request) -> bool:
    try:
        return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "") == "https"
    except Exception:
        return False


def poner_cookie_rol(resp, request, nombre: str, rol: str):
    resp.set_cookie(
        key=nombre,
        value=crear_cookie_rol(rol),
        httponly=True,
        secure=cookie_segura(request),
        max_age=horas_sesion_rol() * 3600,
        samesite="lax",
    )


# ============================================
# TOTP (RFC 6238 / RFC 4226)
# ============================================

def generar_secreto() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _clave_bytes(secreto_b32: str) -> bytes:
    s = secreto_b32.strip().replace(" ", "").upper()
    return base64.b32decode(s + "=" * (-len(s) % 8))


def hotp(clave: bytes, contador: int, digitos: int = DIGITOS) -> str:
    h = hmac.new(clave, struct.pack(">Q", contador), hashlib.sha1).digest()
    o = h[-1] & 0x0F
    n = (struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % (10 ** digitos)
    return str(n).zfill(digitos)


def totp(secreto_b32: str, t=None, digitos: int = DIGITOS) -> str:
    t = time.time() if t is None else t
    return hotp(_clave_bytes(secreto_b32), int(t // PASO_SEG), digitos)


def paso_valido(secreto_b32: str, codigo: str, t=None):
    """Devuelve el número de paso que coincide con el código (dentro de la ventana) o None."""
    if not (codigo and len(codigo) == DIGITOS and codigo.isdigit()):
        return None
    t = time.time() if t is None else t
    clave = _clave_bytes(secreto_b32)
    actual = int(t // PASO_SEG)
    encontrado = None
    for d in range(-VENTANA, VENTANA + 1):          # recorre todo para no filtrar por tiempo
        if hmac.compare_digest(hotp(clave, actual + d), codigo):
            encontrado = actual + d
    return encontrado


def uri_otpauth(secreto_b32: str, etiqueta: str) -> str:
    return "otpauth://totp/{}:{}?secret={}&issuer={}&algorithm=SHA1&digits={}&period={}".format(
        quote(ISSUER), quote(etiqueta), secreto_b32, quote(ISSUER), DIGITOS, PASO_SEG)


def qr_svg(texto: str):
    """QR como SVG inline generado en el servidor. None si 'segno' no está instalado."""
    try:
        import segno
        return segno.make(texto, error="m").svg_inline(scale=5, border=2, dark="#000000", light="#ffffff")
    except Exception:
        return None


# ============================================
# CIFRADO DE SECRETOS Y CÓDIGOS DE RECUPERACIÓN
# ============================================

def _fernet():
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(_derivar("cifrado")))


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode("utf-8")).decode("ascii")


def descifrar(token: str) -> str:
    return _fernet().decrypt(token.encode("ascii")).decode("utf-8")


def _normalizar_rec(c: str) -> str:
    return "".join(ch for ch in (c or "").upper() if ch.isalnum())


def _hash_rec(c: str) -> str:
    return hmac.new(_derivar("recuperacion"), _normalizar_rec(c).encode("utf-8"), hashlib.sha256).hexdigest()


def generar_codigos_recuperacion(n: int = N_RECUPERACION):
    out = []
    for _ in range(n):
        raw = "".join(secrets.choice(_ALFABETO_REC) for _ in range(10))
        out.append(raw[:5] + "-" + raw[5:])
    return out


# ============================================
# BLOQUEO POR CUENTA (en memoria)
# ============================================

_fallos = {}
_lock = threading.Lock()


def _bloqueado(clave) -> bool:
    ahora = time.time()
    with _lock:
        lst = [x for x in _fallos.get(clave, []) if ahora - x < BLOQUEO_SEG]
        _fallos[clave] = lst
        return len(lst) >= MAX_FALLOS


def _registrar_fallo(clave):
    with _lock:
        _fallos.setdefault(clave, []).append(time.time())


def _limpiar_fallos(clave):
    with _lock:
        _fallos.pop(clave, None)


def esta_bloqueada(rol: str, id_usuario: int) -> bool:
    return _bloqueado((rol, int(id_usuario)))


# ============================================
# BASE DE DATOS
# ============================================

def ensure_tablas():
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mfa_usuarios (
            id_mfa INT AUTO_INCREMENT PRIMARY KEY,
            tipo_usuario VARCHAR(20) NOT NULL,
            id_usuario INT NOT NULL,
            secret_enc TEXT NOT NULL,
            activo TINYINT(1) NOT NULL DEFAULT 0,
            ultimo_paso BIGINT NULL,
            fecha_creacion DATETIME NULL,
            fecha_activacion DATETIME NULL,
            UNIQUE KEY uq_mfa_usuario (tipo_usuario, id_usuario)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mfa_recuperacion (
            id_codigo INT AUTO_INCREMENT PRIMARY KEY,
            tipo_usuario VARCHAR(20) NOT NULL,
            id_usuario INT NOT NULL,
            codigo_hash CHAR(64) NOT NULL,
            usado TINYINT(1) NOT NULL DEFAULT 0,
            fecha_uso DATETIME NULL,
            INDEX idx_mfa_rec (tipo_usuario, id_usuario)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def _fila(rol, id_usuario):
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM mfa_usuarios WHERE tipo_usuario = %s AND id_usuario = %s",
                (rol, int(id_usuario)))
    f = cur.fetchone()
    cur.close()
    conn.close()
    return f


def mfa_activo(rol: str, id_usuario: int) -> bool:
    """True si el usuario tiene MFA activado. Si la tabla aún no existe, False."""
    try:
        f = _fila(rol, id_usuario)
    except Exception:
        try:
            ensure_tablas()
            f = _fila(rol, id_usuario)
        except Exception:
            return False
    return bool(f and f.get("activo"))


def _guardar_codigos(rol, id_usuario, codigos):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("DELETE FROM mfa_recuperacion WHERE tipo_usuario = %s AND id_usuario = %s",
                (rol, int(id_usuario)))
    for c in codigos:
        cur.execute("INSERT INTO mfa_recuperacion (tipo_usuario, id_usuario, codigo_hash, usado) "
                    "VALUES (%s, %s, %s, 0)", (rol, int(id_usuario), _hash_rec(c)))
    conn.commit()
    cur.close()
    conn.close()


def iniciar_alta(rol: str, id_usuario: int, etiqueta: str):
    """Genera un secreto pendiente (inactivo). Lanza ValueError si ya está activo o falta MFA_SECRET."""
    if not mfa_configurado():
        raise ValueError("MFA_NO_CONFIGURADO")
    ensure_tablas()
    f = _fila(rol, id_usuario)
    if f and f.get("activo"):
        raise ValueError("YA_ACTIVO")
    secreto = generar_secreto()
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("DELETE FROM mfa_usuarios WHERE tipo_usuario = %s AND id_usuario = %s",
                (rol, int(id_usuario)))
    cur.execute("INSERT INTO mfa_usuarios (tipo_usuario, id_usuario, secret_enc, activo, fecha_creacion) "
                "VALUES (%s, %s, %s, 0, %s)", (rol, int(id_usuario), cifrar(secreto), datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    uri = uri_otpauth(secreto, etiqueta)
    return {"secreto": secreto, "uri": uri, "qr_svg": qr_svg(uri)}


def _consumir_paso(rol, id_usuario, paso) -> bool:
    """Marca el paso como usado; False si ya se usó (anti-replay)."""
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("UPDATE mfa_usuarios SET ultimo_paso = %s WHERE tipo_usuario = %s AND id_usuario = %s "
                "AND (ultimo_paso IS NULL OR ultimo_paso < %s)", (paso, rol, int(id_usuario), paso))
    ok = cur.rowcount == 1
    conn.commit()
    cur.close()
    conn.close()
    return ok


def activar(rol: str, id_usuario: int, codigo: str):
    """Confirma el alta con un código de la app. Devuelve los códigos de recuperación o None."""
    clave = (rol, int(id_usuario))
    if _bloqueado(clave):
        return None
    f = _fila(rol, id_usuario)
    if not f or f.get("activo"):
        return None
    try:
        secreto = descifrar(f["secret_enc"])
    except Exception:
        return None
    paso = paso_valido(secreto, _normalizar_codigo(codigo))
    if paso is None:
        _registrar_fallo(clave)
        return None
    _limpiar_fallos(clave)
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("UPDATE mfa_usuarios SET activo = 1, ultimo_paso = %s, fecha_activacion = %s "
                "WHERE tipo_usuario = %s AND id_usuario = %s", (paso, datetime.now(), rol, int(id_usuario)))
    conn.commit()
    cur.close()
    conn.close()
    codigos = generar_codigos_recuperacion()
    _guardar_codigos(rol, id_usuario, codigos)
    return codigos


def _normalizar_codigo(c: str) -> str:
    s = (c or "").strip()
    d = s.replace(" ", "").replace("-", "")
    return d if d.isdigit() else s


def verificar(rol: str, id_usuario: int, codigo: str) -> bool:
    """Verifica TOTP o código de recuperación para un usuario con MFA activo."""
    clave = (rol, int(id_usuario))
    if _bloqueado(clave):
        return False
    f = _fila(rol, id_usuario)
    if not f or not f.get("activo"):
        return False
    c = _normalizar_codigo(codigo)
    ok = False
    if c.isdigit() and len(c) == DIGITOS:
        try:
            paso = paso_valido(descifrar(f["secret_enc"]), c)
        except Exception:
            paso = None
        ok = paso is not None and _consumir_paso(rol, id_usuario, paso)
    elif len(_normalizar_rec(c)) == 10:
        h = _hash_rec(c)
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("UPDATE mfa_recuperacion SET usado = 1, fecha_uso = %s WHERE tipo_usuario = %s "
                    "AND id_usuario = %s AND codigo_hash = %s AND usado = 0",
                    (datetime.now(), rol, int(id_usuario), h))
        ok = cur.rowcount == 1
        conn.commit()
        cur.close()
        conn.close()
    if ok:
        _limpiar_fallos(clave)
    else:
        _registrar_fallo(clave)
    return ok


def desactivar(rol: str, id_usuario: int):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("DELETE FROM mfa_usuarios WHERE tipo_usuario = %s AND id_usuario = %s", (rol, int(id_usuario)))
    cur.execute("DELETE FROM mfa_recuperacion WHERE tipo_usuario = %s AND id_usuario = %s", (rol, int(id_usuario)))
    conn.commit()
    cur.close()
    conn.close()
    _limpiar_fallos((rol, int(id_usuario)))


def regenerar_recuperacion(rol: str, id_usuario: int):
    codigos = generar_codigos_recuperacion()
    _guardar_codigos(rol, id_usuario, codigos)
    return codigos


def codigos_restantes(rol: str, id_usuario: int) -> int:
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mfa_recuperacion WHERE tipo_usuario = %s AND id_usuario = %s AND usado = 0",
                (rol, int(id_usuario)))
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return int(n)
