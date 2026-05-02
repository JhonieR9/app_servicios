with open('templates/trabajadores/registro_trabajador.html', 'rb') as f:
    raw = f.read()
c = raw.decode('utf-8')

# Buscar el form y su cierre
import re
forms = list(re.finditer(r'<form ', c))
print(f'Forms encontrados: {len(forms)}')
for f in forms:
    print(f'  Form en pos {f.start()}: {repr(c[f.start():f.start()+80])}')

# Buscar cierre del form
form_closes = list(re.finditer(r'</form>', c))
print(f'</form> encontrados: {len(form_closes)}')
for fc in form_closes:
    print(f'  </form> en pos {fc.start()}: {repr(c[fc.start()-100:fc.start()+10])}')
