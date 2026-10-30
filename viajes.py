"""
Servicios de "viaje" — TalentHub

Transporte, Mudanza y Mensajería se piden con un punto de recogida y un destino, y se
cotizan con un PRECIO FIJO POR VIAJE (no por horas × tarifa como el resto de categorías).

Cada una pide además datos propios:
  - Transporte: vehículo, qué se lleva, ayudantes.
  - Mudanza:    vehículo, qué se traslada, ayudantes, piso de recogida y de destino, ascensor.
  - Mensajería: vehículo, qué se envía y peso aproximado del paquete.

Este módulo concentra las reglas para que el formulario del cliente, la cotización del
trabajador y las pantallas usen exactamente las mismas.
"""
import json
import re
import unicodedata

# Categorías que se piden y se cotizan como "viaje" (comparadas sin tildes ni mayúsculas)
CATEGORIAS_VIAJE = {"transporte", "mudanza", "mensajeria"}

VEHICULOS = {
    "moto": "Moto",
    "carro": "Carro",
    "camioneta": "Camioneta",
    "camion": "Camión",
}

# Mensajería: peso aproximado del paquete
PESOS = {
    "hasta2": "Hasta 2 kg",
    "2a5":    "2 a 5 kg",
    "5a10":   "5 a 10 kg",
    "10a20":  "10 a 20 kg",
    "mas20":  "Más de 20 kg",
}

PISO_MAX = 10   # Mudanza: 0 = casa o primer piso

# Límites de validación
DESTINO_MIN, DESTINO_MAX = 5, 200
CARGA_MIN, CARGA_MAX = 3, 300
PRECIO_VIAJE_MIN, PRECIO_VIAJE_MAX = 2_000, 20_000_000


def _sin_tildes(texto) -> str:
    t = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def tipo_viaje(nombre_categoria):
    """'transporte' | 'mudanza' | 'mensajeria' | None según el nombre de la categoría."""
    n = _sin_tildes(nombre_categoria)
    return n if n in CATEGORIAS_VIAJE else None


def es_categoria_viaje(nombre_categoria) -> bool:
    """True si la categoría se pide con origen/destino y se cotiza por viaje."""
    return tipo_viaje(nombre_categoria) is not None


def _a_bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ("1", "true", "si", "sí", "yes", "on")


def _a_piso(valor) -> int:
    """Piso entre 0 y PISO_MAX. Si no viene o no es válido, 0 (casa / primer piso)."""
    try:
        p = int(valor)
    except (ValueError, TypeError):
        return 0
    return max(0, min(PISO_MAX, p))


def normalizar_detalles_viaje(crudo, categoria=None):
    """
    Valida los datos de un viaje que manda el formulario del cliente.
    `crudo` puede ser un JSON (str) o un dict. `categoria` es el nombre de la categoría
    (decide qué datos propios se exigen); si no se indica se trata como Transporte.

    Devuelve (json_str, None) si todo está bien o (None, "mensaje de error").
    Solo se guardan las claves conocidas, con largo limitado: lo que llegue de más se descarta.
    """
    tipo = tipo_viaje(categoria) or "transporte"

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
        "subtipo": tipo,
        "destino": destino,
        "vehiculo": vehiculo,
        "carga": carga,
        "ayudantes": False,
    }

    if tipo == "mudanza":
        limpio["ayudantes"] = _a_bool(datos.get("ayudantes"))
        limpio["piso_origen"] = _a_piso(datos.get("piso_origen"))
        limpio["piso_destino"] = _a_piso(datos.get("piso_destino"))
        limpio["ascensor"] = _a_bool(datos.get("ascensor"))
    elif tipo == "mensajeria":
        # Un mensajero no necesita ayudantes; el peso sí define el vehículo y el precio
        peso = str(datos.get("peso") or "").strip().lower()
        if peso not in PESOS:
            return None, "Indica el peso aproximado del paquete"
        limpio["peso"] = peso
    else:  # transporte
        limpio["ayudantes"] = _a_bool(datos.get("ayudantes"))

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


def _texto_piso(n) -> str:
    return "casa o primer piso" if not n else f"piso {n}"


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
    ]
    if d.get("subtipo") == "mudanza":
        lineas.append(f"Recogida: {_texto_piso(d.get('piso_origen'))} · Destino: {_texto_piso(d.get('piso_destino'))}")
        lineas.append(f"Ascensor: {'Sí' if d.get('ascensor') else 'No'}")
    if d.get("subtipo") == "mensajeria":
        lineas.append(f"Peso aproximado: {PESOS.get(d.get('peso'), d.get('peso', ''))}")
    if d.get("subtipo") != "mensajeria":
        lineas.append(f"Ayudantes: {'Sí' if d.get('ayudantes') else 'No'}")
    if d.get("distancia_km"):
        lineas.append(f"Distancia aproximada: {d['distancia_km']} km")
    return "\n".join(lineas)


