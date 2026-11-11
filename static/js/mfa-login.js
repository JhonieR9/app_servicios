/*
 * TalentHub - segundo paso (MFA) del inicio de sesión.
 *
 * Uso en las páginas de login, justo después de leer la respuesta:
 *   let ok = res.ok; let data = await res.json();
 *   if (data.mfa_requerido) { const r = await MFA.resolver(data); ok = r.ok; data = r.data; }
 *
 * Devuelve { ok, data } con la misma forma que la respuesta normal del login.
 */
(function () {
    'use strict';

    function el(tag, estilos, texto) {
        var e = document.createElement(tag);
        if (estilos) Object.keys(estilos).forEach(function (k) { e.style[k] = estilos[k]; });
        if (texto) e.textContent = texto;
        return e;
    }

    function resolver(datosLogin) {
        return new Promise(function (resolve) {
            var fondo = el('div', {
                position: 'fixed', left: '0', top: '0', right: '0', bottom: '0', zIndex: '99999',
                background: 'rgba(15,23,42,.65)', display: 'flex', alignItems: 'center',
                justifyContent: 'center', padding: '16px'
            });
            fondo.setAttribute('role', 'dialog');
            fondo.setAttribute('aria-modal', 'true');
            fondo.setAttribute('aria-labelledby', 'mfaTitulo');

            var caja = el('div', {
                background: '#fff', borderRadius: '16px', padding: '28px 24px', width: '100%',
                maxWidth: '380px', fontFamily: "'Segoe UI', Tahoma, sans-serif", color: '#1e293b',
                boxShadow: '0 20px 50px rgba(0,0,0,.3)', textAlign: 'center'
            });
            var titulo = el('h2', { fontSize: '1.25rem', margin: '0 0 8px' }, 'Verificación en dos pasos');
            titulo.id = 'mfaTitulo';
            var ayuda = el('p', { fontSize: '.92rem', color: '#475569', margin: '0 0 16px', lineHeight: '1.4' },
                'Escribe el código de 6 dígitos de tu app autenticadora, o un código de recuperación.');
            var input = el('input', {
                width: '100%', boxSizing: 'border-box', padding: '12px', fontSize: '1.3rem',
                textAlign: 'center', letterSpacing: '3px', border: '2px solid #e2e8f0', borderRadius: '10px'
            });
            input.type = 'text';
            input.autocomplete = 'one-time-code';
            input.setAttribute('inputmode', 'text');
            input.setAttribute('aria-label', 'Código de verificación');
            input.maxLength = 14;
            var error = el('div', { color: '#b91c1c', fontSize: '.9rem', minHeight: '1.2em', margin: '10px 0' });
            error.setAttribute('role', 'alert');
            var btnOk = el('button', {
                width: '100%', padding: '12px', border: 'none', borderRadius: '10px', cursor: 'pointer',
                background: '#4361ee', color: '#fff', fontSize: '1rem', fontWeight: '600'
            }, 'Verificar');
            btnOk.type = 'button';
            var btnNo = el('button', {
                width: '100%', padding: '10px', border: 'none', background: 'none', cursor: 'pointer',
                color: '#64748b', fontSize: '.9rem', marginTop: '6px'
            }, 'Cancelar');
            btnNo.type = 'button';

            caja.appendChild(titulo); caja.appendChild(ayuda); caja.appendChild(input);
            caja.appendChild(error); caja.appendChild(btnOk); caja.appendChild(btnNo);
            fondo.appendChild(caja);
            document.body.appendChild(fondo);
            input.focus();

            function cerrar(resultado) {
                if (fondo.parentNode) fondo.parentNode.removeChild(fondo);
                resolve(resultado);
            }

            async function enviar() {
                var codigo = input.value.trim();
                if (!codigo) { error.textContent = 'Escribe el código'; return; }
                btnOk.disabled = true; btnOk.textContent = 'Verificando...'; error.textContent = '';
                try {
                    var fd = new FormData();
                    fd.append('mfa_token', datosLogin.mfa_token);
                    fd.append('codigo', codigo);
                    var res = await fetch('/mfa/login', { method: 'POST', body: fd });
                    var data = await res.json();
                    if (res.ok && data.success !== false) {
                        cerrar({ ok: true, data: data });
                        return;
                    }
                    if (data.expirado) {
                        cerrar({ ok: false, data: { error: data.error } });
                        return;
                    }
                    error.textContent = data.error || 'Código incorrecto';
                } catch (e) {
                    error.textContent = 'Error de conexión';
                }
                btnOk.disabled = false; btnOk.textContent = 'Verificar';
                input.select();
            }

            btnOk.addEventListener('click', enviar);
            input.addEventListener('keydown', function (ev) {
                if (ev.key === 'Enter') { ev.preventDefault(); enviar(); }
                if (ev.key === 'Escape') { cerrar({ ok: false, data: { error: 'Verificación cancelada' } }); }
            });
            btnNo.addEventListener('click', function () {
                cerrar({ ok: false, data: { error: 'Verificación cancelada' } });
            });
        });
    }

    window.MFA = window.MFA || {};
    window.MFA.resolver = resolver;
})();
