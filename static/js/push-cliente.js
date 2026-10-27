/**
 * push-cliente.js — Suscripción a notificaciones push para el CLIENTE.
 *
 * Registra el service worker, pide permiso de notificaciones y guarda la
 * suscripción en el servidor como tipo_usuario='cliente'. Así el cliente recibe
 * avisos de: cotización recibida, servicio iniciado, servicio finalizado, etc.
 *
 * Uso en una página del cliente (al final del body):
 *   <script src="/static/js/push-cliente.js"></script>
 *   <script>PushCliente.activar();</script>
 *
 * Toma el id del cliente de localStorage ('id_cliente') o de /cliente/mi-perfil.
 */
(function (global) {
    'use strict';

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const raw     = atob(base64);
        return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
    }

    async function obtenerIdCliente() {
        let id = parseInt(localStorage.getItem('id_cliente')) || null;
        if (id) return id;
        try {
            const r = await fetch('/cliente/mi-perfil', { credentials: 'include' });
            if (r.ok) {
                const d = await r.json();
                if (d && d.id_cliente) {
                    localStorage.setItem('id_cliente', d.id_cliente);
                    return d.id_cliente;
                }
            }
        } catch (e) { /* silencioso */ }
        return null;
    }

    async function suscribir() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
        try {
            // Asegurar que el service worker esté registrado
            try { await navigator.serviceWorker.register('/static/sw.js'); } catch (e) {}
            const reg = await navigator.serviceWorker.ready;

            const resKey = await fetch('/push/vapid-public');
            const { publicKey } = await resKey.json();

            let sub = await reg.pushManager.getSubscription();
            if (!sub) {
                const perm = await Notification.requestPermission();
                if (perm !== 'granted') return;
                sub = await reg.pushManager.subscribe({
                    userVisibleOnly:      true,
                    applicationServerKey: urlBase64ToUint8Array(publicKey),
                });
            }

            const id = await obtenerIdCliente();
            if (!id) return;

            const subJson = sub.toJSON();
            await fetch('/push/subscribe', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
                    tipo_usuario: 'cliente',
                    id_usuario:   parseInt(id),
                    endpoint:     subJson.endpoint,
                    keys:         subJson.keys,
                }),
            });
        } catch (e) { /* silencioso */ }
    }

    // Reintenta hasta tener id_cliente (el perfil puede tardar en cargar)
    function activar(intentos) {
        intentos = intentos || 0;
        const id = parseInt(localStorage.getItem('id_cliente')) || null;
        if (id || intentos >= 8) {
            suscribir();
        } else {
            setTimeout(() => activar(intentos + 1), 1000);
        }
    }

    global.PushCliente = { activar, suscribir };
})(window);
