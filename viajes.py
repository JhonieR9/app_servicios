"""
Servicios de "viaje" — TalentHub

Transporte, Mudanza y Mensajería se piden con un punto de recogida y un destino, y se
cotizan con un PRECIO FIJO POR VIAJE (no por horas × tarifa como el resto de categorías).

Este módulo concentra las reglas para que el formulario del cliente, la cotización del
trabajador y las pantallas usen exactamente las mismas.
"""
import json
import unicodedata

# Categorías que se piden y se cotizan como "viaje" (comparadas sin tildes ni mayúsculas)
CATEGORIAS_VIAJE = {"transporte", "mudanza", "mensajeria"}

VEHICULOS = {
    "moto": "Moto",
    "carro": "Carro",
    "camioneta": "Camioneta",
    "camion": "Camión",
}

# Límites de validación
DESTINO_MIN, DESTINO_MAX = 5, 200
CARGA_MIN, CARGA_MAX = 3, 300
PRECIO_VIAJE_MIN, PRECIO_VIAJE_MAX = 2_000, 20_000_000


def _sin_tildes(texto) -> str:
    t = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def es_categoria_viaje(nombre_categoria) -> bool:
    """True si la categoría se pide con origen/destino y se cotiza por viaje."""
    return _sin_tildes(nombre_categoria) in CATEGORIAS_VIAJE


def _a_bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ("1", "true", "si", "sí", "yes", "on")


def normalizar_detalles_viaje(crudo):
    """
    Valida los datos de un viaje que manda el formulario del cliente.
    `crudo` puede ser un JSON (str) o un dict.

    Devuelve (json_str, None) si todo está bien o (None, "mensaje de error").
    Solo se guardan las claves conocidas, con largo limitado: lo que llegue de más se descarta.
    """
    if crudo is None or (isinstance(crudo, str) and not crudo.strip()):
        return None, "Indica el destino, el tipo de vehículo y qué se va a transportar"

    if isinstance(crudo, str):
        try:
            datos = json.loads(crudo)
        except (ValueError, TypeError):
            return None, "Los datos del viaje no son válidos"
    else:
        datos = crudo
    if not isinstance(datos, dict):
        return None, "Los datos del viaje no son válidos"

    destino = str(datos.get("destino") or "").strip()
    if not (DESTINO_MIN <= len(destino) <= DESTINO_MAX):
        return None, "Escribe la dirección de destino (mínimo 5 caracteres)"

    vehiculo = _sin_tildes(datos.get("vehiculo"))
    if vehiculo not in VEHICULOS:
        return None, "Elige el tipo de vehículo"

    carga = str(datos.get("carga") or "").strip()
    if not (CARGA_MIN <= len(carga) <= CARGA_MAX):
        return None, "Cuéntanos qué se va a transportar (mínimo 3 caracteres)"

    limpio = {
        "tipo": "viaje",
        "destino": destino,
        "vehiculo": vehiculo,
        "carga": carga,
        "ayudantes": _a_bool(datos.get("ayudantes")),
    }
    return json.dumps(limpio, ensure_ascii=False), None


def leer_detalles(texto):
    """Lee el JSON guardado en BD de forma tolerante: devuelve un dict o None, nunca lanza."""
    if not texto:
        return None
    try:
        d = json.loads(texto) if isinstance(texto, str) else texto
        return d if isinstance(d, dict) else None
    except (ValueError, TypeError):
        return None


def resumen_texto_viaje(detalles) -> str:
    """Texto legible del viaje. Sirve de respaldo (se agrega a la descripción) si no se pudo guardar el JSON."""
    d = leer_detalles(detalles) if not isinstance(detalles, dict) else detalles
    if not d:
        return ""
    lineas = [
        "",
        "— Datos del viaje —",
        f"Destino: {d.get('destino', '')}",
        f"Vehículo: {VEHICULOS.get(d.get('vehiculo'), d.get('vehiculo', ''))}",
        f"Se transporta: {d.get('carga', '')}",
        f"Ayudantes: {'Sí' if d.get('ayudantes') else 'No'}",
    ]
    return "\n".join(lineas)
