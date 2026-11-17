/*
 * TalentHub - buscador de servicios de la pantalla de inicio del cliente.
 * Filtra mientras se escribe (categorias y problemas frecuentes, con sinonimos y sin importar tildes)
 * y lleva al formulario de solicitud con la categoria y el problema ya elegidos.
 *
 * Requiere /static/js/catalogo-servicios.js. Uso:
 *   Buscador.init({ getIdCliente: () => idCliente });
 */
(function (global) {
    'use strict';

    var categorias = null;      // nombres oficiales (del servidor; si falla, la lista base)
    var cargando = null;
    var items = [];             // resultados que se estan mostrando
    var activo = -1;
    var tokens = [];
    var cfg = { getIdCliente: function () { return null; } };
    var el = {};

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // Resalta lo que el usuario escribio, ignorando tildes. Solo si el plegado no cambia la longitud.
    function destacar(texto, toks) {
        var plano = global.Catalogo.foldTexto(texto);
        if (!toks.length || plano.length !== texto.length) return esc(texto);
        var rangos = [];
        toks.forEach(function (tk) {
            if (!tk) return;
            var i = plano.indexOf(tk);
            // preferir inicio de palabra
            var j = plano.search(new RegExp('(^|[^a-z0-9])' + tk.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
            if (j !== -1) i = plano.charAt(j) === tk.charAt(0) ? j : j + 1;
            if (i !== -1) rangos.push([i, i + tk.length]);
        });
        if (!rangos.length) return esc(texto);
        rangos.sort(function (a, b) { return a[0] - b[0]; });
        var fusion = [rangos[0].slice()];
        for (var k = 1; k < rangos.length; k++) {
            var ult = fusion[fusion.length - 1];
            if (rangos[k][0] <= ult[1]) ult[1] = Math.max(ult[1], rangos[k][1]); else fusion.push(rangos[k].slice());
        }
        var out = '', pos = 0;
        fusion.forEach(function (r) {
            out += esc(texto.slice(pos, r[0])) + '<mark>' + esc(texto.slice(r[0], r[1])) + '</mark>';
            pos = r[1];
        });
        return out + esc(texto.slice(pos));
    }

    function cargarCategorias() {
        if (categorias) return Promise.resolve();
        if (cargando) return cargando;
        cargando = fetch('/cliente/categorias', { credentials: 'include' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var nombres = (d.categorias || []).map(function (c) { return c.nombre_categoria; }).filter(Boolean);
                categorias = nombres.length ? nombres : global.Catalogo.CATEGORIAS_BASE.slice();
            })
            .catch(function () { categorias = global.Catalogo.CATEGORIAS_BASE.slice(); });
        return cargando;
    }

    function abrir(si) {
        el.lista.hidden = !si;
        el.input.setAttribute('aria-expanded', si ? 'true' : 'false');
        if (!si) { activo = -1; el.input.removeAttribute('aria-activedescendant'); }
    }

    function filaHtml(it, i) {
        var icono = global.Catalogo.iconoCategoria(it.cat);
        var titulo = it.prob || it.cat;
        var sub = it.prob ? it.cat : it.resumen;
        return '<li id="qOpt' + i + '" role="option" class="q-op' + (i === activo ? ' on' : '') + '" aria-selected="' + (i === activo) + '" data-i="' + i + '">' +
            '<span class="q-ico" style="background:' + icono.bg + ';color:' + icono.color + '"><i class="bi ' + icono.icon + '"></i></span>' +
            '<span class="q-txt"><span class="q-t">' + destacar(titulo, tokens) + '</span>' +
            (sub ? '<span class="q-s">' + esc(sub) + '</span>' : '') + '</span>' +
            '<i class="bi bi-chevron-right q-go" aria-hidden="true"></i></li>';
    }

    function pintar(encabezado) {
        var html = '';
        if (encabezado) {
            // "Populares" va en mayúsculas pequeñas; el aviso de "no encontramos" conserva lo que escribió el usuario
            var estilo = items.length === 1 && items[0].todas ? ' style="text-transform:none;letter-spacing:0;font-size:0.82rem"' : '';
            html += '<li class="q-head" role="presentation"' + estilo + '>' + encabezado + '</li>';
        }
        items.forEach(function (it, i) {
            if (it.todas) {
                html += '<li id="qOpt' + i + '" role="option" class="q-op' + (i === activo ? ' on' : '') + '" aria-selected="' + (i === activo) + '" data-i="' + i + '">' +
                    '<span class="q-ico" style="background:#eef2ff;color:#4f46e5"><i class="bi bi-grid-fill"></i></span>' +
                    '<span class="q-txt"><span class="q-t">Ver todas las categorías</span></span>' +
                    '<i class="bi bi-chevron-right q-go" aria-hidden="true"></i></li>';
            } else {
                html += filaHtml(it, i);
            }
        });
        el.lista.innerHTML = html;
        abrir(true);
        if (activo >= 0) {
            el.input.setAttribute('aria-activedescendant', 'qOpt' + activo);
            var nodo = document.getElementById('qOpt' + activo);
            if (nodo && nodo.scrollIntoView) nodo.scrollIntoView({ block: 'nearest' });
        }
    }

    function actualizar() {
        var q = el.input.value;
        el.limpiar.hidden = !q;
        tokens = global.Catalogo.palabrasDe(q);
        activo = -1;

        if (!tokens.length) {
            // Sin texto: sugerencias populares
            items = global.Catalogo.POPULARES
                .filter(function (p) { return !categorias || categorias.indexOf(p[0]) !== -1; })
                .map(function (p) { return { cat: p[0], prob: p[1], resumen: '' }; });
            pintar('Populares');
            el.estado.textContent = '';
            return;
        }
        var res = global.Catalogo.buscar(q, categorias, 8);
        if (!res.length) {
            items = [{ todas: true }];
            pintar('No encontramos «' + esc(q.trim()) + '»');
            el.estado.textContent = 'Sin resultados para ' + q.trim();
            return;
        }
        items = res;
        pintar('');
        el.estado.textContent = res.length + (res.length === 1 ? ' resultado' : ' resultados');
    }

    function ir(it) {
        var id = cfg.getIdCliente();
        if (!it || it.todas) {
            window.location.href = '/cliente/solicitar_servicio' + (id ? '?id_cliente=' + encodeURIComponent(id) : '');
            return;
        }
        window.location.href = global.Catalogo.urlServicio(it.cat, it.prob, id);
    }

    function mover(delta) {
        if (!items.length) return;
        activo = (activo + delta + items.length) % items.length;
        pintar(el.lista.querySelector('.q-head') ? el.lista.querySelector('.q-head').innerHTML : '');
    }

    function init(opciones) {
        cfg = Object.assign(cfg, opciones || {});
        el.input = document.getElementById('qServicio');
        el.lista = document.getElementById('qLista');
        el.limpiar = document.getElementById('qLimpiar');
        el.estado = document.getElementById('qEstado');
        if (!el.input || !el.lista || !global.Catalogo) return;

        el.input.addEventListener('focus', function () { cargarCategorias().then(actualizar); });
        el.input.addEventListener('input', function () { cargarCategorias().then(actualizar); });
        el.input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') { e.preventDefault(); if (el.lista.hidden) { cargarCategorias().then(actualizar); } else { mover(1); } }
            else if (e.key === 'ArrowUp') { e.preventDefault(); mover(-1); }
            else if (e.key === 'Enter') {
                e.preventDefault();
                if (el.lista.hidden) { cargarCategorias().then(actualizar); return; }
                ir(activo >= 0 ? items[activo] : items[0]);
            }
            else if (e.key === 'Escape') {
                if (!el.lista.hidden) { abrir(false); } else { el.input.value = ''; el.limpiar.hidden = true; }
            }
        });
        el.limpiar.addEventListener('click', function () {
            el.input.value = ''; el.limpiar.hidden = true; el.input.focus(); cargarCategorias().then(actualizar);
        });
        el.lista.addEventListener('click', function (e) {
            var li = e.target.closest('.q-op');
            if (li) ir(items[parseInt(li.getAttribute('data-i'), 10)]);
        });
        el.lista.addEventListener('mousemove', function (e) {
            var li = e.target.closest('.q-op');
            if (!li) return;
            var i = parseInt(li.getAttribute('data-i'), 10);
            if (i !== activo) {
                var previo = el.lista.querySelector('.q-op.on');
                if (previo) { previo.classList.remove('on'); previo.setAttribute('aria-selected', 'false'); }
                li.classList.add('on'); li.setAttribute('aria-selected', 'true'); activo = i;
            }
        });
        document.addEventListener('click', function (e) {
            if (!e.target.closest('#buscador')) abrir(false);
        });
        // Las categorias se piden en cuanto carga la pagina, para que la primera busqueda sea instantanea
        cargarCategorias();
    }

    global.Buscador = { init: init };
})(window);
