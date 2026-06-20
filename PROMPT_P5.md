# PROMPT.md — P5: 12버튼 확장 + 미준비 슬롯 + 화면 크기 최적화

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. P0~P4(MVP)가 완료된 상태에서 시작한다.

## 목표
1. 메인 화면의 영상 버튼을 **12개**로 확장하고 각 버튼에 영상을 연결한다.
2. 아직 파일이 준비되지 않은 슬롯은 **"준비 중" 비활성 버튼**으로 표시하고,
   준비된 슬롯만 재생되게 한다.
3. **안드로이드 화면 크기/방향에 맞춰** 12개 버튼이 스크롤 없이 한 화면에
   최적 크기로 보이게 한다(반응형 + 실제 높이 보정).

## 설계 결정 (확정)
- `videos` 표에 **`is_ready`** 컬럼을 추가해 12개 슬롯을 미리 등록한다.
  - `is_ready = true` + `storage_path` 채워짐 → 재생 가능(활성 버튼)
  - `is_ready = false` → "준비 중" 비활성 버튼, 재생 링크 발급 안 함
- 화면 최적화는 **CSS 그리드 + `dvh` 단위 + JS 높이 보정**의 조합으로 한다.
  서버가 폰 기종을 알 필요 없이, **브라우저가 자기 화면 크기를 읽어** 맞춘다.

## 사전 준비 (수동 — Supabase SQL Editor에서 실행)
```sql
-- 1) 준비됨 여부 컬럼 추가 (없을 때만)
alter table public.videos
  add column if not exists is_ready boolean not null default false;

-- 2) 이미 올린 3개는 '준비됨'으로 표시
update public.videos set is_ready = true where sort_order in (1, 2, 3);

-- 3) 4~12번 슬롯을 '준비 중'으로 미리 등록 (storage_path는 빈 값)
insert into public.videos (name, storage_path, sort_order, is_ready) values
  ('영상 4',  '', 4,  false),
  ('영상 5',  '', 5,  false),
  ('영상 6',  '', 6,  false),
  ('영상 7',  '', 7,  false),
  ('영상 8',  '', 8,  false),
  ('영상 9',  '', 9,  false),
  ('영상 10', '', 10, false),
  ('영상 11', '', 11, false),
  ('영상 12', '', 12, false);
```
> 나중에 영상이 준비되면 해당 슬롯에
> `update public.videos set storage_path='파일명.mp4', is_ready=true where sort_order=4;`
> 처럼 켜기만 하면 활성화된다.

## 범위
### In scope
- 12개 슬롯 표시(준비/미준비 구분), 미준비 버튼 비활성 + 안내
- 미준비 영상에 대한 재생 링크 발급 거부
- 화면 크기/방향에 맞춘 그리드 자동 배치(세로 3×4, 가로 4×3)
### Out of scope (다음 페이즈)
- 영상 등록 관리 화면(SQL 없이 추가) — 이후 별도 페이즈
- 썸네일/카테고리

## 산출물 (파일 단위)
- `app/schemas.py` (수정) — `Video`에 `is_ready: bool` 추가.
- `app/services/catalog.py` (수정) — 목록 조회 시 `is_ready` 포함. 단건 조회 함수는
  `is_ready`와 `storage_path`도 함께 돌려준다.
- `app/routers/api.py` (수정)
  - `GET /api/videos` — 12개 슬롯을 `sort_order` 순으로 반환(각 항목에 `is_ready`).
  - `GET /api/videos/{id}/url` — 대상이 **`is_ready=false`거나 `storage_path`가 비면 409**
    (예: `{"detail": "video not ready"}`)로 거부. 준비된 경우에만 signed URL 발급.
- `static/js/app.js` (수정)
  - 12개 버튼 렌더. `is_ready=false`면 `disabled` + "준비 중" 라벨/클래스 부여.
  - 활성 버튼 클릭 → 재생. 미준비 버튼 클릭 → "준비 중입니다" 안내(재생 시도 안 함).
  - **화면 높이 보정**: `setAppHeight()`가 `window.innerHeight`를 읽어 CSS 변수
    `--app-height`에 px로 주입. 초기 1회 + `resize`/`orientationchange` 때마다 갱신.
