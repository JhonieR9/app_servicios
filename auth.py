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
