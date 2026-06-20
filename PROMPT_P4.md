# PROMPT.md — P4: PWA화 ("홈 화면에 추가"로 설치형 앱 만들기)

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. P0~P3가 완료(영상 재생까지)된 상태에서 시작한다.

## 목표
웹앱을 **PWA(Progressive Web App)**로 만들어, 안드로이드 크롬에서 **"홈 화면에 추가"**
시 아이콘이 생기고 주소창 없이 **전체화면 앱처럼** 실행되게 한다.

## PWA 설치 조건 (셋 다 충족해야 설치 가능)
- **HTTPS** 로 서빙 (Railway가 기본 제공 — 이미 충족).
- 유효한 **manifest.json** (이름·아이콘·표시 모드).
- 등록된 **service worker**.

## 사전 준비 (수동)
- 제공된 아이콘 파일 2개를 `static/icons/` 에 넣는다:
  - `static/icons/icon-192.png`
  - `static/icons/icon-512.png`
  (나중에 자체 로고로 교체 가능. 크기 192x192 / 512x512 정사각형 유지)

## 산출물 (파일 단위)
- `static/manifest.json` (신규) — 아래 내용 기준:
  ```json
  {
    "name": "비디오 라이브러리",
    "short_name": "비디오",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#4F46E5",
    "icons": [
      { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
      { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
    ]
  }
  ```
- `static/sw.js` (신규) — 최소 동작 service worker:
  - `install`/`activate` 이벤트 처리, 앱 셸(정적 파일: `/`, css, js, manifest, 아이콘)을 캐시.
  - `fetch` 이벤트: 정적 자원은 캐시 우선(cache-first), **영상/`/api/` 요청은 캐시하지 않고 네트워크로 통과**(용량·보안 때문).
  - 캐시 버전 상수(`CACHE = "v1"`)를 두고, 갱신 시 버전만 올리면 옛 캐시 정리.
- `app/routers/pages.py` (수정) — **`GET /sw.js` 라우트 추가**로 service worker를 **루트 경로에서 서빙**한다.
  (서비스워커의 제어 범위(scope)는 파일이 놓인 경로로 정해진다. `/static/sw.js`로 두면 scope가 `/static/`로 좁아져 앱 전체를 제어하지 못한다. 루트에서 서빙해 scope를 `/`로 만든다. 응답 헤더에 `Service-Worker-Allowed: /` 포함.)
- `templates/index.html` (수정) — `<head>`에 추가:
  - `<link rel="manifest" href="/static/manifest.json">`
  - `<meta name="theme-color" content="#4F46E5">`
  - `<link rel="apple-touch-icon" href="/static/icons/icon-192.png">`
  - 본문 끝에 service worker 등록 스크립트: `if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');`
  - (login.html에도 manifest/theme-color 링크를 동일하게 넣어 로그인 화면부터 일관되게.)
- `tests/test_pages.py` (신규/수정) — `GET /sw.js`가 200 + `Content-Type: application/javascript` 반환, `GET /static/manifest.json` 200 검증.

## 기술 제약
- service worker는 **`/sw.js`(루트)**에서 서빙한다. `/static/` 아래 두지 않는다.
- 영상 파일과 `/api/` 응답은 **절대 캐시하지 않는다**(signed URL 만료·보안·용량 문제).
- `manifest.json`의 `start_url`·`scope`는 `/`로 둔다.
- 기존 동작(로그인, 버튼, 재생)은 그대로 유지되어야 한다.

## Do Not Break
- `/health` 는 인증 없이 항상 200.
- service worker 캐싱이 로그인/인증 흐름을 깨지 않아야 한다(인증·API는 네트워크 통과).
- P0~P3 테스트가 모두 통과해야 한다.
- 비밀값 미커밋.

## 작업 순서
1. 아이콘 2개를 `static/icons/`에 배치.
2. `static/manifest.json` 작성.
3. `static/sw.js` 작성(정적 캐시 + api/영상 네트워크 통과).
4. `pages.py`에 `GET /sw.js` 라우트 추가(루트 scope, 헤더 포함).
5. `index.html`/`login.html`에 manifest·theme-color·아이콘 링크 + sw 등록 스크립트 추가.
6. `pytest` 전체 통과 → 푸시 → Railway 배포.
7. 안드로이드 크롬으로 라이브 URL 접속 → 메뉴에 **"홈 화면에 추가"**가 뜨는지, 추가 후 전체화면으로 실행되는지 확인.

## 완료 기준 (Regression Gate)
- [ ] `static/icons/`에 192/512 아이콘 존재, `/static/manifest.json` 200.
- [ ] `GET /sw.js` 200 + JS Content-Type, service worker 정상 등록.
- [ ] 안드로이드 크롬에서 "홈 화면에 추가"로 설치, 아이콘 생성, 전체화면 실행 확인.
- [ ] 설치된 앱에서도 로그인 → 버튼 → 영상 재생이 정상 동작.
- [ ] `/health` 200 유지, P0~P3 포함 `pytest` 전체 통과.
- [ ] 비밀값 미커밋.

위 항목이 모두 충족되면 **MVP 완성**이다.

## 다음 단계 (선택: P5 이후)
- 영상 등록 관리 UI(이름·파일 업로드)로 운영 편의성 추가.
- 가입 시 이메일 확인(Confirm email) 운영용으로 재활성화 및 검토.
- 영상이 많아지면 목록 페이지네이션, 썸네일, 카테고리.
- 사용자별 시청 권한 분리가 필요하면 videos 테이블·RLS에 소유/그룹 컬럼 추가.
