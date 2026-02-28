# 🔐 Sistema de Autenticación - TalentHub

## Descripción

Sistema completo de autenticación con login por correo + contraseña y verificación opcional por SMS para trabajadores y clientes.

## ✨ Características

### Seguridad
- ✅ Hash de contraseñas con bcrypt
- ✅ Tokens de sesión únicos
- ✅ Verificación SMS opcional
- ✅ Control de intentos fallidos
- ✅ Bloqueo temporal por seguridad
- ✅ Cookies HTTP-only

### Funcionalidades
- ✅ Login para trabajadores
- ✅ Login para clientes
- ✅ Verificación por SMS
- ✅ Gestión de sesiones
- ✅ Cierre de sesión
- ✅ Configuración de contraseña

## 📋 Flujo de Autenticación

### Para Trabajadores

1. **Registro** → `/trabajador/registro`
   - Completa formulario con datos
   - Sistema crea cuenta sin contraseña

2. **Configurar Contraseña** (Primera vez)
   - Después del registro, configurar contraseña
   - Mínimo 6 caracteres

3. **Login** → `/trabajador/login`
   - Ingresa correo + contraseña
   - Si SMS está activado → Recibe código
   - Verifica código → Sesión iniciada

4. **Acceso** → `/trabajador/disponibilidad`
   - Panel de trabajador
   - Activar/desactivar disponibilidad

### Para Clientes

1. **Registro** → `/cliente/registro`
   - Completa formulario
   - Configura contraseña

2. **Login** → `/cliente/login`
   - Ingresa correo + contraseña
   - Verificación SMS opcional
   - Acceso al mapa

3. **Acceso** → `/cliente/mapa`
   - Ver trabajadores cercanos
   - Solicitar servicios

## 🔧 Configuración

### Base de Datos

Tablas creadas automáticamente:
- `codigos_verificacion` - Códigos SMS
- `sesiones` - Tokens de sesión
- `intentos_login` - Log de intentos
- `configuracion_seguridad` - Parámetros

### Parámetros de Seguridad

En tabla `configuracion_seguridad`:

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `max_intentos_login` | 5 | Intentos antes de bloquear |
| `tiempo_bloqueo_minutos` | 30 | Duración del bloqueo |
| `duracion_sesion_horas` | 24 | Duración de sesión |
| `longitud_codigo_sms` | 6 | Dígitos del código SMS |
| `expiracion_codigo_minutos` | 10 | Validez del código |
| `requiere_verificacion_sms` | 1 | Activar/desactivar SMS |

### Activar/Desactivar SMS

```sql
-- Desactivar verificación SMS
UPDATE configuracion_seguridad 
SET valor = '0' 
WHERE clave = 'requiere_verificacion_sms';

-- Activar verificación SMS
UPDATE configuracion_seguridad 
SET valor = '1' 
WHERE clave = 'requiere_verificacion_sms';
```

## 📱 Integración SMS

### Actualmente (Desarrollo)
- Códigos se muestran en consola
- No se envían SMS reales

### Para Producción

Integrar con servicio de SMS (Twilio recomendado):

```python
# En auth.py, función enviar_sms()

from twilio.rest import Client

def enviar_sms(telefono: str, codigo: str) -> bool:
    account_sid = 'TU_ACCOUNT_SID'
    auth_token = 'TU_AUTH_TOKEN'
    
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f'Tu código de verificación TalentHub es: {codigo}',
        from_='+1234567890',  # Tu número Twilio
        to=telefono
    )
    
    return message.sid is not None
```

## 🔑 Endpoints API

### Trabajadores

#### GET `/trabajador/login`
Muestra página de login

#### POST `/trabajador/login`
Autentica trabajador

**Body**:
```json
{
  "correo": "trabajador@email.com",
  "password": "mipassword"
}
```

**Respuesta** (con SMS):
```json
{
  "requiere_verificacion_sms": true,
  "id_trabajador": 1,
  "mensaje": "Código enviado"
}
```

**Respuesta** (sin SMS):
```json
{
  "requiere_verificacion_sms": false,
  "mensaje": "Login exitoso",
  "redirect": "/trabajador/disponibilidad"
}
```

#### POST `/trabajador/verificar-sms`
Verifica código SMS

**Body**:
```json
{
  "id_trabajador": 1,
  "codigo": "123456"
}
```

#### POST `/trabajador/reenviar-codigo`
Reenvía código SMS

#### GET `/trabajador/logout`
Cierra sesión

#### POST `/trabajador/configurar-password`
Configura contraseña inicial

### Clientes

Mismos endpoints con prefijo `/cliente/`

## 🛡️ Seguridad

### Contraseñas
- Hash con bcrypt (salt automático)
- Nunca se almacenan en texto plano
- Mínimo 6 caracteres

### Sesiones
- Tokens únicos de 32 bytes
- Almacenados en cookies HTTP-only
- Expiración automática (24h)
- Un token por sesión

### Códigos SMS
- 6 dígitos aleatorios
- Válidos por 10 minutos
- Un solo uso
- Se invalidan al verificar

### Protección contra Ataques
- Límite de intentos fallidos
- Bloqueo temporal de cuenta
- Log de todos los intentos
- Validación de entrada

## 📊 Monitoreo

### Ver Intentos de Login

```sql
SELECT * FROM intentos_login 
ORDER BY fecha_intento DESC 
LIMIT 50;
```

### Ver Sesiones Activas

```sql
SELECT s.*, 
       CASE s.tipo_usuario
           WHEN 'trabajador' THEN p.nombre_completo
           WHEN 'cliente' THEN c.nombre_completo
       END as nombre
FROM sesiones s
LEFT JOIN personas p ON s.tipo_usuario = 'trabajador' AND s.id_usuario = p.id_persona
LEFT JOIN clientes c ON s.tipo_usuario = 'cliente' AND s.id_usuario = c.id_cliente
WHERE s.activa = 1 AND s.fecha_expiracion > NOW();
```

### Ver Códigos SMS Pendientes

```sql
SELECT * FROM codigos_verificacion
WHERE usado = 0 AND fecha_expiracion > NOW()
ORDER BY fecha_creacion DESC;
```

## 🔄 Flujo Técnico

```
1. Usuario ingresa correo + contraseña
   ↓
2. Sistema verifica credenciales
   ↓
3. ¿Requiere SMS?
   ├─ SÍ → Genera código → Envía SMS → Espera verificación
   └─ NO → Crea sesión → Redirige a panel
   ↓
4. Usuario verifica código (si aplica)
   ↓
5. Sistema crea sesión con token
   ↓
6. Token guardado en cookie
   ↓
7. Usuario accede a rutas protegidas
```

## 🚀 Próximas Mejoras

- [ ] Recuperación de contraseña por correo
- [ ] Autenticación de dos factores (2FA)
- [ ] Login con Google/Facebook
- [ ] Recordar dispositivo
- [ ] Notificaciones de login sospechoso
- [ ] Historial de sesiones
- [ ] Cambio de contraseña
- [ ] Verificación de correo electrónico

## 📞 Soporte

Para problemas con autenticación:
1. Verifica que las tablas estén creadas
2. Confirma que el módulo `auth.py` esté importado
3. Revisa logs de intentos de login
4. Verifica configuración de seguridad

---

**Versión**: 1.0  
**Última actualización**: 2026-02-27
