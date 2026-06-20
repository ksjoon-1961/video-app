const CACHE = "v5";
const STATIC_URLS = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/vendor/supabase.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      // allSettled: 개별 실패가 전체 설치를 막지 않음
      Promise.allSettled(STATIC_URLS.map((url) => c.add(url)))
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const { pathname, hostname } = new URL(e.request.url);

  // Network-only: API 요청, 외부 호스트(Supabase signed URL, CDN)
  if (pathname.startsWith("/api/") || hostname !== self.location.hostname) {
    return;
  }

  // 정적 자원: 캐시 우선
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request))
  );
});
