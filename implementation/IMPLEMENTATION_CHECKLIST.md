# 구현 체크리스트

## ✅ 완료된 작업

### 📁 프로젝트 구조
- [x] `implementation/` 폴더에 모든 구현 코드 구조화
- [x] `docs/` 폴더에 문서 정리 및 카테고리화

### 📝 문서 작성
- [x] 시스템 명세서 (`docs/rfid-logistics-tracking-system.md`)
- [x] 구현 계획서 (`docs/implementation-plan.md`)
- [x] 시스템 헌법 (`docs/constitution.md`)
- [x] 설계 가이드 (`docs/guides/design-guide.md`)
- [x] 프로젝트 가이드 (`docs/guides/project-guide.md`)
- [x] API 엔드포인트 명세 (`docs/api/endpoints.md`)
- [x] DB 스키마 명세 (`docs/database/schema.md`)
- [x] 임베디드 인터페이스 (`docs/embedded/interface.md`)
- [x] 프론트엔드 컴포넌트 가이드 (`docs/frontend/components.md`)

### 🐳 Docker 설정
- [x] `docker-compose.yml` 생성 (MySQL, API, Frontend)
- [x] `.env.example` 환경 변수 템플릿
- [x] API 서버 `Dockerfile`
- [x] 프론트엔드 `Dockerfile`
- [x] 데이터 영구 보존 설정 (`implementation/data/mysql`)

### 🗄️ 데이터베이스
- [x] DB 스키마 SQL (`implementation/database/init/01-schema.sql`)
- [x] 10개 테이블 구조 정의
- [x] View 6개 정의
- [x] 트리거 및 제약조건

### 🔧 기본 코드 뼈대
- [x] FastAPI 서버 엔트리포인트 (`implementation/api/main.py`)
- [x] Python 의존성 정의 (`implementation/api/requirements.txt`)
- [x] React 앱 초기 구조 (`implementation/frontend/src/`)
- [x] Vite 설정 (`implementation/frontend/vite.config.ts`)
- [x] Node 의존성 정의 (`implementation/frontend/package.json`)
- [x] 임베디드 README (`implementation/embedded/README.md`)

### 🚀 배포 스크립트
- [x] 자동 설정 스크립트 (`setup.sh`)
- [x] `.gitignore` 설정

---

## 🔄 다음 단계: 구현

### Phase 1: MVP (4주) - 인프라 및 기본 RFID 기능

#### Week 1-2: 인프라 구축
- [ ] **Docker 환경 실행 및 테스트**
  ```bash
  ./setup.sh
  # 또는
  docker-compose up -d
  ```
- [ ] **DB 연결 확인**
  - [ ] API 서버에서 MySQL 연결 테스트
  - [ ] SQLAlchemy 모델 생성
  - [ ] Alembic 마이그레이션 설정

- [ ] **API 서버 기본 구조**
  - [ ] `implementation/api/app/` 디렉토리 구조 생성
    - [ ] `app/models/` - DB 모델
    - [ ] `app/schemas/` - Pydantic 스키마
    - [ ] `app/routes/` - API 라우터
    - [ ] `app/services/` - 비즈니스 로직
    - [ ] `app/database.py` - DB 연결 설정
  - [ ] Health check 엔드포인트 구현
  - [ ] CORS 설정 확인

- [ ] **프론트엔드 기본 구조**
  - [ ] `implementation/frontend/src/` 디렉토리 구조 생성
    - [ ] `api/` - API 클라이언트
    - [ ] `components/` - 재사용 컴포넌트
    - [ ] `pages/` - 페이지 컴포넌트
    - [ ] `hooks/` - 커스텀 훅
    - [ ] `store/` - 상태 관리
    - [ ] `types/` - TypeScript 타입
  - [ ] React Router 설정
  - [ ] Ant Design 통합
  - [ ] Axios API 클라이언트 설정

#### Week 3-4: 핵심 RFID 기능
- [ ] **마스터 데이터 CRUD API**
  - [ ] 원자재 관리 API (`/materials`)
  - [ ] 품번 관리 API (`/parts`)
  - [ ] 공정 관리 API (`/processes`)
  - [ ] 리더기 위치 관리 API (`/reader-locations`)
  - [ ] RFID 태그 관리 API (`/rfid-tags`)

- [ ] **팔레트 관리 API**
  - [ ] 팔레트 생성/조회 API
  - [ ] 팔레트-LOT 연결 API
  - [ ] 팔레트 상태 관리 API

- [ ] **LOT 관리 API**
  - [ ] 중간품 LOT 생성 API
  - [ ] 조립품 LOT 생성 API
  - [ ] 구성 요소 관리 API

