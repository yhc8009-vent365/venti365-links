/* 벤티 365 예약 앱 — 서비스워커
   목적: ① 홈 화면 설치 요건 충족 ② 인터넷이 약하거나 끊겨도 화면이 뜨게 함
   원칙: 앱 껍데기(HTML·매니페스트·아이콘)만 캐시한다. 사용자가 입력한 예약 내용은 캐시하지 않는다. */
var CACHE = "venti365-app-v1";
var SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return c.addAll(SHELL).catch(function () { /* 일부 실패해도 설치는 진행 */ });
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // 외부(카카오·전화) 요청은 건드리지 않는다

  // 문서: 네트워크 우선, 실패하면 캐시 (최신 내용 반영 우선)
  if (req.mode === "navigate" || (req.headers.get("accept") || "").indexOf("text/html") > -1) {
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put("./index.html", copy); });
        return res;
      }).catch(function () {
        return caches.match("./index.html").then(function (hit) {
          return hit || caches.match("./");
        });
      })
    );
    return;
  }

  // 그 외 정적 자원: 캐시 우선
  e.respondWith(
    caches.match(req).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === "basic") {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
