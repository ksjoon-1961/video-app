# PROMPT.md — P0: 프로젝트 골격 + 배포 파이프라인 검증

> 본 문서는 PROJECT.md를 상위 컨텍스트로 한다. PROJECT.md를 먼저 읽고 시작할 것.

## 목표
기능(인증·영상)을 얹기 전에 **빈 골격을 만들어 로컬과 Railway 양쪽에서
돌아가는 것**을 먼저 검증한다. 이 페이즈의 핵심 목적은 배포 파이프라인,
`$PORT` 주입, 환경변수 로딩, 정적 파일 서빙을 미리 안정화해
이후 페이즈의 cold-start 리스크를 제거하는 것이다.

## 범위
### In scope
- 프로젝트 폴더 골격 생성
- FastAPI 앱 + `/health` 헬스체크 엔드포인트
- 정적 파일 서빙 + 플레이스홀더 `index.html` (단순 "준비 중" 화면)
- `config.py`로 `os.getenv()` 기반 설정 로딩
- pytest 테스트 골격 + `/health` 테스트
- Railway 배포 설정(Procfile) + 실제 배포 후 라이브 URL 응답 확인

### Out of scope (다음 페이즈)
- 회원가입/로그인/인증 (P1)
- 영상 카탈로그, DB 연동 (P2)
- 영상 재생 (P3)
- PWA manifest/service worker (P4)

## 산출물 (파일 단위)
```
videoapp/
├── requirements.txt          # fastapi, uvicorn[standard], python-dotenv, pytest, httpx
├── .env.example              # PROJECT.md 5장 내용
├── .gitignore                # .env, __pycache__, .venv 등
├── Procfile                  # web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI 인스턴스, /health, 정적/페이지 라우터 등록
│   ├── config.py             # os.getenv 기반 Settings
│   └── routers/
│       ├── __init__.py
│       └── pages.py          # "/" → index.html 반환
├── static/
│   └── css/style.css         # 최소 스타일
├── templates/
│   └── index.html            # "준비 중" 플레이스홀더 (반응형 meta viewport 포함)
└── tests/
    ├── __init__.py
    └── test_health.py        # /health 200 검증
```

## 기술 제약
- Python 3.11+ 기준.
- `app/main.py`는 `app` 객체를 모듈 최상위에 노출 (`app.main:app`).
- 설정값은 전부 `config.py`의 `os.getenv()`로만 읽는다.
- 로컬 실행 명령: `uvicorn app.main:app --reload --port 8000`
- `index.html`에는 `<meta name="viewport" content="width=device-width, initial-scale=1">`를 반드시 포함 (모바일 반응형 기반).
- 외부 의존성 최소화: P0에서는 supabase 패키지 등을 추가하지 않는다.

## Do Not Break
- 비밀값을 코드에 하드코딩하거나 `.env`를 커밋하지 않는다.
- Procfile/시작 명령에서 `$PORT`를 반드시 사용한다 (고정 포트 금지).
- `/health`는 인증 없이 항상 200을 반환해야 한다 (모니터링/배포 점검용).

## 작업 순서
1. 폴더 골격과 빈 파일 생성.
2. `requirements.txt`, `.gitignore`, `.env.example`, `Procfile` 작성.
3. `config.py`: `SUPABASE_URL` 등 환경변수를 `os.getenv()`로 읽는 `Settings` 정의(없으면 None 허용, P0에선 미사용).
4. `app/main.py`: FastAPI 앱 생성, `/health` 추가, `StaticFiles`로 `static/` 마운트, `pages` 라우터 등록.
5. `routers/pages.py`: `"/"`에서 `index.html` 렌더/반환.
6. `templates/index.html`: viewport 포함한 최소 "준비 중" 화면.
7. `tests/test_health.py`: TestClient로 `/health` 200 검증.
8. 로컬에서 `pytest` 통과 및 `uvicorn` 기동 확인.
9. GitHub(ksjoon-1961) 푸시 → Railway 연결 → 배포 → 라이브 URL에서 `/health` 200 확인.

## 완료 기준 (Regression Gate)
- [ ] `pytest`가 로컬에서 모두 통과한다.
- [ ] `uvicorn app.main:app --port 8000` 기동 후 `http://localhost:8000/health` 가 200을 반환한다.
- [ ] `http://localhost:8000/` 에서 "준비 중" 화면이 보인다.
- [ ] Railway 배포 후 라이브 URL의 `/health` 가 200을 반환한다.
- [ ] 저장소에 `.env` 등 비밀값이 커밋되지 않았다.

위 항목이 모두 충족되어야 P1로 진행한다.

## 다음 페이즈 예고 (P1)
Supabase Auth 연동. 프론트에 Supabase JS SDK를 붙여 회원가입/로그인/로그아웃을
구현하고, FastAPI에 `app/auth.py`를 추가해 요청 헤더의 JWT를 검증하는 의존성을
만든다. 검증 통과 시에만 접근 가능한 보호용 더미 엔드포인트(`/api/me`)로 동작을 확인한다.