- [ ] **RFID 스캔 처리**
  - [ ] `POST /rfid/scan` 구현
  - [ ] 상태 기계 로직 구현
  - [ ] 포트 → 공정/위치 자동 판별
  - [ ] 피드백 명령 생성

- [ ] **프론트엔드 마스터 데이터 페이지**
  - [ ] 원자재 관리 페이지
  - [ ] 품번 관리 페이지
  - [ ] 공정 관리 페이지
  - [ ] 리더기 위치 관리 페이지
  - [ ] LOT 관리 페이지
  - [ ] 팔레트 관리 페이지

### Phase 2: 추적성 (3주) - 검증 및 추적

#### Week 5-6: 검증 로직
- [ ] **FIFO 검증**
  - [ ] FIFO 체크 함수 구현
  - [ ] 경고 메시지 생성
  - [ ] 프론트엔드 경고 표시

- [ ] **오투입 방지**
  - [ ] 품번 검증 로직
  - [ ] 차단 메시지 생성
  - [ ] 프론트엔드 에러 표시

- [ ] **완제품 검증**
  - [ ] `is_final_product` 체크
  - [ ] Finished 상태 전이 제한

#### Week 7: 추적성 쿼리
- [ ] **정방향 추적 API**
  - [ ] `GET /trace/forward` 구현
  - [ ] 코일 → 제품 추적
  - [ ] View 활용 최적화

- [ ] **역방향 추적 API**
  - [ ] `GET /trace/backward` 구현
  - [ ] 제품 → 코일 추적
  - [ ] 조립품 계층 구조 처리

- [ ] **드릴다운 검색**
  - [ ] `GET /trace/drill-down` 구현
  - [ ] 통합 검색 기능

- [ ] **추적성 UI**
  - [ ] 추적성 조회 페이지
  - [ ] 트리 구조 시각화
  - [ ] 타임라인 표시

### Phase 3: 실시간 (2주) - 모니터링

#### Week 8: WebSocket
- [ ] **WebSocket 서버**
  - [ ] Socket.IO 서버 설정
  - [ ] 이벤트 브로드캐스트
  - [ ] 연결 관리

- [ ] **WebSocket 클라이언트**
  - [ ] React에서 Socket.IO 연동
  - [ ] 자동 재연결
  - [ ] 이벤트 핸들러

#### Week 9: 모니터링 UI
- [ ] **대시보드**
  - [ ] 요약 통계 표시
  - [ ] 공정별 현황
  - [ ] 리더기 상태

- [ ] **실시간 모니터링 페이지**
  - [ ] 팔레트 현황 테이블
  - [ ] 최근 이벤트 로그
  - [ ] 실시간 업데이트

- [ ] **재고 현황 페이지**
  - [ ] FIFO 기준 재고 표시
  - [ ] 오래된 재고 경고

### Phase 4: 운영 (2주) - 백업 및 보안

#### Week 10: 백업 및 로깅
- [ ] **자동 백업**
  - [ ] 일일 백업 스크립트
  - [ ] 백업 로테이션
  - [ ] 복구 테스트

- [ ] **로깅**
  - [ ] 구조화된 로그
  - [ ] 로그 파일 로테이션
  - [ ] 에러 추적

#### Week 11: 보안 및 최종 테스트
- [ ] **인증/권한**
  - [ ] JWT 인증 구현
  - [ ] 역할 기반 권한 (RBAC)
  - [ ] 로그인/로그아웃

- [ ] **임베디드 시스템**
  - [ ] C/C++ RFID 클라이언트 구현
  - [ ] 로컬 큐잉
  - [ ] GPIO 피드백 제어

- [ ] **통합 테스트**
  - [ ] 전체 시나리오 테스트
  - [ ] 성능 테스트
  - [ ] 장애 복구 테스트

---

## 🎯 지금 바로 시작하기

### 1. Docker 환경 실행
```bash
./setup.sh
```

### 2. API 서버 개발 시작
```bash
cd implementation/api
# app/ 디렉토리 구조 생성
mkdir -p app/{models,schemas,routes,services}
touch app/__init__.py app/database.py
```

### 3. 프론트엔드 개발 시작
```bash
cd implementation/frontend
npm install
# src/ 디렉토리 구조 생성
mkdir -p src/{api,components,pages,hooks,store,types}
```

### 4. 첫 번째 구현: Health Check
- API: `app/routes/health.py`
- Frontend: API 호출 테스트

---

## 📚 참고 자료

- **구현 계획**: `docs/implementation-plan.md` (전체 로드맵)
- **개발 워크플로우**: `docs/guides/development-workflow.md` (상세 단계)
- **설계 가이드**: `docs/guides/design-guide.md` (아키텍처 패턴)
- **프로젝트 가이드**: `docs/guides/project-guide.md` (Phase별 가이드)
