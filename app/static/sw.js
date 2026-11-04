const CACHE_NAME = "gestor-tareas-v1";

// Instalación del Service Worker
self.addEventListener("install", (event) => {
    self.skipWaiting(); // Activa el nuevo SW inmediatamente
});

// Activación
self.addEventListener("activate", (event) => {
    event.waitUntil(clients.claim());
});

// Estrategia de red (Network First)
self.addEventListener("fetch", (event) => {
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});