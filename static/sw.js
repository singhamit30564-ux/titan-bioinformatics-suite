/*
 * Titan Bio — best-effort PWA service worker.
 *
 * HONEST SCOPE: Streamlit renders one dynamic page with a hashed JS/CSS
 * bundle, so a classic static "app shell" cache cannot cover the whole UI.
 * This worker caches what it safely can — the manifest, the app icons, and
 * whichever pages/assets the browser actually requests while online — so
 * that revisiting the app while briefly offline can still render something
 * (cached navigation, flashcards data, cached tool results already in the
 * page). Live features (AI chat, Photo Se Samjhao vision calls, NCBI/KEGG
 * APIs) always need a live network connection; this worker does not and
 * cannot fake those responses.
 *
 * GRACEFUL DEGRADATION: every handler is wrapped so that a cache failure
 * (private browsing, storage quota, disabled SW support) simply falls back
 * to the network instead of breaking navigation.
 */

const CACHE_NAME = "titan-bio-shell-v1";
const PRECACHE_URLS = [
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
        )
      )
      .catch(() => undefined)
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return; // never intercept POST (AI/API calls)

  event.respondWith(
    caches
      .match(request)
      .then((cached) => {
        const network = fetch(request)
          .then((response) => {
            if (response && response.ok && response.type === "basic") {
              const copy = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)).catch(() => undefined);
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
      .catch(() => fetch(request))
  );
});
