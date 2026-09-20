#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인포크링크형 '링크허브' 페이지 생성기 — 단일 HTML 파일 출력.

구조 (인포크링크 실측 구조를 그대로 따름):
    ① 프로필 영역  → ② 고지 블록  → ③ CTA 버튼  → ④ 카테고리·검색  → ⑤ 링크 카드 목록  → ⑥ 푸터

입력: JSON 설정 파일 (아래 SCHEMA 참조)
출력: 자체 완결형(self-contained) HTML 1개 — 이미지 base64 임베드 옵션

SCHEMA:
{
  "title": "벤티365", "bio": "한 줄 소개", "handle": "@venti365",
  "avatar": "경로 또는 URL",
  "theme": {"bg": "#eef4f2", "card": "#ffffff", "accent": "#0f7b6c",
            "text": "#16211f", "muted": "#5d6b68", "radius": 18},
  "notice": {"text": "...", "bg": "#0f0f0f", "fg": "#e8f9fc"},
  "cta": [{"label": "카카오톡 상담", "url": "https://...", "primary": true}],
  "blocks": [{"no": "001", "cat": "공항", "title": "제목", "url": "https://...",
              "image": "경로 또는 URL", "desc": "짧은 설명", "badge": "공지", "date": "2026-09-20"}],
  "footer": "사업자 정보 / 안내 문구",
  "search": true, "embed_images": true
}
"""
import argparse
import base64
import html
import json
import mimetypes
import os
import re
import sys
from datetime import date

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:%(bg)s;--card:%(card)s;--accent:%(accent)s;--text:%(text)s;--muted:%(muted)s;--radius:%(radius)dpx}
html{-webkit-text-size-adjust:100%%}
body{background:var(--bg);color:var(--text);
 font-family:Pretendard,-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;
 line-height:1.5;padding:0 0 40px;-webkit-font-smoothing:antialiased}
.wrap{max-width:520px;margin:0 auto;padding:0 16px}
/* ① 프로필 */
.profile{padding:34px 0 20px;text-align:center}
.avatar{width:88px;height:88px;border-radius:50%%;object-fit:cover;background:#dde5e3;
 box-shadow:0 4px 14px rgba(0,0,0,.10);margin-bottom:12px}
.profile h1{font-size:19px;font-weight:800;letter-spacing:-.02em}
.profile .handle{font-size:12.5px;color:var(--muted);margin-top:3px}
.profile .bio{font-size:13.5px;color:var(--muted);margin-top:9px;white-space:pre-line;padding:0 6px}
/* ② 고지 */
.notice{border-radius:12px;padding:11px 14px;font-size:12px;line-height:1.55;margin:4px 0 14px}
/* ③ CTA */
.cta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.cta a{flex:1 1 0;min-width:132px;text-align:center;text-decoration:none;font-weight:700;font-size:14px;
 padding:13px 10px;border-radius:12px;background:var(--card);color:var(--text);
 border:1px solid rgba(0,0,0,.07);box-shadow:0 2px 8px rgba(0,0,0,.05);transition:.15s}
.cta a.primary{background:var(--accent);color:#fff;border-color:transparent}
.cta a:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.12)}
/* ④ 검색·카테고리 */
.tools{position:sticky;top:0;z-index:9;background:var(--bg);padding:8px 0 10px}
.search{width:100%%;padding:11px 14px;border-radius:12px;border:1px solid rgba(0,0,0,.10);
 background:var(--card);font-size:14px;color:var(--text);outline:none}
.search:focus{border-color:var(--accent)}
.chips{display:flex;gap:6px;overflow-x:auto;margin-top:9px;padding-bottom:2px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{white-space:nowrap;font-size:12.5px;font-weight:600;padding:7px 12px;border-radius:999px;
 background:var(--card);color:var(--muted);border:1px solid rgba(0,0,0,.07);cursor:pointer;transition:.15s}
.chip.on{background:var(--accent);color:#fff;border-color:transparent}
/* ⑤ 카드 */
.card{display:block;background:var(--card);border-radius:var(--radius);overflow:hidden;margin-bottom:12px;
 text-decoration:none;color:inherit;box-shadow:0 2px 10px rgba(0,0,0,.06);transition:.16s}
.card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(0,0,0,.13)}
.thumb{width:100%%;aspect-ratio:16/9;background:#e8eeec;display:block;object-fit:cover}
.body{padding:13px 15px 15px}
.body .cat{font-size:11px;font-weight:700;color:var(--accent);letter-spacing:.02em}
.body h2{font-size:15px;font-weight:700;letter-spacing:-.02em;margin-top:4px;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.body p{font-size:12.5px;color:var(--muted);margin-top:6px;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.body .meta{font-size:11.5px;color:var(--muted);margin-top:9px;display:flex;gap:8px;align-items:center}
.no{font-weight:800;color:var(--accent);font-variant-numeric:tabular-nums}
.badge{font-size:10.5px;font-weight:800;padding:3px 7px;border-radius:6px;background:var(--accent);color:#fff}
.badge.soft{background:rgba(0,0,0,.06);color:var(--muted)}
/* ⑥ 푸터 */
footer{text-align:center;font-size:11.5px;color:var(--muted);line-height:1.8;padding:22px 6px 0;white-space:pre-line}
.empty{text-align:center;color:var(--muted);font-size:13px;padding:26px 0}
@media (prefers-color-scheme:dark){
 :root{--bg:#0e1413;--card:#1b2220;--text:#eef3f1;--muted:#9dada9}
 .cta a,.search,.chip{border-color:rgba(255,255,255,.10)}
 .thumb{background:#232b29}
}
"""

