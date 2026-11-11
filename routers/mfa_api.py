"""
Endpoints de verificación en dos pasos (MFA) para admin, psicóloga, trabajadores y clientes.

La identidad SIEMPRE sale de la cookie de sesión del rol indicado, nunca de un id enviado
por el navegador. Cambiar la configuración de MFA exige la contraseña (y el código si ya
está activo), así que una sesión robada o abierta no basta para apagarlo.
"""

import hmac
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import auth
import mfa
import security
from config import conectar_bd

router = APIRouter(prefix="/mfa", tags=["mfa"])
templates = Jinja2Templates(directory="templates")

_LOGIN = {
    "admin": "/trabajador/admin/login",
    "psicologa": "/psicologa/login",
    "trabajador": "/trabajador/login",
    "cliente": "/cliente/login",
}
_VOLVER = {
    "admin": ("/trabajador/dashboard", "Volver al panel"),
    "psicologa": ("/psicologa/panel", "Volver al panel"),
    "trabajador": ("/trabajador/panel", "Volver al panel"),
    "cliente": ("/cliente/panel", "Volver al panel"),
}


def _identidad(request: Request, rol: str):
    """id_usuario si hay sesión válida de ese rol; si no, None. (admin y psicóloga usan id 0)"""
    if rol == "admin":
        from routers import trabajadores
        return 0 if trabajadores.verificar_admin(request) else None
    if rol == "psicologa":
        from routers import psicologa
        return 0 if psicologa.verificar_psicologa(request) else None
    if rol == "trabajador":
        token = request.cookies.get("session_token")
    elif rol == "cliente":
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    else:
        return None
    sesion = auth.verificar_sesion(token) if token else None
    if sesion and sesion.get("tipo_usuario") == rol:
        return int(sesion["id_usuario"])
    return None


def _password_correcta(rol: str, id_usuario: int, password: str) -> bool:
    if not password:
        return False
    if rol == "admin":
        from routers import trabajadores
        return hmac.compare_digest(password.encode("utf-8"), trabajadores.ADMIN_PASSWORD.encode("utf-8"))
    if rol == "psicologa":
        from routers import psicologa
        return hmac.compare_digest(password.encode("utf-8"), psicologa.PSICO_PASSWORD.encode("utf-8"))
    tabla, col = ("personas", "id_persona") if rol == "trabajador" else ("clientes", "id_cliente")
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT password_hash FROM {tabla} WHERE {col} = %s LIMIT 1", (id_usuario,))
    fila = cur.fetchone()
    cur.close()
    conn.close()
    if not fila or not fila.get("password_hash"):
        return False
    try:
        return auth.verificar_password(password, fila["password_hash"])
    except Exception:
        return False


def _error(msg: str, status: int, **extra):
    d = {"error": msg}
    d.update(extra)
    return JSONResponse(d, status_code=status)


def _precheck(request: Request, rol: str):
    """Valida rol, sesión y rate limit. Devuelve (id_usuario, ip, respuesta_de_error)."""
    if rol not in mfa.ROLES:
        return None, None, _error("Rol inválido", 400)
    id_usuario = _identidad(request, rol)
    if id_usuario is None:
        return None, None, _error("Tu sesión venció. Inicia sesión de nuevo.", 401)
    ip = security._get_ip(request)
    if security.esta_bloqueado(ip, "normal"):
        security.log_rate_blocked(ip, "/mfa")
        return None, None, security.respuesta_bloqueado()
    return id_usuario, ip, None


def _exigir_password(rol, id_usuario, password, ip):
    if _password_correcta(rol, id_usuario, password):
        return None
    security.registrar_fallo(ip, "normal")
    security.log_login_fail(ip, rol, str(id_usuario), "mfa: contraseña incorrecta")
    return _error("Contraseña incorrecta", 403)


def _exigir_codigo(rol, id_usuario, codigo, ip):
    if mfa.verificar(rol, id_usuario, codigo):
        return None
    security.registrar_fallo(ip, "normal")
    if mfa.esta_bloqueada(rol, id_usuario):
        return _error("Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", 429)
    return _error("Código incorrecto", 403)


# ============================================
# ESTADO Y ALTA
# ============================================

@router.get("/estado")
def estado(request: Request, rol: str):
    id_usuario, ip, err = _precheck(request, rol)
    if err:
        return err
    activo = mfa.mfa_activo(rol, id_usuario)
    return {
        "activo": activo,
        "disponible": mfa.mfa_configurado(),
        "restantes": mfa.codigos_restantes(rol, id_usuario) if activo else 0,
    }


@router.post("/iniciar")
def iniciar(request: Request, rol: str = Form(...), password: str = Form("")):
    id_usuario, ip, err = _precheck(request, rol)
    if err:
        return err
    if not mfa.mfa_configurado():
        return _error("La verificación en dos pasos aún no está habilitada en el servidor "
                      "(falta configurar MFA_SECRET).", 503)
    err = _exigir_password(rol, id_usuario, password, ip)
    if err:
        return err
    try:
        datos = mfa.iniciar_alta(rol, id_usuario, f"{rol}-{id_usuario}" if id_usuario else rol)
    except ValueError as e:
        if str(e) == "YA_ACTIVO":
            return _error("La verificación en dos pasos ya está activa.", 409)
        return _error("No se pudo iniciar la configuración.", 500)
    except Exception:
        return _error("No se pudo iniciar la configuración.", 500)
    return {"ok": True, "secreto": datos["secreto"], "uri": datos["uri"], "qr_svg": datos["qr_svg"]}


