#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""벤티365(blog.naver.com/venti365) 링크허브 데이터 수집 → 설정 JSON 생성.

소스: 네이버 블로그 공식 RSS (https://rss.blog.naver.com/<아이디>) — 서버렌더 XML, 50건 제공.
출력: data/venti365.json  (linkhub.py 가 읽어 HTML 로 렌더)
"""
import html
import hashlib
import json
import os
import re
import urllib.request

BLOG_ID = "venti365"
RSS = f"https://rss.blog.naver.com/{BLOG_ID}"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")
MAX_ITEMS = 30

# 고정 상단 링크 (실제 확인된 주소만)
PHONE = "010-8622-0611"
KAKAO = "https://pf.kakao.com/_xgMuaX/chat"
BLOG = f"https://blog.naver.com/{BLOG_ID}"

CAT_ORDER = ["공지·예약", "공항", "골프", "출장", "기차·KTX", "여행정보"]

# 썸네일은 반드시 자체 보관한다.
# 🚨 네이버 CDN(blogthumb.pstatic.net)은 외부 도메인에서의 핫링크를 차단한다 — github.io 에서
#    참조하면 이미지가 전부 깨진다(2026-09-20 실측: 로컬 file:// 에서는 Referer 가 없어 정상,
#    배포 후에는 전부 broken). 그래서 내려받아 저장소에 함께 올리고 상대경로로 참조한다.
_USED_IMAGES = set()


def local_image(url, prefix=""):
    """원격 이미지를 images/ 로 내려받고 상대경로를 돌려준다. 실패하면 원래 URL 유지."""
    if not url:
        return ""
    os.makedirs(IMG_DIR, exist_ok=True)
    fn = f"{prefix}{hashlib.sha1(url.encode()).hexdigest()[:16]}.jpg"
    path = os.path.join(IMG_DIR, fn)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
        except Exception as e:
            print(f"  ! 이미지 내려받기 실패: {str(e)[:60]} — 원격 URL 유지")
            return url
    _USED_IMAGES.add(fn)
    return f"images/{fn}"


def prune_images():
    """이번 실행에서 쓰이지 않은 내려받은 썸네일을 정리한다(저장소 비대화 방지)."""
    if not os.path.isdir(IMG_DIR):
        return 0
    n = 0
    for f in os.listdir(IMG_DIR):
        if f.endswith(".jpg") and f not in _USED_IMAGES:
            try:
                os.remove(os.path.join(IMG_DIR, f))
                n += 1
            except Exception:
                pass
    return n


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def clean(t):
    t = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", t or "", flags=re.S)  # CDATA 먼저 벗긴다
    t = html.unescape(t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def cat_of(title, raw_cat):
    """RSS 카테고리 + 제목 키워드로 표시용 카테고리 결정 (추측 최소화 — 명시 키워드만)."""
    t = title
    if raw_cat in ("공지", "예약안내") or "예약 안내" in t:
        return "공지·예약"
    if any(k in t for k in ("골프", "라운딩", "캐디", "티오프", "부킹")):
        return "골프"
    if any(k in t for k in ("출장", "컨벤션", "전시회", "킨텍스", "코엑스", "벡스코", "송도컨벤시아")):
        return "출장"
    if any(k in t for k in ("KTX", "SRT", "ITX", "기차", "무궁화", "역")):
        return "기차·KTX"
    if any(k in t for k in ("공항", "인천공항", "김포공항", "터미널", "비행기", "항공", "수하물", "탑승", "체크인")):
        return "공항"
    return "여행정보"


def main():
    xml = fetch(RSS)
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    ch = re.search(r"<channel>(.*?)<item>", xml, re.S).group(1)

    ch_title = clean(re.search(r"<title>(.*?)</title>", ch, re.S).group(1))
    ch_desc = clean(re.search(r"<description>(.*?)</description>", ch, re.S).group(1))
    ch_img = re.search(r"<image>\s*<url>(.*?)</url>", ch, re.S)
    avatar = local_image(clean(ch_img.group(1)), "avatar_") if ch_img else ""

    blocks = []
    for it in items[:MAX_ITEMS]:
        title = clean(re.search(r"<title>(.*?)</title>", it, re.S).group(1))
        link = clean(re.search(r"<link>(.*?)</link>", it, re.S).group(1)).split("?")[0]
        pm = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        pub = clean(pm.group(1)) if pm else ""
        cm = re.search(r"<category>(.*?)</category>", it, re.S)
        raw_cat = clean(cm.group(1)) if cm else ""
        dm = re.search(r"<description>(.*?)</description>", it, re.S)
        desc = clean(dm.group(1)) if dm else ""
        im = re.search(r'<img[^>]+src="([^"]+)"', it)
        img = html.unescape(im.group(1)) if im else ""
        # 날짜: 'Sun, 20 Sep 2026 20:55:22 +0900' → 2026-09-20
        m = re.search(r"(\d{1,2}) (\w{3}) (\d{4})", pub)
        date = ""
        if m:
            mon = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                   "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}[m.group(2)]
            date = f"{m.group(3)}-{mon:02d}-{int(m.group(1)):02d}"
        blocks.append({"cat": cat_of(title, raw_cat), "title": title,
                       "url": link, "image": local_image(img),
                       "desc": re.sub(r'^["\'\s]+|["\'\s]+$', "", desc)[:95], "date": date})

    # 최신 글이 가장 큰 번호를 갖도록 부여 (인포크링크 운영 방식과 동일)
    for i, b in enumerate(reversed(blocks), 1):
        b["no"] = f"{i:03d}"
    # 예약 안내 글은 맨 위 고정 + 공지 배지
    for b in blocks:
        if "예약 안내" in b["title"]:
            b["badge"] = "공지"
            blocks.remove(b)
            blocks.insert(0, b)
            break

    cats = [c for c in CAT_ORDER if any(b["cat"] == c for b in blocks)]
    pruned = prune_images()

    cfg = {
        "title": "벤티365",
        "handle": f"@{BLOG_ID} · 여행.공항·골프·출장",
        "bio": ch_desc or "공항·골프·출장 이동 정보와 예약 안내",
        "avatar": avatar,
        "theme": {"bg": "#eef4f2", "card": "#ffffff", "accent": "#0f7b6c",
                  "text": "#16211f", "muted": "#5d6b68", "radius": 18},
        "notice": {"text": "예약 문의 " + PHONE + " · 카카오톡 채널 '벤티365' · "
                           "아래 링크는 블로그 글과 상담 채널로 연결됩니다.",
                   "bg": "#0f2b26", "fg": "#dcf5ef"},
        "cta": [{"label": "카카오톡 채널 상담", "url": KAKAO, "primary": True},
                {"label": "전화 문의", "url": "tel:" + PHONE.replace("-", "")}],
        "blocks": blocks,
        "footer": f"벤티365 · blog.naver.com/{BLOG_ID}\n"
                  f"문의 {PHONE} · 카카오톡 채널 '벤티365'\n"
                  f"글 {len(blocks)}건 · 최신 갱신 기준 RSS 제공분",
        "search": True,
        "embed_images": False,
    }
    out = os.path.join(ROOT, "data", "venti365.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(cfg, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"수집 완료: 글 {len(blocks)}건 → {out}")
    print(f"썸네일 자체 보관: images/ {len(_USED_IMAGES)}장 (정리 {pruned}장)")
    from collections import Counter
    print("카테고리 분포:", dict(Counter(b["cat"] for b in blocks)))
    print("상단 3건:")
    for b in blocks[:3]:
        print(f"   {b['no']} [{b['cat']}] {b['title'][:44]} | 썸네일 {'O' if b['image'] else 'X'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
