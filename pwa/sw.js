// Network-first for the app shell and lesson JSON, so edits show up immediately
// and the last good copy still loads offline. Audio is left to the browser:
// intercepting byte-range requests stalls <audio>, and the podcast feed covers
// offline listening. Only registered over https or localhost.
const CACHE = "maaya-v3";
self.addEventListener("install", (e) => e.waitUntil(self.skipWaiting()));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.endsWith(".mp3") || e.request.headers.has("range")) return;
  e.respondWith(fetch(e.request).then((res) => {
    if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
    return res;
  }).catch(() => caches.match(e.request)));
});
