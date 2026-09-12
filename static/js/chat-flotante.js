/**
 * chat-flotante.js — Burbuja de chat flotante tipo Messenger para TalentHub
 *
 * Uso:
 *   <script src="/static/js/chat-flotante.js"></script>
 *   <script>
 *     ChatFlotante.init({
 *       idSolicitud: 42,
 *       tipoUsuario: 'cliente',   // 'cliente' | 'trabajador'
 *       idUsuario:   3,
 *       tituloChat:  'Plomería - Goteras'
 *     });
 *   </script>
 */

(function (global) {
    'use strict';

    // ── FILTRO DE SEGURIDAD ──────────────────────────────────────────
    // Patrones que detectan intentos de sacar la conversación de la app
    const PATRONES_PELIGRO = [
        /\b(\+?57)?[\s\-.]?3\d{2}[\s\-.]?\d{3}[\s\-.]?\d{4}\b/,  // teléfonos colombianos
        /\b\d{7,12}\b/,                                              // números largos genéricos
        /whatsapp|wapp|wsp|wpp|wa\.me/i,
        /instagram|insta|ig\b/i,
        /telegram|tele\b/i,
        /facebook|fb\.com|fb\.me/i,
        /tiktok/i,
        /https?:\/\//i,                                              // links externos
        /www\./i,
        /\.com|\.net|\.co\b/i,
        /correo|email|gmail|hotmail|outlook/i,
        /contacta(me|nos)|llama(me)?|escrib[eé]me fuera/i,
    ];

    function esTextoSospechoso(texto) {
        return PATRONES_PELIGRO.some(p => p.test(texto));
    }

    async function reportarAlAdmin(idSolicitud, tipoUsuario, idUsuario, mensaje) {
        try {
            const fd = new FormData();
            fd.append('id_solicitud',  idSolicitud);
            fd.append('tipo_usuario',  tipoUsuario);
            fd.append('id_usuario',    idUsuario);
            fd.append('mensaje_bloqueado', mensaje);
            await fetch('/chat/bloqueo-seguridad', { method: 'POST', body: fd });
        } catch (e) { /* silencioso */ }
    }

    // ── ESTILOS ──────────────────────────────────────────────────────
    const CSS = `
    #cf-burbuja {
        position: fixed;
        bottom: 76px;          /* encima del bottom nav */
        right: 18px;
        z-index: 1000;
        width: 52px; height: 52px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        box-shadow: 0 4px 20px rgba(79,70,229,.45);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer;
        font-size: 1.3rem;
        transition: transform .2s;
        border: none;
        color: white;
    }
    #cf-burbuja:hover { transform: scale(1.08); }
    #cf-badge {
        position: absolute; top: -3px; right: -3px;
        background: #ef4444; color: white;
        font-size: 0.65rem; font-weight: 800;
        min-width: 18px; height: 18px;
        border-radius: 99px; padding: 0 4px;
        display: flex; align-items: center; justify-content: center;
        border: 2px solid white;
        display: none;
    }
    #cf-ventana {
        position: fixed;
        bottom: 136px;
        right: 18px;
        z-index: 1001;
        width: 320px;
        height: 430px;
        background: white;
        border-radius: 18px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.18);
        display: flex; flex-direction: column;
        overflow: hidden;
        transform: scale(0.85) translateY(20px);
        opacity: 0;
        pointer-events: none;
        transition: transform .25s cubic-bezier(.4,0,.2,1), opacity .25s;
    }
    #cf-ventana.open {
        transform: scale(1) translateY(0);
        opacity: 1;
        pointer-events: all;
    }
    #cf-header {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        padding: 12px 14px;
        display: flex; align-items: center; gap: 10px;
        flex-shrink: 0;
    }
    #cf-header-avatar {
        width: 34px; height: 34px; border-radius: 50%;
        background: rgba(255,255,255,0.25);
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; font-weight: 800; color: white; flex-shrink: 0;
        overflow: hidden;
    }
    #cf-header-avatar img { width:100%;height:100%;border-radius:50%;object-fit:cover; }
    #cf-header-info { flex: 1; min-width: 0; }
    #cf-titulo {
        font-size: 0.82rem; font-weight: 800; color: white;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    #cf-subtitulo { font-size: 0.68rem; color: rgba(255,255,255,0.75); margin-top:1px; }
    .cf-ctrl-btn {
        background: rgba(255,255,255,0.2); border: none;
        color: white; width: 28px; height: 28px;
        border-radius: 50%; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; transition: background .15s; flex-shrink: 0;
    }
    .cf-ctrl-btn:hover { background: rgba(255,255,255,0.35); }
    #cf-mensajes {
        flex: 1; overflow-y: auto; padding: 12px;
        display: flex; flex-direction: column; gap: 6px;
        background: #f8fafc;
    }
    #cf-mensajes::-webkit-scrollbar { width: 4px; }
    #cf-mensajes::-webkit-scrollbar-track { background: transparent; }
    #cf-mensajes::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 99px; }
    .cf-msg {
        max-width: 80%; padding: 8px 11px;
        border-radius: 14px; font-size: 0.8rem; line-height: 1.4;
        word-break: break-word;
    }
    .cf-msg.mine {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white; align-self: flex-end;
        border-bottom-right-radius: 4px;
    }
    .cf-msg.theirs {
        background: white; color: #1e293b;
        border: 1px solid #e2e8f0;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    .cf-msg.sistema {
        background: #fef3c7; color: #92400e;
        font-size: 0.72rem; align-self: center;
        text-align: center; border-radius: 99px;
        padding: 4px 12px;
    }
    .cf-msg-hora {
        font-size: 0.62rem; color: rgba(255,255,255,0.65);
        text-align: right; margin-top: 2px;
    }
    .cf-msg.theirs .cf-msg-hora { color: #94a3b8; }
    #cf-input-area {
        padding: 10px 12px;
        border-top: 1px solid #f1f5f9;
        display: flex; gap: 8px; align-items: flex-end;
        background: white; flex-shrink: 0;
    }
    #cf-input {
        flex: 1; border: 1.5px solid #e2e8f0; border-radius: 20px;
        padding: 8px 14px; font-size: 0.82rem;
        font-family: inherit; outline: none; resize: none;
        max-height: 80px; overflow-y: auto;
        transition: border-color .15s;
        line-height: 1.4;
    }
    #cf-input:focus { border-color: #6366f1; }
    #cf-send {
        width: 34px; height: 34px; border-radius: 50%;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        border: none; cursor: pointer; color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.9rem; flex-shrink: 0;
        transition: transform .15s;
    }
    #cf-send:hover { transform: scale(1.1); }
    #cf-send:disabled { opacity: .5; cursor: default; transform: none; }
    #cf-aviso-seguridad {
        display: none;
        margin: 0 12px 8px;
        background: #fef2f2; border: 1px solid #fecaca;
        border-radius: 10px; padding: 8px 12px;
        font-size: 0.75rem; color: #dc2626; font-weight: 600;
    }
    #cf-ver-completo {
        text-align: center; padding: 6px;
        font-size: 0.72rem; color: #6366f1;
        cursor: pointer; text-decoration: none; display: block;
        border-top: 1px solid #f1f5f9;
        background: white; flex-shrink: 0;
    }
    #cf-ver-completo:hover { background: #f5f3ff; }
    .cf-empty {
        text-align: center; color: #94a3b8;
        font-size: 0.8rem; padding: 20px;
        margin: auto;
    }
    `;

    // ── ESTADO ───────────────────────────────────────────────────────
    let cfg = {};
    let abierto = false;
    let ultimoId = 0;
    let pollingInterval = null;

    // ── INICIALIZAR ──────────────────────────────────────────────────
    function init(opciones) {
        cfg = Object.assign({
            idSolicitud: 0,
            tipoUsuario: 'cliente',
            idUsuario:   0,
            tituloChat:  'Chat',
            idContraparte: 0,
            avatarUrl:   '',
        }, opciones);

        // Inyectar estilos
        const style = document.createElement('style');
        style.textContent = CSS;
        document.head.appendChild(style);

        // Burbuja
        const burbuja = document.createElement('button');
        burbuja.id = 'cf-burbuja';
        burbuja.innerHTML = `
            <span id="cf-badge"></span>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>`;
        burbuja.onclick = toggleVentana;
        document.body.appendChild(burbuja);

        // Ventana flotante
        const ventana = document.createElement('div');
        ventana.id = 'cf-ventana';
        ventana.innerHTML = `
            <div id="cf-header">
                <div id="cf-header-avatar">💬</div>
                <div id="cf-header-info">
                    <div id="cf-titulo">${cfg.tituloChat}</div>
                    <div id="cf-subtitulo">● En línea</div>
                </div>
                <a href="/chat/?id_solicitud=${cfg.idSolicitud}&tipo=${cfg.tipoUsuario}&id_usuario=${cfg.idUsuario}"
                   target="_blank" class="cf-ctrl-btn" title="Abrir completo" style="text-decoration:none;font-size:0.75rem">↗</a>
                <button class="cf-ctrl-btn" onclick="ChatFlotante._minimizar()" title="Minimizar">—</button>
            </div>
            <div id="cf-mensajes"><div class="cf-empty">Cargando...</div></div>
            <div id="cf-aviso-seguridad">
                🚫 No puedes compartir datos de contacto dentro de la app. El mensaje fue bloqueado.
            </div>
            <div id="cf-input-area">
                <textarea id="cf-input" rows="1" placeholder="Escribe un mensaje..."
                    oninput="ChatFlotante._autoResize(this)"
                    onkeydown="ChatFlotante._tecla(event)"></textarea>
                <button id="cf-send" onclick="ChatFlotante._enviar()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
            <a id="cf-ver-completo"
               href="/chat/?id_solicitud=${cfg.idSolicitud}&tipo=${cfg.tipoUsuario}&id_usuario=${cfg.idUsuario}">
               📱 Ver chat completo →
            </a>`;
        document.body.appendChild(ventana);

        // Cargar avatar
        if (cfg.avatarUrl) {
            const img = document.createElement('img');
            img.src = cfg.avatarUrl;
            img.onload = () => { document.getElementById('cf-header-avatar').innerHTML = ''; document.getElementById('cf-header-avatar').appendChild(img); };
        }

        // Polling de badge (sin abrir el chat)
        actualizarBadge();
        setInterval(actualizarBadge, 10000);
    }

    function toggleVentana() {
        abierto = !abierto;
        const v = document.getElementById('cf-ventana');
        v.classList.toggle('open', abierto);
        if (abierto) {
            cargarMensajes();
            marcarLeidos();
            ocultarBadge();
            if (!pollingInterval) {
                pollingInterval = setInterval(() => {
                    if (abierto) { cargarMensajes(true); marcarLeidos(); }
                }, 2000);
            }
        }
    }

    function _minimizar() {
        abierto = false;
        document.getElementById('cf-ventana').classList.remove('open');
    }

    // ── MENSAJES ─────────────────────────────────────────────────────
    async function cargarMensajes(silencioso = false) {
        if (!cfg.idSolicitud) return;
        try {
            const res  = await fetch(`/chat/mensajes?id_solicitud=${cfg.idSolicitud}&desde_id=0`);
            const data = await res.json();
            const msgs = data.mensajes || [];

            if (!msgs.length) {
                if (!silencioso) document.getElementById('cf-mensajes').innerHTML = '<div class="cf-empty">Aún no hay mensajes</div>';
                return;
            }

            const nuevoUltimoId = msgs[msgs.length - 1].id_mensaje;
            if (nuevoUltimoId === ultimoId && silencioso) return;
            ultimoId = nuevoUltimoId;

            const wrap = document.getElementById('cf-mensajes');
            const atBottom = wrap.scrollHeight - wrap.scrollTop - wrap.clientHeight < 60;

            wrap.innerHTML = msgs.map(m => {
                const esMio = m.tipo_remitente === cfg.tipoUsuario && m.id_remitente === cfg.idUsuario;
                const hora  = m.fecha_envio ? String(m.fecha_envio).split(' ')[1]?.slice(0,5) || '' : '';
                if (m.tipo_remitente === 'sistema') {
                    return `<div class="cf-msg sistema">🔔 ${escHtml(m.mensaje)}</div>`;
                }
                return `<div class="cf-msg ${esMio ? 'mine' : 'theirs'}">
                    ${escHtml(m.mensaje)}
                    <div class="cf-msg-hora">${hora}</div>
                </div>`;
            }).join('');

            if (atBottom || !silencioso) wrap.scrollTop = wrap.scrollHeight;
        } catch(e) {}
    }

    async function _enviar() {
        const input = document.getElementById('cf-input');
        const texto = input.value.trim();
        if (!texto) return;

        // ── FILTRO DE SEGURIDAD ──
        if (esTextoSospechoso(texto)) {
            const aviso = document.getElementById('cf-aviso-seguridad');
            aviso.style.display = 'block';
            setTimeout(() => { aviso.style.display = 'none'; }, 5000);
            reportarAlAdmin(cfg.idSolicitud, cfg.tipoUsuario, cfg.idUsuario, texto);
            input.value = '';
            input.style.height = 'auto';
            return;
        }

        const btn = document.getElementById('cf-send');
        btn.disabled = true;
        input.value = '';
        input.style.height = 'auto';

        try {
            const fd = new FormData();
            fd.append('id_solicitud',   cfg.idSolicitud);
            fd.append('tipo_remitente', cfg.tipoUsuario);
            fd.append('id_remitente',   cfg.idUsuario);
            fd.append('mensaje',        texto);
            await fetch('/chat/enviar', { method: 'POST', body: fd });
            await cargarMensajes();
        } catch(e) {}
        btn.disabled = false;
    }

    function _tecla(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            _enviar();
        }
    }

    function _autoResize(el) {
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 80) + 'px';
    }

    // ── BADGE ────────────────────────────────────────────────────────
    async function actualizarBadge() {
        if (!cfg.idSolicitud || abierto) return;
        try {
            const res  = await fetch(`/chat/no-leidos?id_solicitud=${cfg.idSolicitud}&tipo_receptor=${cfg.tipoUsuario}`);
            const data = await res.json();
            const n = data.no_leidos || 0;
            const badge = document.getElementById('cf-badge');
            if (n > 0) {
                badge.textContent = n > 9 ? '9+' : n;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        } catch(e) {}
    }

    function ocultarBadge() {
        const b = document.getElementById('cf-badge');
        if (b) b.style.display = 'none';
    }

    async function marcarLeidos() {
        if (!cfg.idSolicitud) return;
        try {
            const fd = new FormData();
            fd.append('id_solicitud',  cfg.idSolicitud);
            fd.append('tipo_receptor', cfg.tipoUsuario);
            await fetch('/chat/leer', { method: 'POST', body: fd });
        } catch(e) {}
    }

    // ── UTILIDADES ───────────────────────────────────────────────────
    function escHtml(s) {
        return String(s)
            .replace(/&/g,'&amp;')
            .replace(/</g,'&lt;')
            .replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;');
    }

    // ── API PÚBLICA ──────────────────────────────────────────────────
    global.ChatFlotante = { init, _minimizar, _enviar, _tecla, _autoResize };

})(window);
