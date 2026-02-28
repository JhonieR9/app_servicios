"""
Script para generar código QR del formulario de registro
"""

try:
    import qrcode
    from PIL import Image
except ImportError:
    print("=" * 60)
    print("INSTALANDO DEPENDENCIAS...")
    print("=" * 60)
    import subprocess
    subprocess.check_call(['pip', 'install', 'qrcode[pil]'])
    import qrcode
    from PIL import Image

# URL del formulario (ACTUALIZA ESTA URL CON TU URL DE NGROK)
URL_FORMULARIO = "https://alta-dynamoelectric-dania.ngrok-free.app/trabajador/registro"

print("=" * 60)
print("GENERANDO CÓDIGO QR")
print("=" * 60)
print(f"\nURL: {URL_FORMULARIO}\n")

# Crear código QR
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)

qr.add_data(URL_FORMULARIO)
qr.make(fit=True)

# Crear imagen
img = qr.make_image(fill_color="black", back_color="white")

# Guardar imagen
filename = "qr_formulario_registro.png"
img.save(filename)

print(f"✅ Código QR generado: {filename}")
print("\nPuedes:")
print("1. Imprimir el código QR")
print("2. Compartirlo en redes sociales")
print("3. Ponerlo en volantes")
print("\n" + "=" * 60)

# Intentar abrir la imagen
try:
    img.show()
except:
    print("\nAbre el archivo manualmente:", filename)
