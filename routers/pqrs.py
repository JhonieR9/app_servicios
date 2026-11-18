"""
Canal de peticiones, quejas, reclamos (PQRS) con número de radicado, fecha y hora, y seguimiento.
Cubre también las consultas y reclamos de datos personales (Ley 1581 de 2012) y las
solicitudes de retracto (Ley 1480 de 2011, art. 47). Ley 2439 de 2024: canales con trazabilidad.
"""

import html
import threading

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import auth
import legal
import security

router = APIRouter(tags=["pqrs"])
templates = Jinja2Templates(directory="templates")


def _fmt(dt):
    try:
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(dt or "")


def _es_admin(request: Request) -> bool:
    from routers.trabajadores import verificar_admin
    return verificar_admin(request)


def _correo_async(destino, asunto, cuerpo_html):
    threading.Thread(target=lambda: auth._enviar_gmail(destino, asunto, cuerpo_html), daemon=True).start()


# ============================================
# PÚBLICO
# ============================================

@router.get("/pqrs", response_class=HTMLResponse)
def pagina_pqrs(request: Request):
    inicio_url, inicio_txt = legal.destino_inicio(request)
    return templates.TemplateResponse("pqrs.html", {
        "request": request, "legal": legal.datos_legales(), "tipos": legal.TIPOS_PQRS,
        "tipo_inicial": request.query_params.get("tipo", ""),
        "inicio_url": inicio_url, "inicio_txt": inicio_txt,
    })


@router.post("/pqrs")
def enviar_pqrs(
    request: Request,
    tipo: str = Form(""),
    nombre: str = Form(""),
    correo: str = Form(""),
    telefono: str = Form(""),
    id_solicitud: str = Form(""),
    mensaje: str = Form(""),
):
    ip = security._get_ip(request)
    radicado, fecha, error = legal.crear_pqrs(tipo, nombre, correo, telefono, id_solicitud, mensaje, ip)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    tipo_txt = legal.TIPOS_PQRS.get(tipo, tipo)
    cuerpo = (
        "<div style='font-family:Segoe UI,Arial,sans-serif;max-width:520px;margin:auto;color:#334155'>"
        "<h2 style='color:#0f172a'>Recibimos tu solicitud</h2>"
        f"<p>Hola {html.escape(nombre.strip())}, registramos tu solicitud ({html.escape(tipo_txt)}).</p>"
        f"<p><strong>Número de radicado:</strong> {html.escape(radicado)}<br>"
        f"<strong>Fecha y hora de recepción:</strong> {_fmt(fecha)}</p>"
        "<p>Te responderemos a este correo dentro de los quince (15) días hábiles siguientes. "
        "Puedes consultar el estado en la sección Peticiones, quejas y reclamos de TalentHub, "
        "con tu radicado y este correo.</p></div>"
    )
    _correo_async(correo.strip().lower(), f"TalentHub: radicado {radicado}", cuerpo)
    return {"ok": True, "radicado": radicado, "fecha": _fmt(fecha)}


@router.get("/pqrs/consulta", response_class=HTMLResponse)
def pagina_consulta(request: Request):
    inicio_url, inicio_txt = legal.destino_inicio(request)
    return templates.TemplateResponse("pqrs_consulta.html", {"request": request, "legal": legal.datos_legales(),
                                                            "inicio_url": inicio_url, "inicio_txt": inicio_txt})


@router.post("/pqrs/consulta")
def consultar(request: Request, radicado: str = Form(""), correo: str = Form("")):
    ip = security._get_ip(request)
    if security.esta_bloqueado(ip, "normal"):
        security.log_rate_blocked(ip, "/pqrs/consulta")
        return security.respuesta_bloqueado()
    fila = legal.consultar_pqrs(radicado, correo)
    if not fila:
        security.registrar_fallo(ip, "normal")
        return JSONResponse({"error": "No encontramos una solicitud con ese radicado y correo."}, status_code=404)
    return {
        "radicado": fila["radicado"],
        "tipo": legal.TIPOS_PQRS.get(fila["tipo"], fila["tipo"]),
        "estado": legal.ESTADOS_PQRS.get(fila["estado"], fila["estado"]),
        "fecha": _fmt(fila["fecha_creacion"]),
        "respuesta": fila.get("respuesta") or "",
        "fecha_respuesta": _fmt(fila["fecha_respuesta"]) if fila.get("fecha_respuesta") else "",
    }


# ============================================
# ADMINISTRADOR
# ============================================

@router.get("/pqrs/admin", response_class=HTMLResponse)
def pagina_admin(request: Request):
    if not _es_admin(request):
        return RedirectResponse(url="/trabajador/admin/login", status_code=302)
    return templates.TemplateResponse("trabajadores/admin_pqrs.html", {"request": request})


@router.get("/pqrs/admin/listar")
def listar(request: Request, estado: str = ""):
    if not _es_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)
    filas = legal.listar_pqrs(estado or None)
    salida = []
    for f in filas:
        salida.append({
            "id_pqrs": f["id_pqrs"], "radicado": f["radicado"],
            "tipo": legal.TIPOS_PQRS.get(f["tipo"], f["tipo"]),
            "estado": f["estado"], "nombre": f["nombre"], "correo": f["correo"],
            "telefono": f.get("telefono") or "", "id_solicitud": f.get("id_solicitud") or "",
            "mensaje": f["mensaje"], "respuesta": f.get("respuesta") or "",
            "fecha": _fmt(f["fecha_creacion"]),
            "fecha_respuesta": _fmt(f["fecha_respuesta"]) if f.get("fecha_respuesta") else "",
        })
    return {"pqrs": salida}


@router.post("/pqrs/admin/responder")
def responder(request: Request, id_pqrs: int = Form(...), estado: str = Form(...), respuesta: str = Form("")):
    if not _es_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)
    if estado == "resuelto" and not respuesta.strip():
        return JSONResponse({"error": "Escribe la respuesta antes de marcarla como resuelta."}, status_code=400)
    fila = legal.responder_pqrs(id_pqrs, estado, respuesta)
    if not fila:
        return JSONResponse({"error": "Solicitud no encontrada o estado inválido."}, status_code=404)
    if respuesta.strip():
        cuerpo = (
            "<div style='font-family:Segoe UI,Arial,sans-serif;max-width:520px;margin:auto;color:#334155'>"
            f"<h2 style='color:#0f172a'>Respuesta a tu solicitud {html.escape(fila['radicado'])}</h2>"
            f"<p style='white-space:pre-wrap'>{html.escape(respuesta.strip())}</p>"
            "<p>Si no estás conforme, puedes acudir a la Superintendencia de Industria y Comercio (sic.gov.co).</p></div>"
        )
        _correo_async(fila["correo"], f"TalentHub: respuesta a tu solicitud {fila['radicado']}", cuerpo)
    security.security_logger.info(f"PQRS_ACTUALIZADA radicado={fila['radicado']} estado={estado}")
    return {"ok": True}
