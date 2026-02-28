# 🎯 Instrucciones para Probar: Solicitar Servicio

## ✅ Cambios Realizados

1. **Dashboard del Cliente** - Ahora guarda el ID del cliente en localStorage
2. **Login** - Guarda el ID del cliente automáticamente al iniciar sesión
3. **Formulario de Solicitud** - Obtiene el ID del cliente desde URL o localStorage
4. **Mapa de Trabajadores** - Pasa el ID del cliente al formulario
5. **Backend** - Devuelve el ID del cliente en la respuesta de login

## 📋 Pasos para Probar

### 1. Iniciar el Servidor

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Iniciar Ngrok (si quieres compartir)

```bash
ngrok http 8000
```

### 3. Acceder a la Aplicación

**URL Local:**
```
http://localhost:8000
```

**URL Pública (Ngrok):**
```
https://alta-dynamoelectric-dania.ngrok-free.app
```

### 4. Iniciar Sesión como Cliente

1. Ir a la página principal
2. Hacer clic en "Soy Cliente"
3. Ingresar credenciales:
   - **Email:** cliente@test.com
   - **Password:** cliente123
4. Serás redirigido al Dashboard

### 5. Solicitar un Servicio (Opción 1: Desde el Mapa)

1. En el Dashboard, hacer clic en **"🗺️ Ver Mapa de Trabajadores"**
2. El mapa cargará tu ubicación actual (permitir acceso al GPS)
3. Verás trabajadores cercanos con marcadores en el mapa
4. Hacer clic en un marcador para ver información del trabajador
5. En el popup, hacer clic en **"📋 Solicitar Servicio"**
6. Serás redirigido al formulario con:
   - Trabajador pre-seleccionado
   - Categoría pre-seleccionada
   - Tu ID de cliente ya configurado
7. Completar los detalles:
   - Título del servicio
   - Descripción detallada
   - Dirección completa
   - Ciudad y departamento
   - Fecha programada (opcional)
8. Hacer clic en **"Publicar Solicitud"**
9. Verás mensaje de éxito y serás redirigido a "Mis Solicitudes"

### 6. Solicitar un Servicio (Opción 2: Directamente)

1. En el Dashboard, hacer clic en **"🔍 Solicitar un Servicio"**
2. Seleccionar una categoría (Plomería, Electricidad, etc.)
3. Completar los detalles del servicio
4. Hacer clic en **"Publicar Solicitud"**
5. La solicitud se creará como "pendiente" (sin trabajador asignado)

### 7. Ver Mis Solicitudes

1. En el Dashboard, hacer clic en **"📋 Mis Solicitudes"**
2. Verás todas tus solicitudes con:
   - Estado (Pendiente, Aceptada, En Proceso, Completada, Cancelada)
   - Categoría del servicio
   - Trabajador asignado (si aplica)
   - Fecha de solicitud
   - Opción de cancelar (si está pendiente o aceptada)

## 🔍 Diferencias entre las Opciones

### Solicitud desde el Mapa (con trabajador)
- ✅ Trabajador pre-seleccionado
- ✅ Categoría pre-seleccionada
- ✅ Estado inicial: **"aceptada"**
- ✅ Trabajador asignado automáticamente

### Solicitud Directa (sin trabajador)
- ⚠️ Sin trabajador pre-seleccionado
- ⚠️ Debes elegir categoría manualmente
- ⚠️ Estado inicial: **"pendiente"**
- ⚠️ Trabajador se asigna después

## 📊 Datos de Prueba

### Cliente
- **Email:** cliente@test.com
- **Password:** cliente123

### Trabajador
- **Email:** trabajador@test.com
- **Password:** trabajador123

### Admin
- **Password:** admin123

## 🗺️ Ubicación de Prueba

**Cali, Colombia:**
- Latitud: 3.431608
- Longitud: -76.522041

## ✨ Características Implementadas

1. ✅ Login con autenticación
2. ✅ Dashboard del cliente con estadísticas
3. ✅ Mapa interactivo con trabajadores cercanos
4. ✅ Filtros por categoría y radio de búsqueda
5. ✅ Contacto directo (WhatsApp y llamada)
6. ✅ Solicitud de servicio con trabajador pre-seleccionado
7. ✅ Solicitud de servicio sin trabajador
8. ✅ Historial de solicitudes
9. ✅ Cancelación de solicitudes
10. ✅ Estados de solicitud (pendiente, aceptada, en proceso, completada, cancelada)

## 🐛 Solución de Problemas

### Si no aparecen trabajadores en el mapa:
1. Verificar que el GPS esté habilitado en el navegador
2. Aumentar el radio de búsqueda (10km → 50km)
3. Verificar que hay trabajadores en la base de datos con `disponible = 1`

### Si el ID del cliente es 1 (temporal):
1. Cerrar sesión
2. Volver a iniciar sesión
3. El ID correcto se guardará en localStorage

### Si no se puede crear la solicitud:
1. Verificar que todos los campos estén completos
2. Verificar que se haya seleccionado una categoría
3. Revisar la consola del navegador (F12) para errores

## 🎉 ¡Listo para Presentar!

La funcionalidad está completa y lista para demostrar al jefe. El flujo es intuitivo y profesional.
