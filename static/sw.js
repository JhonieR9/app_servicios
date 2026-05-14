// Service Worker - TalentHub PWA
const CACHE_NAME = 'talenthub-v1';

// Archivos a guardar en caché para funcionar offline
const CACHE_URLS = [
  '/',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
];

// Instalar Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('TalentHub: Cache instalado');
      return cache.addAll(CACHE_URLS).catch(err => {
        console.log('Cache parcial:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activar Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Interceptar peticiones - Network First (siempre intenta internet primero)
self.addEventListener('fetch', event => {
  // Solo manejar peticiones GET
  if (event.request.method !== 'GET') return;

  // No cachear peticiones de API
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/cliente/') || 
      url.pathname.startsWith('/trabajador/') ||
      url.pathname.includes('/api/')) {
    return; // Dejar pasar sin caché
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Guardar en caché si la respuesta es válida
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Si no hay internet, usar caché
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Página offline por defecto
          return new Response(
            `<!DOCTYPE html>
            <html lang="es">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Sin conexión - TalentHub</title>
              <style>
                body { font-family: sans-serif; text-align: center; padding: 50px 20px;
                       background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; min-height: 100vh; }
                h1 { font-size: 2rem; margin-bottom: 15px; }
                p { font-size: 1rem; opacity: 0.8; margin-bottom: 30px; }
                button { background: white; color: #1e3a8a; border: none; padding: 14px 28px;
                         border-radius: 12px; font-size: 1rem; font-weight: 700; cursor: pointer; }
              </style>
            </head>
            <body>
              <h1>📡 Sin conexión</h1>
              <p>Verifica tu conexión a internet e intenta de nuevo</p>
              <button onclick="location.reload()">🔄 Reintentar</button>
            </body>
            </html>`,
            { headers: { 'Content-Type': 'text/html' } }
          );
        });
      })
  );
});
