with open('templates/trabajadores/registro_trabajador.html', 'rb') as f:
    raw = f.read()
c = raw.decode('utf-8')

# Buscar el botón de guardar
idx = c.find('Guardar Registro')
print(f'Guardar Registro en: {idx}')
if idx != -1:
    print(repr(c[idx-200:idx+100]))
