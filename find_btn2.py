import re
with open('templates/trabajadores/registro_trabajador.html', 'rb') as f:
    raw = f.read()
c = raw.decode('utf-8')

# Buscar el bloque de botones HTML
m = re.search(r'<div class="d-flex justify-content-between', c)
if m:
    print(f'Botones en: {m.start()}')
    print(repr(c[m.start():m.start()+300]))
else:
    print("No encontrado d-flex")
    # Buscar btn-primary-custom en HTML
    for m2 in re.finditer(r'btn-primary-custom', c):
        ctx = c[m2.start()-50:m2.start()+100]
        if 'button' in ctx.lower():
            print(f'btn-primary-custom en {m2.start()}:')
            print(repr(ctx))
