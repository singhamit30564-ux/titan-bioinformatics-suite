/**
 * Minimal service worker (PWA shell caching). API traffic is never cached:
 * sequence payloads must stay ephemeral (Zero Data Retention).
 */
const SHELL = "titan-shell-v1";
const SHELL_ASSETS = ["/", "/manifest.webmanifest", "/titan-mark.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((cache) => cache.addAll(SHELL_ASSETS)));
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api")) {
    return; // never cache API responses
  }
  event.respondWith(
    caches.match(event.request).then(
      (cached) =>
        cached ||
        fetch(event.request).then((response) => {
          if (response.ok && event.request.method === "GET") {
            const clone = response.clone();
            caches.open(SHELL).then((cache) => cache.put(event.request, clone));
          }
          return response;
        }),
    ),
  );
});
