# 벤티365 링크허브 (인포크링크형)

블로그 글·예약 채널을 카드형으로 모아 놓은 **단일 HTML 링크 페이지**입니다.
데이터는 네이버 블로그 공식 RSS(`rss.blog.naver.com/venti365`)에서 자동 수집합니다.

## 구성
| 파일 | 역할 |
|---|---|
| `linkhub.py` | 생성기 — JSON 설정 → 단일 HTML (외부 의존 0) |
| `collect_venti365.py` | 데이터 수집기 — 블로그 RSS → `data/venti365.json` |
| `data/venti365.json` | 프로필·고지·CTA·링크 30건 설정 |
| `out/venti365.html` | 결과물 (브라우저로 바로 열림) |
| `docs/index.html` | 배포용 사본 (GitHub Pages 서빙 대상) |
| `preview/*.png` | 렌더 검증 스크린샷 |

## 수동 실행
```bash
python3 collect_venti365.py
python3 linkhub.py data/venti365.json -o out/venti365.html
```

## 자동 갱신
- 크론(프로필 `yoon-hyuncheol`): 매일 **08:00 · 12:00 · 16:00 · 21:00** → `scripts/linkhub_refresh.sh`
- 변경이 없으면 알림을 보내지 않고, 새 글이 반영되면 한 줄로 보고합니다.
- `git remote` 가 설정돼 있으면 **자동 커밋·푸시까지** 수행합니다.

## 배포 (GitHub Pages)
1. 로그인(최초 1회): `gh auth login`
2. 저장소 생성 + 업로드:
   ```bash
   cd ~/Desktop/linkhub
   gh repo create venti365-links --public --source=. --push
   ```
3. 저장소 → Settings → Pages → Source: `Deploy from a branch` → Branch: `main` / **`/docs`** → Save
4. 1~2분 뒤 `https://<계정>.github.io/venti365-links/` 로 공개됩니다.
5. 커스텀 도메인(예: `link.벤티도메인`)은 Pages 설정의 Custom domain 에 입력 후 DNS 에 CNAME 추가.

## 주의
- 페이지에 쓰이는 썸네일은 네이버 블로그 CDN 이미지를 그대로 참조합니다(핫링크, 실측 HTTP 200).
- 링크·제목은 **RSS 실측 수집분**이며 추측으로 채우지 않습니다.
