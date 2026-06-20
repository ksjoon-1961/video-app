# PROMPT.md — P2: 영상 카탈로그 + 메인화면 버튼 렌더링

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. P0·P1이 완료된 상태에서 시작한다.

## 목표
Supabase에 영상 메타데이터 테이블(`videos`)을 만들고 RLS로 로그인 사용자만 읽도록
설정한다. 백엔드 `GET /api/videos`가 목록을 반환하고, 로그인 후 메인 화면에 영상
**이름 버튼들을 동적으로 렌더링**한다. (실제 재생은 P3)

## 데이터 흐름 (확정)
- 영상 목록도 **백엔드 `/api/videos`가 내려준다** (PROJECT.md 원칙 유지).
- 백엔드는 요청자의 **access token을 그대로 Supabase PostgREST에 전달**해 조회한다.
  → RLS가 그대로 작동하므로 **secret 키 불필요**. publishable 키(apikey 헤더) + 사용자 토큰만 사용.
- P2에서는 **메타데이터만** 다룬다. 실제 파일 재생/ signed URL은 P3.

## 사전 준비 (수동 — Supabase SQL Editor에서 실행)
```sql
-- 1) 테이블
create table public.videos (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  storage_path text not null,        -- 예: 'videos/sample1.mp4' (P3에서 재생에 사용)
  sort_order int default 0,
  created_at timestamptz default now()
);

-- 2) RLS 활성화 + 로그인 사용자 읽기 허용
alter table public.videos enable row level security;
create policy "authenticated can read videos"
  on public.videos for select
  to authenticated
  using (true);

-- 3) 시드 데이터 (P2 확인용 — storage_path는 임시값 가능)
insert into public.videos (name, storage_path, sort_order) values
  ('샘플 영상 1', 'videos/sample1.mp4', 1),
  ('샘플 영상 2', 'videos/sample2.mp4', 2),
  ('샘플 영상 3', 'videos/sample3.mp4', 3);
```
> RLS를 활성화했으므로, 위 정책 없이는 어떤 클라이언트도 조회할 수 없다(보안 기본값).

## 범위
### In scope
- `videos` 테이블 조회 백엔드 엔드포인트 `GET /api/videos` (인증 필요)
- 사용자 토큰 기반 PostgREST 조회 서비스
- 로그인 후 메인 화면에 이름 버튼 동적 렌더링
### Out of scope (다음 페이즈)
- signed URL 생성, 실제 영상 재생 (P3)
- PWA화 (P4), 영상 등록 관리 UI (P5)

## 산출물 (파일 단위)
- `app/auth.py` (수정) — 검증된 클레임뿐 아니라 **원본 토큰도 함께 제공**하는 의존성 추가
  (예: `get_auth_context()` → `{"user": claims, "token": raw_token}`). 기존 `get_current_user`는 유지.
- `app/schemas.py` (수정) — `Video` 모델 추가 (`id`, `name`, `storage_path`, `sort_order`).
- `app/services/catalog.py` (신규) — 사용자 토큰으로 PostgREST 호출해 `videos`를 `sort_order` 순으로 조회.
  `GET {SUPABASE_URL}/rest/v1/videos?select=*&order=sort_order`,
  headers: `apikey: <PUBLISHABLE_KEY>`, `Authorization: Bearer <user_token>`. httpx 사용.
- `app/routers/api.py` (수정) — `GET /api/videos` 추가, 인증 의존성 적용, `List[Video]` 반환.
- `static/js/app.js` (수정) — 로그인 세션 확인 → access token으로 `/api/videos` 호출 → 응답을 순회하며 이름 버튼 렌더링. 버튼 클릭 핸들러는 P3 자리만 잡아둔다(클릭 시 콘솔 로그/placeholder).
- `templates/index.html` (수정) — 버튼들이 들어갈 컨테이너(`#video-buttons`) 추가, 반응형 그리드 스타일.
- `static/css/style.css` (수정) — 버튼 그리드 최소 스타일(모바일 폭 기준 세로 정렬/터치 영역 충분히).
- `tests/test_api.py` (수정/신규) — `/api/videos` 미인증 401 테스트 필수. (선택) PostgREST 응답을 모킹해 목록 반환·정렬 검증.

## 기술 제약
- 백엔드는 **secret 키를 사용하지 않는다.** 사용자 토큰 + publishable 키만으로 조회.
- PostgREST 호출은 httpx로 수행하고, 사용자 토큰을 그대로 전달해 RLS가 적용되게 한다.
- 버튼은 하드코딩하지 않고 **항상 `/api/videos` 응답으로 동적 생성**한다.
- 모바일 터치 대상 크기를 충분히 확보한다(버튼 최소 높이 등).

## Do Not Break
- `/health` 는 인증 없이 항상 200.
- 토큰 없거나 잘못되면 `/api/videos` 는 401.
- P0·P1 테스트가 모두 통과해야 한다.
- `.env`·secret 등 비밀값 미커밋. (publishable 키만 프론트 노출 허용)

## 작업 순서
1. 사전 준비 SQL을 Supabase에서 실행하고 시드가 들어갔는지 확인.
2. `auth.py`에 원본 토큰까지 제공하는 의존성 추가.
3. `schemas.py`에 `Video` 모델, `services/catalog.py`에 조회 로직 구현.
4. `routers/api.py`에 `GET /api/videos` 추가.
5. 프론트 `app.js`에서 목록을 받아 버튼 렌더링, `index.html`/`style.css` 수정.
6. 로컬에서 로그인 후 시드 영상 이름 버튼 3개가 보이는지 확인.
7. `pytest` 전체 통과 → 푸시 → 라이브에서 동일 확인.

## 완료 기준 (Regression Gate)
- [ ] Supabase에 `videos` 테이블 + RLS 정책 + 시드 데이터 존재.
- [ ] 토큰 없이 `GET /api/videos` 호출 시 401.
- [ ] 로그인 후 `GET /api/videos` 가 시드 목록을 `sort_order` 순으로 반환.
- [ ] 로그인 후 메인 화면에 영상 이름 버튼들이 동적으로 표시된다.
- [ ] `/health` 200 유지, P0·P1 포함 `pytest` 전체 통과.
- [ ] 비밀값 미커밋.

위 항목이 모두 충족되어야 P3로 진행한다.

## 다음 페이즈 예고 (P3)
영상 재생. 백엔드 `GET /api/videos/{id}/url` 가 해당 영상의 `storage_path`로
Supabase Storage **단기 signed URL**을 생성해 반환하고, 프론트는 버튼 클릭 시 이
URL을 HTML5 `<video>`에 물려 재생한다. 영상 파일을 Storage 버킷(`videos`)에
업로드하는 사전 준비도 포함된다.