JS = """
(function(){
  var q=document.getElementById('q'), chips=[].slice.call(document.querySelectorAll('.chip')),
      cards=[].slice.call(document.querySelectorAll('.card')), cat='전체', empty=document.getElementById('empty');
  function apply(){
    var t=(q.value||'').trim().toLowerCase(), n=0;
    cards.forEach(function(c){
      var okCat = (cat==='전체') || (c.dataset.cat===cat);
      var okTxt = !t || (c.dataset.key.indexOf(t)>-1);
      var show = okCat && okTxt; c.style.display = show?'':'none'; if(show) n++;
    });
    empty.style.display = n? 'none':'block';
  }
  q.addEventListener('input', apply);
  chips.forEach(function(ch){ ch.addEventListener('click', function(){
    chips.forEach(function(x){x.classList.remove('on')}); ch.classList.add('on');
    cat=ch.dataset.cat; apply();
  })});
})();
"""


def img_src(ref, embed, base_dir):
    """이미지 참조를 src 문자열로. embed=True면 base64 data URI로 인라인."""
    if not ref:
        return ""
    if re.match(r"^https?://", ref):
        return ref
    path = ref if os.path.isabs(ref) else os.path.join(base_dir, ref)
    if not embed:
        return ref
    if not os.path.exists(path):
        return ""
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def render(cfg, base_dir="."):
    th = {"bg": "#eef4f2", "card": "#ffffff", "accent": "#0f7b6c",
          "text": "#16211f", "muted": "#5d6b68", "radius": 18}
    th.update(cfg.get("theme") or {})
    embed = cfg.get("embed_images", True)
    e = html.escape

    cats, blocks = [], cfg.get("blocks") or []
    for b in blocks:
        c = (b.get("cat") or "").strip()
        if c and c not in cats:
            cats.append(c)

    parts = [f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(cfg.get('title','링크허브'))}</title>
<meta name="description" content="{e(cfg.get('bio','') or '')}">
<style>{CSS % th}</style></head>
<body><div class="wrap">
<div class="profile">"""]
    av = img_src(cfg.get("avatar"), embed, base_dir)
    if av:
        parts.append(f'<img class="avatar" src="{av}" alt="">')
    parts.append(f'<h1>{e(cfg.get("title",""))}</h1>')
    if cfg.get("handle"):
        parts.append(f'<div class="handle">{e(cfg["handle"])}</div>')
    if cfg.get("bio"):
        parts.append(f'<div class="bio">{e(cfg["bio"])}</div>')
    parts.append("</div>")

    nt = cfg.get("notice")
    if nt and nt.get("text"):
        parts.append(
            f'<div class="notice" style="background:{nt.get("bg","#0f0f0f")};'
            f'color:{nt.get("fg","#e8f9fc")}">{e(nt["text"])}</div>')

    if cfg.get("cta"):
        parts.append('<div class="cta">')
        for c in cfg["cta"]:
            cls = "primary" if c.get("primary") else ""
            parts.append(f'<a class="{cls}" href="{e(c["url"])}" target="_blank" '
                         f'rel="noopener">{e(c["label"])}</a>')
        parts.append("</div>")

    if cfg.get("search") and blocks:
        parts.append('<div class="tools">'
                     '<input class="search" id="q" type="search" placeholder="상품·글 검색" '
                     'autocomplete="off"><div class="chips">')
        for c in ["전체"] + cats:
            on = " on" if c == "전체" else ""
            parts.append(f'<div class="chip{on}" data-cat="{e(c)}">{e(c)}</div>')
        parts.append("</div></div>")

    parts.append('<div id="list">')
    for b in blocks:
        cat = (b.get("cat") or "").strip()
        key = " ".join([str(b.get("title", "")), str(b.get("desc", "")), cat]).lower()
        parts.append(f'<a class="card" href="{e(b["url"])}" target="_blank" rel="noopener" '
                     f'data-cat="{e(cat)}" data-key="{e(key)}">')
        src = img_src(b.get("image"), embed, base_dir)
        if src:
            parts.append(f'<img class="thumb" src="{src}" alt="" loading="lazy">')
        parts.append('<div class="body">')
        if cat:
            parts.append(f'<div class="cat">{e(cat)}</div>')
        parts.append(f'<h2>{e(b["title"])}</h2>')
        if b.get("desc"):
            parts.append(f'<p>{e(b["desc"])}</p>')
        meta = []
        if b.get("no"):
            meta.append(f'<span class="no">{e(str(b["no"]))}</span>')
        if b.get("badge"):
            meta.append(f'<span class="badge">{e(b["badge"])}</span>')
        if b.get("date"):
            meta.append(f'<span>{e(b["date"])}</span>')
        if meta:
            parts.append('<div class="meta">' + "".join(meta) + "</div>")
        parts.append("</div></a>")
    parts.append('</div><div class="empty" id="empty" style="display:none">검색 결과가 없습니다.</div>')

    if cfg.get("footer"):
        parts.append(f'<footer>{e(cfg["footer"])}</footer>')

    parts.append("</div>")
    if cfg.get("search") and blocks:
        parts.append(f"<script>{JS}</script>")
    parts.append("</body></html>")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser(description="링크허브 페이지 생성기")
    ap.add_argument("config", help="JSON 설정 파일")
    ap.add_argument("-o", "--out", default=None, help="출력 HTML 경로")
    a = ap.parse_args()
    cfg = json.load(open(os.path.expanduser(a.config), encoding="utf-8"))
    out = a.out or os.path.splitext(a.config)[0] + ".html"
    doc = render(cfg, base_dir=os.path.dirname(os.path.abspath(os.path.expanduser(a.config))))
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)
    print(f"생성 완료: {out}  ({len(cfg.get('blocks') or [])}개 링크, {len(doc)/1024:.0f}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
