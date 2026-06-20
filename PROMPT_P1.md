# PROMPT.md — P1: Supabase Auth 연동 (가입/로그인/로그아웃 + JWT 검증)

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. P0이 완료된 상태에서 시작한다.

## 목표
프론트엔드에 Supabase JS SDK를 붙여 **회원가입 / 로그인 / 로그아웃**을 구현하고,
FastAPI에 **JWKS 기반 JWT 검증 의존성**을 추가한다. 검증을 통과한 요청만 접근
가능한 보호 엔드포인트 `/api/me` 로 동작을 확인한다.

## 인증 아키텍처 (확정)
- 인증은 **브라우저의 Supabase JS**가 처리하고 access token(JWT)을 보관한다.
- 프론트는 보호된 API 호출 시 `Authorization: Bearer <access_token>` 헤더를 붙인다.
- 백엔드는 **비대칭(ES256) JWT를 JWKS 공개키로 로컬 검증**한다 (Auth 서버 round-trip 없음).
- 서명용 비밀키는 Supabase를 벗어나지 않는다. 백엔드는 **공개키 검증만** 한다.
- 따라서 P1 백엔드는 `secret` 키가 불필요하다. publishable 키만 프론트에서 사용.

## 사전 준비 (수동 — 코딩 전에 사람이 확인)
1. Supabase 프로젝트 생성(또는 기존 프로젝트 선택).
2. Dashboard → Authentication → Signing Keys 에서 **비대칭(ES256) signing key가 활성(Active)** 인지 확인. (레거시 HS256만 있으면 standby 키를 생성 후 Rotate)
3. 아래 값 확보:
   - `SUPABASE_URL` = `https://<project-ref>.supabase.co`
   - JWKS URL = `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`
   - `SUPABASE_PUBLISHABLE_KEY` = `sb_publishable_...` (Dashboard → API Keys)
4. Authentication → Providers 에서 Email 활성화. 테스트 편의상 "Confirm email" 옵션은 개발 중 비활성화 가능(운영 전 재검토).
5. 위 값을 로컬 `.env` 와 Railway Variables 양쪽에 입력.

## 범위
### In scope
- 프론트: 가입/로그인/로그아웃 UI + Supabase JS 세션 처리
- 백엔드: JWKS 공개키 캐싱 + JWT 검증 의존성 + `/api/me`
- 미인증/만료 토큰에 대한 401 처리
### Out of scope (다음 페이즈)
- 영상 카탈로그 테이블, 버튼 렌더링 (P2)
- 영상 재생 (P3), PWA화 (P4)

## 산출물 (파일 단위)
- `requirements.txt` — `pyjwt[crypto]` 추가 (ES256 검증에 cryptography 필요). httpx는 P0 유지.
- `app/config.py` — 환경변수 추가: `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWT_AUDIENCE`(기본값 `authenticated`).
- `app/auth.py` (신규) — `PyJWKClient`로 JWKS를 가져와 캐싱. `get_current_user()` 의존성: Bearer 토큰 추출 → ES256 검증(issuer=`<SUPABASE_URL>/auth/v1`, audience=`authenticated`) → 실패 시 401, 성공 시 사용자 클레임 반환.
- `app/schemas.py` — `User` Pydantic 모델 (id=sub, email 등).
- `app/routers/api.py` (신규) — `GET /api/me`, `get_current_user` 의존성 적용, 사용자 정보 반환.
- `static/js/supabase-client.js` (신규) — `createClient(SUPABASE_URL, PUBLISHABLE_KEY)` 초기화. (키는 페이지 템플릿에서 주입하거나 `/config.js` 엔드포인트로 노출)
- `static/js/auth.js` (신규) — `signUp`, `signIn`, `signOut`, 세션 변경 구독, access token으로 `/api/me` 호출 데모.
- `templates/login.html` (신규) — 이메일/비밀번호 가입·로그인 폼.
- `templates/index.html` (수정) — 로그인 상태면 환영 메시지+로그아웃 버튼, 아니면 login으로 유도.
- `tests/test_auth.py` (신규) — 미인증 401 테스트 필수. (선택) 자체 생성한 테스트 EC 키페어로 토큰을 서명해 JWKS를 모킹하고 검증 통과 케이스 테스트.

## 기술 제약
- JWT 검증 라이브러리는 **PyJWT(`pyjwt[crypto]`)** 의 `PyJWKClient` 사용.
- JWKS는 앱 시작 시 또는 첫 요청 시 1회 가져와 캐싱하고, `kid` 불일치 시에만 재요청.
- 검증 시 `algorithms=["ES256"]`, `audience`, `issuer`를 명시적으로 검증한다.
- publishable 키는 공개되어도 되는 값이므로 프론트 노출 허용. **secret 키는 P1에서 사용 금지.**
- 비밀번호 해싱·세션 저장을 직접 구현하지 않는다 (전부 Supabase 위임).

## Do Not Break
- `/health` 는 인증 없이 항상 200 (P0 불변식 유지).
- P0의 기존 테스트가 모두 통과해야 한다.
- `.env` 및 어떤 비밀값도 커밋하지 않는다.
- 보호 엔드포인트는 토큰 없거나 잘못되면 반드시 401을 반환한다 (조용히 통과 금지).

## 작업 순서
1. 사전 준비 값이 `.env`에 채워졌는지 확인.
2. `requirements.txt` 갱신, `config.py`에 환경변수 추가.
3. `app/auth.py`에 JWKS 클라이언트와 `get_current_user` 의존성 구현.
4. `schemas.py`에 `User` 모델, `routers/api.py`에 `/api/me` 추가 후 `main.py`에 라우터 등록.
5. 프론트: `supabase-client.js`, `auth.js`, `login.html` 작성, `index.html` 수정.
6. `tests/test_auth.py` 작성 (미인증 401 + 선택적 모킹 검증).
7. 로컬에서 가입 → 로그인 → `/api/me`가 사용자 정보 반환, 로그아웃 후 401 확인.
8. `pytest` 전체 통과 확인 후 푸시 → Railway 환경변수 입력 → 라이브에서 동일 흐름 확인.

## 완료 기준 (Regression Gate)
- [ ] 신규 이메일로 가입 후 로그인하면 access token이 발급된다.
- [ ] 유효 토큰으로 `GET /api/me` 호출 시 200 + 본인 email/id 반환.
- [ ] 토큰 없이/만료·위조 토큰으로 `/api/me` 호출 시 401.
- [ ] 로그아웃 후 `/api/me` 호출 시 401.
- [ ] `/health`는 여전히 인증 없이 200.
- [ ] P0 포함 `pytest` 전체 통과.
- [ ] 비밀값 미커밋.

위 항목이 모두 충족되어야 P2로 진행한다.

## 다음 페이즈 예고 (P2)
영상 카탈로그. Supabase에 `videos` 테이블(이름, 스토리지 경로 등)을 만들고 RLS로
로그인 사용자만 읽도록 설정. `GET /api/videos`가 목록을 반환하고, 로그인 후 메인
화면에 이름 버튼들을 동적으로 렌더링한다. (재생은 P3)
