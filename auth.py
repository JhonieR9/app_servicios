"""
Módulo de Autenticación para TalentHub
Maneja login, verificación SMS, sesiones y seguridad
"""

import bcrypt
import secrets
import random
from datetime import datetime, timedelta
import mysql.connector
from typing import Optional, Dict, Tuple
from config import DB_CONFIG

def conectar_bd():
    """Establece conexión con la base de datos"""
    return mysql.connector.connect(**DB_CONFIG)

# ============================================
# FUNCIONES DE HASH Y VERIFICACIÓN
# ============================================

def hash_password(password: str) -> str:
    """Genera hash de contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verificar_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# ============================================
# FUNCIONES DE CÓDIGOS SMS
# ============================================

def generar_codigo_sms() -> str:
    """Genera código de 4 dígitos para verificación"""
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def crear_codigo_verificacion(tipo_usuario: str, id_usuario: int, telefono: str, tipo_verificacion: str = 'login') -> str:
    """
    Crea un código de verificación SMS
    
    Args:
        tipo_usuario: 'trabajador' o 'cliente'
        id_usuario: ID del usuario
        telefono: Número de teléfono
        tipo_verificacion: 'registro', 'login' o 'recuperacion'
    
    Returns:
        Código generado
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    codigo = generar_codigo_sms()
    expiracion = datetime.now() + timedelta(minutes=10)
    
    cursor.execute("""
        INSERT INTO codigos_verificacion 
        (tipo_usuario, id_usuario, telefono, codigo, tipo_verificacion, fecha_expiracion)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (tipo_usuario, id_usuario, telefono, codigo, tipo_verificacion, expiracion))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return codigo

def verificar_codigo_sms(tipo_usuario: str, id_usuario: int, codigo: str) -> Tuple[bool, str]:
    """
    Verifica un código SMS
    
    Returns:
        (valido, mensaje)
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM codigos_verificacion
        WHERE tipo_usuario = %s AND id_usuario = %s AND codigo = %s
        AND usado = 0 AND fecha_expiracion > NOW()
        ORDER BY fecha_creacion DESC
        LIMIT 1
    """, (tipo_usuario, id_usuario, codigo))
    
    resultado = cursor.fetchone()
    
    if not resultado:
        cursor.close()
        conexion.close()
        return False, "Código inválido o expirado"
    
    # Marcar como usado
    cursor.execute("""
        UPDATE codigos_verificacion
        SET usado = 1, fecha_uso = NOW()
        WHERE id_codigo = %s
    """, (resultado['id_codigo'],))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return True, "Código verificado correctamente"

# ============================================
# FUNCIONES DE SESIÓN
# ============================================

def generar_token() -> str:
    """Genera token único para sesión"""
    return secrets.token_urlsafe(32)

def crear_sesion(tipo_usuario: str, id_usuario: int, ip_address: str = None, user_agent: str = None) -> str:
    """
    Crea una nueva sesión
    
    Returns:
        Token de sesión
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    token = generar_token()
    expiracion = datetime.now() + timedelta(days=7)
    
    cursor.execute("""
        INSERT INTO sesiones
        (tipo_usuario, id_usuario, token, ip_address, user_agent, fecha_expiracion)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (tipo_usuario, id_usuario, token, ip_address, user_agent, expiracion))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return token

def verificar_sesion(token: str) -> Optional[Dict]:
    """
    Verifica si una sesión es válida
    
    Returns:
        Datos de la sesión o None
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM sesiones
        WHERE token = %s AND activa = 1 AND fecha_expiracion > NOW()
    """, (token,))
    
    sesion = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    return sesion

def cerrar_sesion(token: str):
    """Cierra una sesión"""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    cursor.execute("""
        UPDATE sesiones
        SET activa = 0
        WHERE token = %s
    """, (token,))
    
    conexion.commit()
    cursor.close()
    conexion.close()

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def autenticar_trabajador(correo: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Autentica un trabajador
    
    Returns:
        (exitoso, datos_trabajador, mensaje)
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    # Buscar trabajador por correo
    cursor.execute("""
        SELECT p.*, c.correo, t.telefono
        FROM personas p
        INNER JOIN correo_persona c ON p.id_persona = c.id_persona
        LEFT JOIN telefono_persona t ON p.id_persona = t.id_persona
        WHERE c.correo = %s AND (p.estado = 'activo' OR p.estado IS NULL)
        LIMIT 1
    """, (correo,))
    
    trabajador = cursor.fetchone()
    
    if not trabajador:
        cursor.close()
        conexion.close()
        return False, None, "Correo no registrado"
    
    # Verificar si tiene contraseña configurada
    if not trabajador.get('password_hash'):
        cursor.close()
        conexion.close()
        return False, None, "Debes configurar tu contraseña primero"
    
    # Verificar contraseña
    if not verificar_password(password, trabajador['password_hash']):
        # Registrar intento fallido
        cursor.execute("""
            UPDATE personas
            SET intentos_fallidos = intentos_fallidos + 1
            WHERE id_persona = %s
        """, (trabajador['id_persona'],))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return False, None, "Contraseña incorrecta"
    
    # Resetear intentos fallidos
    cursor.execute("""
        UPDATE personas
        SET intentos_fallidos = 0, ultimo_login = NOW()
        WHERE id_persona = %s
    """, (trabajador['id_persona'],))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    return True, trabajador, "Autenticación exitosa"

def autenticar_cliente(correo: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Autentica un cliente
    
    Returns:
        (exitoso, datos_cliente, mensaje)
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    # Buscar cliente por correo
    cursor.execute("""
        SELECT c.*, e.correo, t.telefono
        FROM clientes c
        INNER JOIN correo_cliente e ON c.id_cliente = e.id_cliente
        LEFT JOIN telefono_cliente t ON c.id_cliente = t.id_cliente
        WHERE e.correo = %s AND c.estado = 'activo'
        LIMIT 1
    """, (correo,))
    
    cliente = cursor.fetchone()
    
    if not cliente:
        cursor.close()
        conexion.close()
        return False, None, "Correo no registrado"
    
    # Verificar si tiene contraseña configurada
    if not cliente.get('password_hash'):
        cursor.close()
        conexion.close()
        return False, None, "Debes configurar tu contraseña primero"
    
    # Verificar contraseña
    if not verificar_password(password, cliente['password_hash']):
        # Registrar intento fallido
        cursor.execute("""
            UPDATE clientes
            SET intentos_fallidos = intentos_fallidos + 1
            WHERE id_cliente = %s
        """, (cliente['id_cliente'],))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return False, None, "Contraseña incorrecta"
    
    # Resetear intentos fallidos
    cursor.execute("""
        UPDATE clientes
        SET intentos_fallidos = 0, ultimo_login = NOW()
        WHERE id_cliente = %s
    """, (cliente['id_cliente'],))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    return True, cliente, "Autenticación exitosa"

# ============================================
# FUNCIONES DE CONFIGURACIÓN DE CONTRASEÑA
# ============================================

def configurar_password_trabajador(id_persona: int, password: str) -> bool:
    """Configura la contraseña de un trabajador"""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute("""
        UPDATE personas
        SET password_hash = %s
        WHERE id_persona = %s
    """, (password_hash, id_persona))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return True

def configurar_password_cliente(id_cliente: int, password: str) -> bool:
    """Configura la contraseña de un cliente"""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute("""
        UPDATE clientes
        SET password_hash = %s
        WHERE id_cliente = %s
    """, (password_hash, id_cliente))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return True

# ============================================
# FUNCIÓN DE ENVÍO DE SMS (SIMULADO)
# ============================================

def enviar_sms(telefono: str, codigo: str) -> bool:
    """
    Envía SMS con código de verificación
    
    NOTA: Esta es una versión simulada.
    En producción, integrar con Twilio, AWS SNS, etc.
    """
    print(f"\n{'='*50}")
    print(f"📱 SMS ENVIADO A: {telefono}")
    print(f"🔐 CÓDIGO: {codigo}")
    print(f"{'='*50}\n")
    
    # TODO: Integrar con servicio real de SMS
    # Ejemplo con Twilio:
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=f"Tu código de verificación es: {codigo}",
    #     from_='+1234567890',
    #     to=telefono
    # )
    
    return True

# ============================================
# RECUPERACIÓN DE CONTRASEÑA POR EMAIL
# ============================================

def crear_token_recuperacion(tipo_usuario: str, correo: str) -> Optional[str]:
    """
    Busca el usuario por correo, crea un token de recuperación y lo guarda.
    Retorna el token si el correo existe, None si no.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    try:
        if tipo_usuario == 'trabajador':
            cursor.execute("""
                SELECT p.id_persona AS id_usuario, cp.correo
                FROM personas p
                INNER JOIN correo_persona cp ON p.id_persona = cp.id_persona
                WHERE cp.correo = %s AND (p.estado = 'activo' OR p.estado IS NULL)
                LIMIT 1
            """, (correo,))
        else:
            cursor.execute("""
                SELECT c.id_cliente AS id_usuario, ec.correo
                FROM clientes c
                INNER JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente
                WHERE ec.correo = %s AND c.estado = 'activo'
                LIMIT 1
            """, (correo,))

        usuario = cursor.fetchone()
        if not usuario:
            return None

        token = secrets.token_urlsafe(32)
        expiracion = datetime.now() + timedelta(hours=1)

        cursor.execute("""
            INSERT INTO tokens_recuperacion
            (tipo_usuario, id_usuario, correo, token, fecha_expiracion)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_usuario, usuario['id_usuario'], correo, token, expiracion))
        conexion.commit()
        return token

    finally:
        cursor.close()
        conexion.close()


def verificar_token_recuperacion(token: str) -> Optional[Dict]:
    """
    Verifica que el token sea válido y no haya expirado.
    Retorna los datos del token o None.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM tokens_recuperacion
            WHERE token = %s AND usado = 0 AND fecha_expiracion > NOW()
            LIMIT 1
        """, (token,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


def consumir_token_recuperacion(token: str, nueva_password: str) -> bool:
    """
    Valida el token, actualiza la contraseña y marca el token como usado.
    Retorna True si fue exitoso.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM tokens_recuperacion
            WHERE token = %s AND usado = 0 AND fecha_expiracion > NOW()
            LIMIT 1
        """, (token,))
        datos = cursor.fetchone()
        if not datos:
            return False

        password_hash = hash_password(nueva_password)

        if datos['tipo_usuario'] == 'trabajador':
            cursor.execute(
                "UPDATE personas SET password_hash = %s WHERE id_persona = %s",
                (password_hash, datos['id_usuario'])
            )
        else:
            cursor.execute(
                "UPDATE clientes SET password_hash = %s WHERE id_cliente = %s",
                (password_hash, datos['id_usuario'])
            )

        cursor.execute(
            "UPDATE tokens_recuperacion SET usado = 1 WHERE id_token = %s",
            (datos['id_token'],)
        )
        conexion.commit()
        return True
    finally:
        cursor.close()
        conexion.close()


# ============================================
# FUNCIÓN CENTRAL DE ENVÍO DE EMAIL (RESEND API)
# ============================================

def enviar_codigo_verificacion_email(correo: str, codigo: str) -> bool:
    """Envía un código de 4 dígitos por email para verificar la cuenta"""
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="420" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#059669,#0891b2);
                     padding:28px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:8px;">🔐</div>
            <h1 style="margin:0;color:white;font-size:1.3rem;font-weight:800;">
              Código de verificación
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 28px;text-align:center;">
            <p style="color:#374151;font-size:0.95rem;margin:0 0 24px;">
              Tu código de verificación es:
            </p>
            <div style="background:#f0fdf4;border:2px solid #bbf7d0;border-radius:16px;
                        padding:20px;display:inline-block;margin-bottom:24px;">
              <span style="font-size:2.5rem;font-weight:900;letter-spacing:12px;color:#059669;">
                {codigo}
              </span>
            </div>
            <p style="color:#64748b;font-size:0.82rem;margin:0;">
              Este código expira en 10 minutos.<br>
              Si no solicitaste esto, ignora este correo.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    return _enviar_gmail(correo, f"Tu código TalentHub: {codigo}", html)


def _enviar_gmail(destinatario: str, asunto: str, html: str) -> bool:
    """
    Envía un email usando Resend API (HTTP).
    Requiere variable de entorno: RESEND_API_KEY.
    Fallback a consola si no está configurada.
    Mantiene nombre _enviar_gmail por compatibilidad con el resto del código.
    """
    import os
    import requests as _req

    resend_key = os.getenv("RESEND_API_KEY", "")
    gmail_user = os.getenv("GMAIL_USER", "")

    if not resend_key:
        print(f"\n{'='*60}")
        print(f"[EMAIL] Sin RESEND_API_KEY — modo consola")
        print(f"   Para: {destinatario}")
        print(f"   Asunto: {asunto}")
        print(f"{'='*60}\n")
        return True

    # Remitente: dominio verificado en Resend
    from_email = "noreply@talenthubcol.com"

    try:
        resp = _req.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"TalentHub <{from_email}>",
                "to": [destinatario],
                "subject": asunto,
                "html": html
            },
            timeout=15
        )

        if resp.status_code in (200, 201):
            print(f"[EMAIL] ✅ Enviado a {destinatario} via Resend")
            return True
        else:
            print(f"[EMAIL] ❌ Resend error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"[EMAIL] ❌ Error Resend: {e}")
        return False


# ============================================
# RECUPERACIÓN DE CONTRASEÑA POR EMAIL
# ============================================

def enviar_email_recuperacion(correo: str, token: str, tipo_usuario: str, base_url: str) -> bool:
    """Envía el correo de recuperación de contraseña via Gmail SMTP."""
    ruta = "trabajador" if tipo_usuario == "trabajador" else "cliente"
    link = f"{base_url}/{ruta}/recuperar/nueva-password?token={token}"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);
                     padding:32px 28px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:8px;">&#128272;</div>
            <h1 style="margin:0;color:white;font-size:1.4rem;font-weight:800;">
              Recuperar contrasena
            </h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.8);font-size:0.85rem;">TalentHub</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 28px;">
            <p style="color:#374151;font-size:0.95rem;line-height:1.7;margin:0 0 24px;">
              Recibimos una solicitud para restablecer la contrasena de tu cuenta.
              Haz clic en el boton para crear una nueva. <strong>Expira en 1 hora.</strong>
            </p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center" style="padding:8px 0 28px;">
                  <a href="{link}"
                     style="display:inline-block;background:#4f46e5;color:white;
                            text-decoration:none;padding:14px 32px;border-radius:12px;
                            font-weight:700;font-size:1rem;">
                    Restablecer contrasena
                  </a>
                </td>
              </tr>
            </table>
            <p style="color:#9ca3af;font-size:0.78rem;line-height:1.6;margin:0;
                      border-top:1px solid #f3f4f6;padding-top:20px;">
              Si no solicitaste esto, ignora este correo.<br>
              O copia: <span style="color:#6366f1;word-break:break-all;">{link}</span>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _enviar_gmail(correo, "Recuperar contrasena - TalentHub", html)


# ============================================
# NOTIFICACIONES DE SOLICITUD POR EMAIL
# ============================================

def notificar_nueva_solicitud(
    correo_trabajador: str,
    nombre_trabajador: str,
    nombre_cliente: str,
    categoria: str,
    descripcion: str,
    ciudad: str,
    id_solicitud: int,
    base_url: str
) -> bool:
    """Envía email al trabajador cuando llega una nueva solicitud."""
    link = f"{base_url}/trabajador/panel"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);
                     padding:28px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:8px;">&#128276;</div>
            <h1 style="margin:0;color:white;font-size:1.3rem;font-weight:800;">
              Nueva solicitud de servicio
            </h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.8);font-size:0.85rem;">TalentHub</p>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="color:#374151;font-size:0.95rem;line-height:1.7;margin:0 0 20px;">
              Hola <strong>{nombre_trabajador}</strong>, tienes una nueva solicitud esperando tu respuesta.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f8fafc;border-radius:12px;overflow:hidden;margin-bottom:24px;">
              <tr><td style="padding:14px 18px;border-bottom:1px solid #e2e8f0;">
                <span style="font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Cliente</span><br>
                <span style="font-size:0.95rem;font-weight:700;color:#111827;">{nombre_cliente}</span>
              </td></tr>
              <tr><td style="padding:14px 18px;border-bottom:1px solid #e2e8f0;">
                <span style="font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Servicio</span><br>
                <span style="font-size:0.95rem;font-weight:700;color:#4f46e5;">{categoria}</span>
              </td></tr>
              <tr><td style="padding:14px 18px;border-bottom:1px solid #e2e8f0;">
                <span style="font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Ciudad</span><br>
                <span style="font-size:0.95rem;color:#111827;">&#128205; {ciudad or 'No especificada'}</span>
              </td></tr>
              <tr><td style="padding:14px 18px;">
                <span style="font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Descripcion</span><br>
                <span style="font-size:0.88rem;color:#374151;line-height:1.5;">
                  {(descripcion or 'Sin descripcion')[:200]}{'...' if len(descripcion or '') > 200 else ''}
                </span>
              </td></tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center">
                <a href="{link}"
                   style="display:inline-block;background:#4f46e5;color:white;
                          text-decoration:none;padding:14px 32px;border-radius:12px;
                          font-weight:700;font-size:1rem;">
                  Ver solicitud en TalentHub
                </a>
              </td></tr>
            </table>
            <p style="color:#9ca3af;font-size:0.75rem;text-align:center;margin:20px 0 0;">
              Responde pronto — los clientes prefieren trabajadores que contestan rapido.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _enviar_gmail(correo_trabajador, f"Nueva solicitud: {categoria} - TalentHub", html)


# ============================================
# EMAIL DE BIENVENIDA Y VERIFICACIÓN
# ============================================

def enviar_email_bienvenida(
    correo: str,
    nombre: str,
    tipo_usuario: str,
    id_usuario: int,
    base_url: str
) -> bool:
    """Envía email de bienvenida con link de verificación al registrarse."""

    # Crear token de verificación
    token      = secrets.token_urlsafe(32)
    expiracion = datetime.now() + timedelta(hours=48)

    try:
        conexion = conectar_bd()
        cursor   = conexion.cursor()
        cursor.execute("""
            INSERT INTO tokens_recuperacion
            (tipo_usuario, id_usuario, correo, token, fecha_expiracion)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_usuario, id_usuario, correo, token, expiracion))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"[BIENVENIDA] Error guardando token: {e}")
        return False

    ruta         = "cliente" if tipo_usuario == "cliente" else "trabajador"
    link         = f"{base_url}/{ruta}/verificar-email?token={token}"
    nombre_corto = nombre.split()[0] if nombre else nombre
    color_grad   = "#059669, #0891b2" if tipo_usuario == "cliente" else "#4f46e5, #7c3aed"
    emoji_tipo   = "&#128269;" if tipo_usuario == "cliente" else "&#128188;"
    features     = (
        "&#8226; Solicitar servicios profesionales a domicilio<br>"
        "&#8226; Ver trabajadores en el mapa<br>"
        "&#8226; Chatear directamente con profesionales"
        if tipo_usuario == "cliente" else
        "&#8226; Recibir solicitudes de clientes<br>"
        "&#8226; Gestionar tu disponibilidad<br>"
        "&#8226; Construir tu reputacion con resenas"
    )

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,{color_grad});
                     padding:32px 28px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:8px;">{emoji_tipo}</div>
            <h1 style="margin:0;color:white;font-size:1.4rem;font-weight:800;">
              Bienvenido a TalentHub
            </h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:0.88rem;">
              Tu cuenta ha sido creada exitosamente
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 28px;">
            <p style="color:#374151;font-size:0.95rem;line-height:1.7;margin:0 0 20px;">
              Hola <strong>{nombre_corto}</strong>, gracias por unirte a TalentHub.
              Para confirmar tu correo y activar todas las funciones, haz clic aqui:
            </p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center" style="padding:8px 0 28px;">
                <a href="{link}"
                   style="display:inline-block;background:linear-gradient(135deg,{color_grad});
                          color:white;text-decoration:none;padding:14px 36px;
                          border-radius:12px;font-weight:700;font-size:1rem;">
                  Verificar mi correo
                </a>
              </td></tr>
            </table>
            <div style="background:#f8fafc;border-radius:12px;padding:16px 18px;margin-bottom:20px;">
              <p style="margin:0;color:#374151;font-size:0.88rem;line-height:1.8;">
                <strong>&#191;Que puedes hacer en TalentHub?</strong><br>
                {features}
              </p>
            </div>
            <p style="color:#9ca3af;font-size:0.75rem;text-align:center;margin:0;line-height:1.5;">
              Este enlace expira en 48 horas.<br>
              Si no creaste esta cuenta, ignora este correo.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _enviar_gmail(correo, f"Bienvenido a TalentHub, {nombre_corto}! Verifica tu correo", html)


def verificar_email_token(token: str) -> Optional[Dict]:
    """
    Verifica el token de email, marca el correo como verificado y consume el token.
    Retorna dict con tipo_usuario e id_usuario si fue exitoso, None si falló.
    """
    conexion = conectar_bd()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM tokens_recuperacion
            WHERE token = %s AND usado = 0 AND fecha_expiracion > NOW()
            LIMIT 1
        """, (token,))
        datos = cursor.fetchone()
        if not datos:
            return None

        if datos['tipo_usuario'] == 'cliente':
            cursor.execute("""
                UPDATE correo_cliente SET verificado = 1
                WHERE id_cliente = %s AND correo = %s
            """, (datos['id_usuario'], datos['correo']))
        else:
            cursor.execute("""
                UPDATE correo_persona SET verificado = 1
                WHERE id_persona = %s AND correo = %s
            """, (datos['id_usuario'], datos['correo']))

        cursor.execute(
            "UPDATE tokens_recuperacion SET usado = 1 WHERE id_token = %s",
            (datos['id_token'],)
        )
        conexion.commit()
        return datos
    except Exception as e:
        print(f"[VERIFICAR EMAIL] Error: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()
