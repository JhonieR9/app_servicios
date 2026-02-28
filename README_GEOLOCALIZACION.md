# 🗺️ Sistema de Geolocalización - TalentHub

## Descripción
Sistema de ubicación en tiempo real para conectar clientes con trabajadores cercanos, similar a DiDi/Uber.

## Características

### 1. Geolocalización de Trabajadores
- Los trabajadores pueden activar/desactivar su ubicación
- Actualización de coordenadas GPS en tiempo real
- Almacenamiento de latitud y longitud en la base de datos

### 2. Búsqueda por Proximidad
- Clientes pueden ver trabajadores cercanos en un mapa
- Cálculo de distancia en kilómetros
- Filtrado por categoría de servicio

### 3. Mapa Interactivo
- Visualización con Google Maps / Leaflet
- Marcadores para trabajadores disponibles
- Información al hacer clic en marcador

## Tablas de Base de Datos

### Tabla: `disponibilidad_trabajador`
```sql
CREATE TABLE disponibilidad_trabajador (
    id_disponibilidad INT PRIMARY KEY AUTO_INCREMENT,
    id_trabajador INT NOT NULL,
    disponible BOOLEAN DEFAULT 0,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona)
);
```

## Endpoints API

### Trabajadores

#### `POST /trabajador/disponibilidad/actualizar`
Actualiza la ubicación y disponibilidad del trabajador.

**Parámetros:**
- `id_trabajador` (int): ID del trabajador
- `disponible` (bool): Estado de disponibilidad
- `latitud` (float): Coordenada latitud
- `longitud` (float): Coordenada longitud

**Respuesta:**
```json
{
    "mensaje": "Disponibilidad actualizada"
}
```

### Clientes

#### `GET /cliente/trabajadores/cercanos`
Obtiene trabajadores disponibles cerca de una ubicación.

**Parámetros:**
- `latitud` (float): Ubicación del cliente
- `longitud` (float): Ubicación del cliente
- `id_categoria` (int, opcional): Filtrar por categoría
- `radio_km` (float, opcional): Radio de búsqueda en km (default: 5)

**Respuesta:**
```json
{
    "trabajadores": [
        {
            "id_persona": 1,
            "nombre_completo": "Juan Pérez",
            "distancia_km": 2.5,
            "latitud": 4.6097,
            "longitud": -74.0817,
            "calificacion": 4.8,
            "servicios_completados": 45
        }
    ]
}
```

#### `GET /cliente/mapa`
Muestra página con mapa interactivo de trabajadores.

## Uso del Sistema

### Para Trabajadores

1. **Activar ubicación:**
```javascript
// Obtener ubicación del navegador
navigator.geolocation.getCurrentPosition(function(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    
    // Enviar al servidor
    fetch('/trabajador/disponibilidad/actualizar', {
        method: 'POST',
        body: new FormData({
            id_trabajador: 1,
            disponible: true,
            latitud: lat,
            longitud: lng
        })
    });
});
```

2. **Desactivar disponibilidad:**
```javascript
fetch('/trabajador/disponibilidad/actualizar', {
    method: 'POST',
    body: new FormData({
        id_trabajador: 1,
        disponible: false
    })
});
```

### Para Clientes

1. **Ver trabajadores cercanos:**
```javascript
// Obtener ubicación del cliente
navigator.geolocation.getCurrentPosition(function(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    
    // Buscar trabajadores cercanos
    fetch(`/cliente/trabajadores/cercanos?latitud=${lat}&longitud=${lng}&radio_km=5`)
        .then(response => response.json())
        .then(data => {
            console.log('Trabajadores cercanos:', data.trabajadores);
        });
});
```

## Cálculo de Distancia

Usamos la fórmula de Haversine para calcular distancia entre dos puntos GPS:

```python
import math

def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula distancia en km entre dos coordenadas GPS.
    
    Args:
        lat1, lon1: Coordenadas del punto 1
        lat2, lon2: Coordenadas del punto 2
    
    Returns:
        float: Distancia en kilómetros
    """
    R = 6371  # Radio de la Tierra en km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia = R * c
    
    return round(distancia, 2)
```

## Seguridad y Privacidad

1. **Permisos de ubicación:** Siempre pedir permiso al usuario
2. **Precisión:** Usar precisión media para ahorrar batería
3. **Actualización:** Actualizar cada 30 segundos cuando está activo
4. **Privacidad:** No mostrar ubicación exacta, solo aproximada

## Próximas Mejoras

- [ ] Tracking en tiempo real durante servicio
- [ ] Historial de ubicaciones
- [ ] Rutas optimizadas
- [ ] Notificaciones de proximidad
- [ ] Modo offline con caché

## Tecnologías Utilizadas

- **Backend:** FastAPI + MySQL
- **Frontend:** JavaScript Geolocation API
- **Mapas:** Leaflet.js (open source) o Google Maps API
- **Cálculos:** Fórmula de Haversine

## Ejemplo de Coordenadas (Bogotá)

- Centro: 4.7110° N, 74.0721° W
- Norte: 4.8° N
- Sur: 4.5° N
- Radio típico: 5-10 km
