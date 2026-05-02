// Service Worker para TalentHub PWA
const CACHE_NAME = 'talenthub-v1';

// Archivos a cachear para uso offline básico
const CACHE_URLS = [
  '/',
  '/static/manifest.json',
];

// Instalar service worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(CACHE_URLS);
    })
  );
  self.skipWaiting();
});

// Activar y limpiar caches viejos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Estrategia: Network first, cache como fallback
self.addEventListener('fetch', (event) => {
  // Solo cachear GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Guardar en cache si es exitoso
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Si no hay internet, usar cache
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Página offline básica
          return new Response(
            '<html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0f172a;color:white"><h2>Sin conexión</h2><p>Necesitas internet para usar TalentHub</p></body></html>',
            { headers: { 'Content-Type': 'text/html' } }
          );
        });
      })
  );
});
