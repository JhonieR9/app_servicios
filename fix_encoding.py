"""Corrige la codificación del formulario"""
import codecs

# Leer el archivo
with codecs.open('templates/trabajadores/registro_trabajador.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazos
replacements = {
    'SECCIÃ"N': 'SECCIÓN',
    'INFORMACIÃ"N': 'INFORMACIÓN',
    'InformaciÃ³n': 'Información',
    'identificaciÃ³n': 'identificación',
    'Ã³': 'ó',
    'Ã­': 'í',
    'Ã¡': 'á',
    'Ã©': 'é',
    'Ãº': 'ú',
    'Ã±': 'ñ',
    'Ã"': 'Ó',
    'SÃ­': 'Sí',
    'MÃ¡ximo': 'Máximo',
    'DÃ­as': 'Días',
    'TÃ‰RMINOS': 'TÉRMINOS',
    'tÃ©rminos': 'términos',
    'TÃ©rminos': 'Términos',
    'ubicaciÃ³n': 'ubicación',
    'geogrÃ¡fica': 'geográfica',
    'validaciÃ³n': 'validación',
    'AnimaciÃ³n': 'Animación',
    'mÃ­nimo': 'mínimo',
    'PÃ©rez': 'Pérez',
    'GarcÃ­a': 'García',
    'nÃºmero': 'número',
    'dÃ­gitos': 'dígitos',
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Guardar
with codecs.open('templates/trabajadores/registro_trabajador.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo corregido!")