- `static/css/style.css` (수정)
  - 버튼 영역을 **CSS Grid**로: 세로(portrait) `grid-template-columns: repeat(3, 1fr)`,
    가로(landscape)는 `@media (orientation: landscape)`로 `repeat(4, 1fr)`.
  - 컨테이너 높이는 `var(--app-height)`(JS 주입값) 기반, 폴백으로 `100dvh` 사용.
  - 버튼/글자 크기는 `clamp()`로 유동. 터치 영역 충분히 확보.
  - "준비 중" 버튼은 흐리게(낮은 채도/투명도) + 커서/포인터 비활성 스타일.
- `templates/index.html` (수정) — viewport에 `viewport-fit=cover` 포함, 그리드 컨테이너 구조 정리.
- `static/sw.js` (수정) — 정적 파일이 바뀌므로 **캐시 버전 올리기**(예: `"v2"` → `"v3"`).
- `tests/test_api.py` (수정) — ① 미인증 401 유지 ② 미준비 영상 `/url` 요청 시 409
  ③ `/api/videos` 응답에 12개 항목과 `is_ready` 필드 포함 검증.

## 기술 제약
- 미준비 영상은 **백엔드에서도 반드시 차단**한다(프론트 비활성만 믿지 않는다).
- `100vh` 단독 사용 금지(모바일 주소창 문제). `dvh` + `--app-height` 보정 사용.
- 12개가 **스크롤 없이** 한 화면에 들어오도록 그리드 행/열로 공간을 분배한다.
- 세로/가로 회전 모두 대응한다.
- 기존 로그인·재생·signed URL 동작을 깨지 않는다.

## Do Not Break
- `/health` 인증 없이 200 유지.
- 준비된 영상의 재생은 종전대로 정상 동작.
- 미준비 영상은 재생 링크가 발급되지 않는다.
- P0~P4 테스트가 모두 통과해야 한다.
- 비밀값 미커밋.

## 작업 순서
1. 사전 준비 SQL 실행(컬럼 추가 + 12슬롯 등록 + 3개 준비 표시).
2. `schemas.py`/`catalog.py`/`api.py`에 `is_ready` 반영, 미준비 차단 추가.
3. `app.js`에 12버튼 렌더·비활성 처리·화면 높이 보정 구현.
4. `style.css`에 그리드/반응형/방향 대응/준비중 스타일 추가, `index.html` viewport 정리.
5. `sw.js` 캐시 버전 올림.
6. 로컬·폰에서 확인: 12버튼 표시, 준비된 3개 재생, 나머지 "준비 중", 세로/가로 모두 한 화면에 맞음.
7. `pytest` 전체 통과 → 푸시 → Railway 배포 → 폰 재확인(필요 시 아이콘/캐시 갱신).

## 완료 기준 (Regression Gate)
- [ ] 메인 화면에 12개 버튼이 보인다(준비 3 + 준비중 9).
- [ ] 준비된 버튼 클릭 시 영상 재생, 미준비 버튼은 비활성 + "준비 중" 안내.
- [ ] 미준비 영상 `/api/videos/{id}/url` 호출 시 409.
- [ ] 세로·가로 양쪽에서 12개 버튼이 스크롤 없이 한 화면에 보인다(여러 폰 폭에서).
- [ ] `/health` 200 유지, P0~P4 포함 `pytest` 전체 통과.
- [ ] `sw.js` 캐시 버전이 올라가 새 화면이 반영된다.

위 항목이 모두 충족되면 P5 완료.

## 참고: 나중에 영상 추가로 활성화하는 법
1. Storage `videos` 버킷에 mp4 업로드(파일명 메모, 대소문자 정확히).
2. SQL: `update public.videos set storage_path='파일명.mp4', is_ready=true, name='제목' where sort_order=<번호>;`
끝나면 해당 버튼이 자동으로 활성화되어 재생된다.
