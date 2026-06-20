# PROMPT.md — P3: 영상 재생 (signed URL + HTML5 video)

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. P0·P1·P2가 완료된 상태에서 시작한다.

## 목표
버튼을 클릭하면 백엔드가 해당 영상의 **단기 signed URL**을 만들어 내려주고,
프론트는 그 URL을 HTML5 `<video>`에 물려 **실제로 영상을 재생**한다.

## 재생 아키텍처 (확정)
- 영상은 **비공개(Private) `videos` 버킷**에 있다. 직접 공개 URL은 없다.
- 프론트가 버튼 클릭 시 `GET /api/videos/{id}/url` 호출(인증 필요).
- 백엔드는 요청자의 **access token으로 Supabase Storage에 signed URL을 요청**한다.
  → secret 키 불필요. 사용자 토큰 + publishable 키 + Storage RLS 정책으로 보호.
- signed URL은 만료 시간이 지나면 무효가 되는 임시 링크다.

## 사전 준비 (수동 — Supabase SQL Editor에서 실행)
```sql
-- 1) 시드 경로를 실제 업로드한 파일 이름에 맞춘다 (대소문자/하이픈 정확히)
update public.videos set storage_path = 'Sample-1.mp4' where sort_order = 1;
update public.videos set storage_path = 'Sample-2.mp4' where sort_order = 2;
update public.videos set storage_path = 'Sample-3.mp4' where sort_order = 3;

-- 2) Storage 접근 RLS: 로그인 사용자가 videos 버킷 객체를 읽을 수 있게 허용
--    (이 정책이 있어야 사용자 토큰으로 signed URL을 만들 수 있다)
create policy "authenticated can read videos bucket"
  on storage.objects for select
  to authenticated
  using (bucket_id = 'videos');
```
> 참고: `storage_path`에는 **버킷명(videos)을 빼고** 버킷 안에서의 경로만 넣는다.
> 버킷명은 백엔드 코드가 따로 지정한다.

## 범위
### In scope
- 백엔드 `GET /api/videos/{id}/url` — 단건 영상의 signed URL 생성·반환
- 프론트: 버튼 클릭 → signed URL 요청 → `<video>` 재생
### Out of scope (다음 페이즈)
- PWA화 (manifest/service worker/아이콘) — P4
- 영상 등록 관리 UI — P5

## 산출물 (파일 단위)
- `app/config.py` (수정) — `VIDEO_BUCKET`(기본값 `videos`), `SIGNED_URL_TTL`(초, 기본 3600) 추가.
- `app/services/storage.py` (신규) — 사용자 토큰으로 Storage sign 엔드포인트 호출:
  `POST {SUPABASE_URL}/storage/v1/object/sign/{VIDEO_BUCKET}/{storage_path}`,
  headers: `apikey: <PUBLISHABLE_KEY>`, `Authorization: Bearer <user_token>`,
  body: `{"expiresIn": <SIGNED_URL_TTL>}`.
  응답의 상대경로 `signedURL`(예: `/object/sign/...`) 앞에 `{SUPABASE_URL}/storage/v1`를 붙여 **완전한 URL**로 만들어 반환.
- `app/services/catalog.py` (수정) — id로 단건 영상(특히 `storage_path`)을 조회하는 함수 추가.
- `app/schemas.py` (수정) — `SignedUrlResponse` 모델(`url`, `expires_in`).
- `app/routers/api.py` (수정) — `GET /api/videos/{id}/url`: 인증 → id로 `storage_path` 조회 → signed URL 생성 → 반환. 없는 id는 404.
- `static/js/app.js` (수정) — 버튼 클릭 핸들러: `/api/videos/{id}/url` 호출 → 받은 `url`을 `<video>`의 `src`로 설정하고 재생. 로딩/에러 표시.
- `templates/index.html` (수정) — 버튼 영역 아래 `<video controls playsinline>` 플레이어 영역 추가.
- `static/css/style.css` (수정) — 플레이어를 모바일 화면 폭에 맞게 반응형으로(가로 100%, 비율 유지).
- `tests/test_api.py` (수정) — `/api/videos/{id}/url` 미인증 401 필수. (선택) Storage 응답을 모킹해 완전한 URL 조립 검증, 없는 id 404 검증.

## 기술 제약
- 백엔드는 **secret 키를 사용하지 않는다.** 사용자 토큰으로 signed URL을 만든다.
- `<video>`에는 모바일 인라인 재생을 위해 `playsinline` 속성을 넣는다(아이폰 등 전체화면 강제 방지).
- signed URL 만료(`SIGNED_URL_TTL`)는 영상 길이보다 넉넉히 잡는다(기본 3600초). 너무 짧으면 재생 도중 만료되어 끊길 수 있다.
- 영상 포맷은 H.264 mp4 기준(안드로이드 호환성).

## Do Not Break
- `/health` 는 인증 없이 항상 200.
- 토큰 없거나 잘못되면 `/api/videos/{id}/url` 는 401.
- P0·P1·P2 테스트가 모두 통과해야 한다.
- 비밀값 미커밋. (publishable 키만 프론트 노출 허용)

## 작업 순서
1. 사전 준비 SQL 2종을 Supabase에서 실행(경로 업데이트 + Storage RLS).
2. `config.py`에 버킷명·TTL 추가, `services/storage.py`에 signed URL 생성 구현.
3. `catalog.py`에 단건 조회 추가, `routers/api.py`에 `/api/videos/{id}/url` 추가.
4. 프론트: 버튼 클릭 → URL 요청 → `<video>` 재생 연결, `index.html`/`style.css` 수정.
5. 로컬에서 로그인 → 버튼 클릭 → 영상이 실제로 재생되는지 확인.
6. `pytest` 전체 통과 → 푸시 → 라이브에서 폰 브라우저로 재생 확인.

## 완료 기준 (Regression Gate)
- [ ] 사전 준비 SQL 실행 완료(경로 일치 + Storage RLS 정책 존재).
- [ ] 토큰 없이 `/api/videos/{id}/url` 호출 시 401.
- [ ] 로그인 후 버튼 클릭 시 영상이 실제로 재생된다(로컬·라이브 모두).
- [ ] 존재하지 않는 id로 호출 시 404.
- [ ] `/health` 200 유지, P0·P1·P2 포함 `pytest` 전체 통과.
- [ ] 비밀값 미커밋.

위 항목이 모두 충족되어야 P4로 진행한다.

## 다음 페이즈 예고 (P4)
PWA화. `manifest.json`(앱 이름·아이콘·시작 URL·표시 모드), 서비스워커(`sw.js`)
등록, 192/512 아이콘을 추가해 안드로이드에서 **"홈 화면에 추가"** 시 설치형 앱처럼
전체화면으로 뜨게 만든다.
