/* SeoulVentiTaxi 예약 앱 — 서비스워커
   목적: ① 홈 화면 설치 요건 충족 ② 인터넷이 약하거나 끊겨도 화면이 뜨게 함
   원칙: 앱 껍데기(HTML·매니페스트·아이콘)만 캐시한다. 사용자가 입력한 예약 내용은 캐시하지 않는다.
   변경(v2): 관리자 페이지(admin.html) 추가 + 화면별로 캐시 키를 분리(예전엔 admin.html 로 오프라인
             진입하면 예약 앱 화면이 대신 떴다 — 경로별 키로 고쳤다). */
var CACHE = "venti365-app-v2-7926";
var SHELL = [
  "./",
  "./index.html",
  "./admin.html",
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
    var isAdmin = /admin\.html?$/i.test(url.pathname || "");
    var key = isAdmin ? "./admin.html" : "./index.html";
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(key, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(key).then(function (hit) {
          return hit || caches.match("./index.html") || caches.match("./");
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
