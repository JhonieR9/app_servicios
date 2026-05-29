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
    """Genera código de 6 dígitos para SMS"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

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
    expiracion = datetime.now() + timedelta(hours=24)
    
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


def enviar_email_recuperacion(correo: str, token: str, tipo_usuario: str, base_url: str) -> bool:
    """
    Envía el correo de recuperación usando SMTP.
    Configura SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD en variables de entorno.
    """
    import smtplib
    import os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        # Sin credenciales: imprimir en consola (útil en desarrollo)
        ruta = "trabajador" if tipo_usuario == "trabajador" else "cliente"
        link = f"{base_url}/{ruta}/recuperar/nueva-password?token={token}"
        print(f"\n{'='*60}")
        print(f"📧 EMAIL DE RECUPERACIÓN (modo consola)")
        print(f"   Para: {correo}")
        print(f"   Link: {link}")
        print(f"   Expira en: 1 hora")
        print(f"{'='*60}\n")
        return True

    ruta = "trabajador" if tipo_usuario == "trabajador" else "cliente"
    link = f"{base_url}/{ruta}/recuperar/nueva-password?token={token}"

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#0a0a0f;color:#f1f5f9;border-radius:16px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 28px;text-align:center;">
        <div style="font-size:2rem;margin-bottom:8px;">🔐</div>
        <h1 style="margin:0;font-size:1.3rem;font-weight:800;">Recuperar contraseña</h1>
        <p style="margin:6px 0 0;opacity:0.85;font-size:0.85rem;">TalentHub</p>
      </div>
      <div style="padding:28px;">
        <p style="color:#cbd5e1;font-size:0.9rem;line-height:1.6;margin-bottom:24px;">
          Recibimos una solicitud para restablecer la contraseña de tu cuenta.
          Haz clic en el botón para crear una nueva contraseña. El enlace expira en <strong>1 hora</strong>.
        </p>
        <a href="{link}" style="display:block;text-align:center;background:linear-gradient(135deg,#4f46e5,#7c3aed);
           color:white;text-decoration:none;padding:14px 24px;border-radius:12px;
           font-weight:700;font-size:0.95rem;margin-bottom:20px;">
          Restablecer contraseña
        </a>
        <p style="color:#475569;font-size:0.78rem;line-height:1.5;">
          Si no solicitaste esto, ignora este correo. Tu contraseña no cambiará.<br>
          O copia este enlace en tu navegador:<br>
          <span style="color:#a5b4fc;word-break:break-all;">{link}</span>
        </p>
      </div>
    </div>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Recuperar contraseña – TalentHub"
        msg['From']    = f"TalentHub <{smtp_user}>"
        msg['To']      = correo
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, correo, msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️ Error enviando email: {e}")
        return False