@router.post("/activar")
def activar(request: Request, rol: str = Form(...), codigo: str = Form(...)):
    id_usuario, ip, err = _precheck(request, rol)
    if err:
        return err
    codigos = mfa.activar(rol, id_usuario, codigo)
    if codigos is None:
        security.registrar_fallo(ip, "normal")
        if mfa.esta_bloqueada(rol, id_usuario):
            return _error("Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", 429)
        return _error("Código incorrecto. Revisa que la hora de tu celular sea automática.", 403)
    security.security_logger.info(f"MFA_ACTIVADO rol={rol} id={id_usuario} ip={ip}")
    return {"ok": True, "codigos": codigos}


@router.post("/desactivar")
def desactivar(request: Request, rol: str = Form(...), password: str = Form(""), codigo: str = Form("")):
    id_usuario, ip, err = _precheck(request, rol)
    if err:
        return err
    if not mfa.mfa_activo(rol, id_usuario):
        return _error("La verificación en dos pasos no está activa.", 409)
    err = _exigir_password(rol, id_usuario, password, ip) or _exigir_codigo(rol, id_usuario, codigo, ip)
    if err:
        return err
    mfa.desactivar(rol, id_usuario)
    security.security_logger.info(f"MFA_DESACTIVADO rol={rol} id={id_usuario} ip={ip}")
    return {"ok": True}


@router.post("/regenerar")
def regenerar(request: Request, rol: str = Form(...), password: str = Form(""), codigo: str = Form("")):
    id_usuario, ip, err = _precheck(request, rol)
    if err:
        return err
    if not mfa.mfa_activo(rol, id_usuario):
        return _error("La verificación en dos pasos no está activa.", 409)
    err = _exigir_password(rol, id_usuario, password, ip) or _exigir_codigo(rol, id_usuario, codigo, ip)
    if err:
        return err
    codigos = mfa.regenerar_recuperacion(rol, id_usuario)
    security.security_logger.info(f"MFA_RECUPERACION_REGENERADA rol={rol} id={id_usuario} ip={ip}")
    return {"ok": True, "codigos": codigos}


# ============================================
# SEGUNDO PASO DEL LOGIN
# ============================================

@router.post("/login")
def login_segundo_paso(request: Request, mfa_token: str = Form(...), codigo: str = Form(...)):
    ip = security._get_ip(request)
    if security.esta_bloqueado(ip, "normal"):
        security.log_rate_blocked(ip, "/mfa/login")
        return security.respuesta_bloqueado()

    pendiente = mfa.leer_token_pendiente(mfa_token)
    if not pendiente:
        return _error("La verificación expiró. Vuelve a iniciar sesión.", 401, expirado=True)
    rol, id_usuario = pendiente["r"], int(pendiente["i"])

    if not mfa.verificar(rol, id_usuario, codigo):
        bloqueado = security.registrar_fallo(ip, "normal")
        security.log_login_fail(ip, rol, str(id_usuario), "mfa: código incorrecto")
        if bloqueado:
            return security.respuesta_bloqueado()
        if mfa.esta_bloqueada(rol, id_usuario):
            return _error("Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", 429, expirado=True)
        return _error("Código incorrecto", 401)

    security.limpiar_bloqueo(ip, "normal")
    security.log_login_ok(ip, rol, f"{id_usuario} (mfa)")

    if rol == "admin":
        from routers import trabajadores
        return trabajadores.finalizar_login_admin(request)
    if rol == "psicologa":
        from routers import psicologa
        return psicologa.finalizar_login_psicologa(request)
    if rol == "trabajador":
        from routers import trabajadores
        fila = trabajadores.cargar_trabajador_login(id_usuario)
        if not fila:
            return _error("Tu cuenta no está disponible.", 403, expirado=True)
        return trabajadores.finalizar_login_trabajador(fila)
    from routers import clientes
    fila = clientes.cargar_cliente_login(id_usuario)
    if not fila:
        return _error("Tu cuenta no está disponible.", 403, expirado=True)
    return clientes.finalizar_login_cliente(fila)


# ============================================
# PÁGINA DE SEGURIDAD
# ============================================

def _avisos_configuracion():
    avisos = []
    if not mfa.mfa_configurado():
        avisos.append("Falta definir MFA_SECRET (mínimo 16 caracteres) en las variables de entorno. "
                      "Sin eso no se puede activar la verificación en dos pasos.")
    if os.getenv("ADMIN_PASSWORD", "admin123") == "admin123":
        avisos.append("ADMIN_PASSWORD está con el valor por defecto público. Cámbialo en las variables de entorno.")
    if os.getenv("PSICO_PASSWORD", "psico2026") == "psico2026":
        avisos.append("PSICO_PASSWORD está con el valor por defecto público. Cámbialo en las variables de entorno.")
    return avisos


@router.get("/seguridad/{rol}", response_class=HTMLResponse)
def pagina_seguridad(request: Request, rol: str):
    if rol not in mfa.ROLES:
        return RedirectResponse(url="/", status_code=302)
    if _identidad(request, rol) is None:
        return RedirectResponse(url=_LOGIN[rol], status_code=302)
    volver_url, volver_txt = _VOLVER[rol]
    return templates.TemplateResponse("seguridad.html", {
        "request": request,
        "rol": rol,
        "volver_url": volver_url,
        "volver_txt": volver_txt,
        "avisos": _avisos_configuracion() if rol == "admin" else [],
    })