# ─────────────────────────────────────────────────────────────────────────────
# Distancia automática con Mapbox
# ─────────────────────────────────────────────────────────────────────────────

_RE_COORDENADAS = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$")
RELEVANCIA_MINIMA = 0.4   # descarta direcciones que Mapbox solo adivinó


def _coordenadas_en_texto(texto):
    """Si el texto es 'lat, lng' (lo que guarda el GPS del formulario) devuelve (lng, lat)."""
    m = _RE_COORDENADAS.match(str(texto or ""))
    if not m:
        return None
    lat, lng = float(m.group(1)), float(m.group(2))
    if -90 <= lat <= 90 and -180 <= lng <= 180:
        return (lng, lat)
    return None


def _geocodificar(requests, texto, token, timeout, cerca=None):
    """Texto → (lng, lat) con Mapbox Geocoding, limitado a Colombia. None si no se encuentra."""
    from urllib.parse import quote
    params = {"access_token": token, "country": "co", "limit": 1, "language": "es"}
    if cerca:
        params["proximity"] = f"{cerca[0]},{cerca[1]}"   # prioriza lo cercano al origen
    r = requests.get(
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(str(texto), safe='')}.json",
        params=params, timeout=timeout
    )
    r.raise_for_status()
    features = r.json().get("features") or []
    if not features:
        return None
    f = features[0]
    if float(f.get("relevance") or 0) < RELEVANCIA_MINIMA:
        return None
    lng, lat = f["center"]
    return (lng, lat)


def calcular_distancia_mapbox(origen, destino, token, contexto_origen="", timeout=6, requests_mod=None):
    """
    Distancia y tiempo por carretera entre dos direcciones escritas en texto.
    Devuelve {"distancia_km": 12.4, "duracion_min": 25} o None si no se pudo calcular.
    Nunca lanza: el cálculo es un extra y no debe romper nada.
    """
    try:
        if requests_mod is None:
            import requests as requests_mod
        if not token:
            return None

        # Origen: coordenadas del GPS tal cual, o dirección + ciudad
        o = _coordenadas_en_texto(origen)
        if not o:
            consulta = ", ".join(x for x in (str(origen or "").strip(), contexto_origen) if x)
            o = _geocodificar(requests_mod, consulta, token, timeout)
        if not o:
            return None

        # Destino: se busca cerca del origen (si dice otra ciudad, el cliente la escribe en el texto)
        d = _geocodificar(requests_mod, destino, token, timeout, cerca=o)
        if not d:
            return None

        r = requests_mod.get(
            f"https://api.mapbox.com/directions/v5/mapbox/driving/{o[0]},{o[1]};{d[0]},{d[1]}",
            params={"access_token": token, "overview": "false"}, timeout=timeout
        )
        r.raise_for_status()
        rutas = r.json().get("routes") or []
        if not rutas:
            return None
        metros = float(rutas[0]["distance"])
        segundos = float(rutas[0]["duration"])
        return {
            "distancia_km": round(metros / 1000, 1),
            "duracion_min": max(1, round(segundos / 60)),
        }
    except Exception as e:
        print(f"[VIAJE] No se pudo calcular la distancia: {e}")
        return None


def completar_distancia_viaje(id_solicitud, direccion_origen, ciudad, departamento, token):
    """
    Se ejecuta en segundo plano justo después de crear la solicitud: calcula la distancia y la
    agrega a los datos del viaje. Si falla, la solicitud queda igual (el trabajador usa el enlace al mapa).
    """
    conn = None
    try:
        from config import conectar_bd
        conn = conectar_bd()
        if not conn:
            return
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT detalles_servicio FROM solicitudes_servicio WHERE id_solicitud = %s", (id_solicitud,))
        fila = cur.fetchone()
        datos = leer_detalles(fila["detalles_servicio"]) if fila else None
        if not datos or not datos.get("destino"):
            return

        contexto = ", ".join(x for x in (ciudad, departamento) if x)
        res = calcular_distancia_mapbox(direccion_origen, datos["destino"], token, contexto_origen=contexto)
        if not res:
            return

        datos.update(res)
        cur.execute(
            "UPDATE solicitudes_servicio SET detalles_servicio = %s WHERE id_solicitud = %s",
            (json.dumps(datos, ensure_ascii=False), id_solicitud)
        )
        conn.commit()
    except Exception as e:
        print(f"[VIAJE] completar_distancia_viaje #{id_solicitud}: {e}")
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass
