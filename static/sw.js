// Service Worker - TalentHub PWA v3
const CACHE_NAME    = 'talenthub-v3';
const STATIC_CACHE  = 'talenthub-static-v3';

// Recursos estáticos que siempre queremos offline
const STATIC_ASSETS = [
  '/static/css/talenthub.css',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
  'https://fonts.googleapis.com/css2?family=Lato:wght@300;400;600;700&display=swap',
  'https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css',
];

// Rutas de PÁGINAS que cacheamos para acceso offline
const PAGE_ASSETS = [
  '/',
];

// ── INSTALL ────────────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache =>
        cache.addAll(STATIC_ASSETS).catch(() => {})
      ),
      caches.open(CACHE_NAME).then(cache =>
        cache.addAll(PAGE_ASSETS).catch(() => {})
      ),
    ]).then(() => self.skipWaiting())
  );
});

// ── ACTIVATE ───────────────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME && k !== STATIC_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── FETCH ──────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // ── 1. APIs y rutas dinámicas → Network Only (sin caché) ──
  const isDynamic = (
    url.pathname.startsWith('/cliente/') ||
    url.pathname.startsWith('/trabajador/') ||
    url.pathname.startsWith('/chat/') ||
    url.pathname.includes('/api/') ||
    url.searchParams.toString().length > 0
  );
  if (isDynamic) return; // dejar pasar sin interferir

  // ── 2. Archivos estáticos → Cache First ──
  const isStatic = (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('api.mapbox.com')
  );
  if (isStatic) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(resp => {
          if (resp && resp.status === 200) {
            const clone = resp.clone();
            caches.open(STATIC_CACHE).then(c => c.put(event.request, clone));
          }
          return resp;
        }).catch(() => caches.match(event.request));
      })
    );
    return;
  }

  // ── 3. Páginas HTML → Network First con fallback a caché ──
  event.respondWith(
    fetch(event.request)
      .then(resp => {
        if (resp && resp.status === 200) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return resp;
      })
      .catch(() => {
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Fallback offline bonito
          return new Response(
            `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sin conexión - TalentHub</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:#0a0a0f;min-height:100vh;
         display:flex;align-items:center;justify-content:center;padding:20px;color:white}
    .card{background:#111118;border:1px solid rgba(255,255,255,0.08);border-radius:24px;
          padding:48px 32px;max-width:400px;width:100%;text-align:center;
          box-shadow:0 32px 64px rgba(0,0,0,0.5)}
    .icon{font-size:3.5rem;margin-bottom:16px;display:block}
    h1{font-size:1.4rem;font-weight:800;margin-bottom:10px}
    p{color:#64748b;font-size:0.9rem;line-height:1.6;margin-bottom:28px}
    button{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:white;border:none;
           padding:14px 28px;border-radius:12px;font-size:0.95rem;font-weight:700;
           cursor:pointer;width:100%;font-family:'Segoe UI',sans-serif}
    button:hover{opacity:0.9}
  </style>
</head>
<body>
  <div class="card">
    <span class="icon">📡</span>
    <h1>Sin conexión</h1>
    <p>Verifica tu conexión a internet e intenta de nuevo.<br>
       TalentHub necesita conexión para mostrarte los profesionales.</p>
    <button onclick="location.reload()">🔄 Reintentar</button>
  </div>
</body>
</html>`,
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        });
      })
  );
});
