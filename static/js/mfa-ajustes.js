/*
 * TalentHub - ajustes de verificación en dos pasos.
 * Se monta en un contenedor: <div id="mfaAjustes" data-rol="admin|psicologa|trabajador|cliente"></div>
 */
(function () {
    'use strict';

    var cont = document.getElementById('mfaAjustes');
    if (!cont) return;
    var ROL = cont.getAttribute('data-rol');

    function h(tag, attrs, texto) {
        var e = document.createElement(tag);
        if (attrs) Object.keys(attrs).forEach(function (k) {
            if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]);
        });
        if (texto !== undefined && texto !== null) e.textContent = texto;
        return e;
    }

    function limpiar() { while (cont.firstChild) cont.removeChild(cont.firstChild); }

    async function api(url, datos) {
        var opts = { credentials: 'same-origin' };
        if (datos) {
            var fd = new FormData();
            Object.keys(datos).forEach(function (k) { fd.append(k, datos[k]); });
            opts.method = 'POST';
            opts.body = fd;
        }
        var res = await fetch(url, opts);
        var data = {};
        try { data = await res.json(); } catch (e) { /* sin cuerpo */ }
        return { ok: res.ok, status: res.status, data: data };
    }

    function campo(id, etiqueta, tipo, extra) {
        var g = h('div', { class: 'campo' });
        var l = h('label', { for: id }, etiqueta);
        var i = h('input', { id: id, type: tipo || 'text', autocomplete: 'off' });
        if (extra) Object.keys(extra).forEach(function (k) { i.setAttribute(k, extra[k]); });
        g.appendChild(l); g.appendChild(i);
        return g;
    }

    function mensaje(texto, tipo) {
        var m = cont.querySelector('.msg');
        if (!m) { m = h('div', { class: 'msg', role: 'alert' }); cont.insertBefore(m, cont.firstChild); }
        m.className = 'msg ' + (tipo || 'error');
        m.textContent = texto;
    }

    function boton(texto, clase, fn) {
        var b = h('button', { type: 'button', class: 'btn ' + (clase || '') }, texto);
        b.addEventListener('click', async function () {
            b.disabled = true;
            try { await fn(); } finally { b.disabled = false; }
        });
        return b;
    }

    // ---------- Pantallas ----------

    async function cargar() {
        limpiar();
        var r = await api('/mfa/estado?rol=' + encodeURIComponent(ROL));
        if (!r.ok) { cont.appendChild(h('p', { class: 'msg error' }, r.data.error || 'No se pudo cargar.')); return; }
        if (r.data.activo) pantallaActivo(r.data); else pantallaInactivo(r.data);
    }

    function pantallaInactivo(est) {
        cont.appendChild(h('div', { class: 'estado off' }, 'Verificación en dos pasos: desactivada'));
        cont.appendChild(h('p', null,
            'Agrega una capa extra: además de tu contraseña, se pedirá un código de 6 dígitos de una app ' +
            'autenticadora (Google Authenticator, Microsoft Authenticator, Authy, 1Password).'));
        if (!est.disponible) {
            cont.appendChild(h('p', { class: 'msg error' },
                'Aún no está habilitada en el servidor. Avisa al administrador.'));
            return;
        }
        cont.appendChild(campo('mfaPass', 'Tu contraseña para continuar', 'password', { autocomplete: 'current-password' }));
        cont.appendChild(boton('Activar', 'primario', async function () {
            var pass = document.getElementById('mfaPass').value;
            var r = await api('/mfa/iniciar', { rol: ROL, password: pass });
            if (!r.ok) { mensaje(r.data.error || 'No se pudo iniciar', 'error'); return; }
            pantallaEscanear(r.data);
        }));
    }

    function pantallaEscanear(d) {
        limpiar();
        cont.appendChild(h('div', { class: 'estado pend' }, 'Paso 1: escanea el código QR'));
        cont.appendChild(h('p', null, 'Abre tu app autenticadora, elige "agregar cuenta" y escanea este código.'));
        var qr = h('div', { class: 'qr' });
        if (d.qr_svg) {
            qr.innerHTML = d.qr_svg;   // SVG generado por nuestro servidor
            var svg = qr.querySelector('svg');
            if (svg) { svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Código QR para tu app autenticadora'); }
        }
        cont.appendChild(qr);
        cont.appendChild(h('p', { class: 'peq' }, 'Si no puedes escanear, escribe esta clave a mano (tipo "basada en tiempo"):'));
        cont.appendChild(h('code', { class: 'clave' }, d.secreto.replace(/(.{4})/g, '$1 ').trim()));
        var enlace = h('a', { href: d.uri, class: 'peq' }, 'Abrir directamente en la app de este celular');
        cont.appendChild(h('div', null)).appendChild(enlace);
        cont.appendChild(h('div', { class: 'estado pend' }, 'Paso 2: escribe el código que muestra la app'));
        cont.appendChild(campo('mfaCod', 'Código de 6 dígitos', 'text', { inputmode: 'numeric', maxlength: '8', autocomplete: 'one-time-code' }));
        cont.appendChild(boton('Confirmar y activar', 'primario', async function () {
            var r = await api('/mfa/activar', { rol: ROL, codigo: document.getElementById('mfaCod').value });
            if (!r.ok) { mensaje(r.data.error || 'Código incorrecto', 'error'); return; }
            pantallaCodigos(r.data.codigos, true);
        }));
        cont.appendChild(boton('Cancelar', '', cargar));
    }

    function pantallaCodigos(codigos, recienActivado) {
        limpiar();
        cont.appendChild(h('div', { class: 'estado on' },
            recienActivado ? 'Verificación en dos pasos activada' : 'Nuevos códigos de recuperación'));
        cont.appendChild(h('p', null,
            'Guarda estos códigos en un lugar seguro. Cada uno sirve una sola vez si pierdes tu celular. ' +
            'No volverán a mostrarse.'));
        var lista = h('div', { class: 'codigos' });
        codigos.forEach(function (c) { lista.appendChild(h('code', null, c)); });
        cont.appendChild(lista);
        cont.appendChild(boton('Copiar', '', async function () {
            try { await navigator.clipboard.writeText(codigos.join('\n')); mensaje('Códigos copiados', 'ok'); }
            catch (e) { mensaje('No se pudo copiar. Anótalos manualmente.', 'error'); }
        }));
        cont.appendChild(boton('Descargar .txt', '', async function () {
            var blob = new Blob(['Códigos de recuperación TalentHub\n\n' + codigos.join('\n') + '\n'], { type: 'text/plain' });
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'talenthub-codigos-recuperacion.txt';
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
            setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        }));
        cont.appendChild(boton('Ya los guardé', 'primario', cargar));
    }

    function pantallaActivo(est) {
        cont.appendChild(h('div', { class: 'estado on' }, 'Verificación en dos pasos: activada'));
        cont.appendChild(h('p', null, 'Códigos de recuperación disponibles: ' + est.restantes +
            (est.restantes <= 2 ? ' (te quedan pocos, genera nuevos)' : '')));
        cont.appendChild(h('p', { class: 'peq' },
            'Para desactivarla o generar nuevos códigos confirma con tu contraseña y un código de tu app.'));
        cont.appendChild(campo('mfaPass', 'Tu contraseña', 'password', { autocomplete: 'current-password' }));
        cont.appendChild(campo('mfaCod', 'Código de tu app (o de recuperación)', 'text', { autocomplete: 'one-time-code' }));
        cont.appendChild(boton('Generar nuevos códigos de recuperación', '', async function () {
            var r = await api('/mfa/regenerar', {
                rol: ROL, password: document.getElementById('mfaPass').value, codigo: document.getElementById('mfaCod').value
            });
            if (!r.ok) { mensaje(r.data.error || 'No se pudo', 'error'); return; }
            pantallaCodigos(r.data.codigos, false);
        }));
        cont.appendChild(boton('Desactivar', 'peligro', async function () {
            if (!window.confirm('¿Seguro que quieres desactivar la verificación en dos pasos?')) return;
            var r = await api('/mfa/desactivar', {
                rol: ROL, password: document.getElementById('mfaPass').value, codigo: document.getElementById('mfaCod').value
            });
            if (!r.ok) { mensaje(r.data.error || 'No se pudo', 'error'); return; }
            await cargar();
            mensaje('Verificación en dos pasos desactivada', 'ok');
        }));
    }

    cargar();
})();
