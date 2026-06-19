# PROJECT.md — VideoApp (가칭)

## 1. 프로젝트 개요
로그인한 사용자에게 이름이 적힌 버튼들을 보여주고, 버튼을 클릭하면
라이브러리에 등록된 동영상을 재생해 주는 **반응형 웹앱 → PWA**.
안드로이드 폰의 브라우저에서 URL로 접속하며, 최종적으로 "홈 화면에 추가"로
설치형 앱처럼 동작한다.

## 2. 기술 스택 (확정)
- 백엔드/서빙: **FastAPI** + Uvicorn (정적 HTML/CSS/JS 직접 서빙)
- 인증: **Supabase Auth** (회원가입/로그인/세션/토큰 위임)
- 영상 저장: **Supabase Storage** (signed URL 재생)
- DB: Supabase(PostgreSQL) — 영상 카탈로그 테이블, Row Level Security
- 배포: **Railway** (`$PORT` 주입, `os.getenv()` 사용)
- 프론트: 순수 HTML/CSS/JS + Supabase JS SDK (별도 프레임워크 없음)

## 3. 아키텍처 원칙
- **인증은 클라이언트(Supabase JS)가 처리**하고 세션 토큰을 보관한다.
- **FastAPI는 JWT를 검증한 뒤에만** 영상 목록·signed URL을 내려준다.
- 보안 민감 키(SUPABASE_SERVICE_ROLE_KEY)는 **서버에만** 존재한다.
- 영상 URL은 영구 공개하지 않고 **단기 signed URL**로만 제공한다.
- 모든 비밀값은 코드에 하드코딩하지 않고 `os.getenv()`로 읽는다.

## 4. 페이즈 로드맵
| 페이즈 | 범위 | 완료 기준 |
|---|---|---|
| P0 | 골격 + 헬스체크 + 정적 서빙 + Railway 배포 검증 | 로컬·라이브 `/health` 200, pytest green |
| P1 | Supabase Auth (가입/로그인/로그아웃) + JWT 검증 | 토큰으로만 보호 엔드포인트 접근 |
| P2 | 영상 카탈로그(RLS) + 메인화면 버튼 렌더링 | 로그인 후 버튼 목록 표시 |
| P3 | 버튼 클릭 → signed URL → HTML5 재생 | 폰에서 영상 실제 재생 |
| P4 | PWA화 (manifest + service worker + 아이콘) | "홈 화면에 추가" 동작 |
| P5 | (선택) 영상 등록 관리 UI, 에러/로딩 처리 | — |

## 5. 환경변수 (.env.example 기준)
```
SUPABASE_URL=
SUPABASE_ANON_KEY=          # 프론트에 노출되어도 되는 공개 키
SUPABASE_SERVICE_ROLE_KEY=  # 서버 전용, 절대 노출 금지
SUPABASE_JWT_SECRET=        # (P1) JWT 검증용
VIDEO_BUCKET=videos         # Supabase Storage 버킷명
PORT=8000                   # Railway가 주입, 로컬 기본값
```

## 6. 전역 Do Not Break (모든 페이즈 공통)
- 비밀값을 코드/깃에 커밋하지 않는다 (`.env`는 `.gitignore`).
- `os.getenv()`만 사용. `st.secrets` 같은 방식 금지.
- Railway 시작 명령은 반드시 `$PORT`를 사용한다.
- 각 페이즈 종료 시 이전 페이즈의 테스트가 모두 통과해야 다음으로 진행한다.
