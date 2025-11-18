       # 프로젝트 개발 가이드

## 문서 개요
AJIN RFID 물류 추적 시스템 개발을 위한 전체 가이드입니다.

---

## 📚 문서 구조

### 핵심 명세 문서
1. **`.specify/specs/rfid-logistics-tracking-system.md`** - 시스템 전체 명세 (Specify)
2. **`.specify/plans/implementation-plan.md`** - 구현 계획 (Plan)

### API 문서
- `docs/api/api-server-spec.md` - API 서버 상세 명세
- `docs/api/endpoints.md` - API 엔드포인트 전체 목록

### 임베디드 문서
- `docs/embedded/embedded-system-spec.md` - 임베디드 시스템 상세 명세
- `docs/embedded/interface.md` - RFID 리더기 인터페이스 명세

### 프론트엔드 문서
- `docs/frontend/web-app-spec.md` - 웹 애플리케이션 상세 명세
- `docs/frontend/components.md` - React 컴포넌트 가이드

### 데이터베이스 문서
- `docs/database/schema.md` - 데이터베이스 스키마 명세
- `docs/database/database-architecture.md` - DB 아키텍처
- `docs/database/pallet-state-machine.md` - 팔레트 상태 기계

### 가이드 문서
- `docs/guides/GETTING_STARTED.md` - 시작 가이드
- `docs/guides/development-workflow.md` - 개발 워크플로우
- `docs/guides/project-guide.md` - 이 문서

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론
git clone <repository-url>
cd Ajin_Pbl

# 환경 변수 설정
cp .env.example .env
nano .env  # 비밀번호 변경

# 데이터베이스 스키마 준비
cp temp/DB/Ajin_DB.sql database/init/01-schema.sql
```

### 2. Docker로 전체 시스템 실행
```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 접속
# - API: http://localhost:8000/docs
# - Frontend: http://localhost:5173
# - DB: localhost:3306
```

### 3. 로컬 개발 모드
```bash
# API 개발
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend 개발
cd frontend
npm install
npm run dev

# Embedded 개발 (Raspberry Pi)
cd embedded
mkdir build && cd build
cmake ..
make
```

---

## 📖 개발 순서

### Phase 1: MVP (4주)

**Week 1-2: 인프라 구축**
1. Docker Compose 환경 설정
2. MySQL 스키마 생성
3. FastAPI 기본 구조 생성
   - `api/app/models/` - SQLAlchemy 모델
   - `api/app/routers/` - 기본 라우터
4. React 기본 구조 생성
   - 레이아웃 컴포넌트
   - 라우팅 설정

**참고 문서**:
- `.specify/plans/implementation-plan.md` (섹션 2: 프로젝트 구조)
- `docs/database/schema.md`

**Week 3-4: 핵심 RFID 기능**
1. 임베디드 시스템 개발
   - RFID 리더기 통신
   - API 서버 연동
   - GPIO 제어 (부저, LED)
   
2. API 서버 개발
   - `POST /api/v1/rfid/scan` 구현
   - 상태 전이 로직
   - 기본 검증 (오투입)
   
3. 웹 개발
   - 팔레트 등록 화면
   - 리더기 매핑 화면
   - 기본 모니터링

**참고 문서**:
- `docs/embedded/interface.md`
- `docs/api/endpoints.md`
- `docs/frontend/components.md`

**검증**: 샤링 → 프레스 단일 공정 흐름 동작

---

### Phase 2: 추적성 및 검증 (3주)

**Week 5-6: 검증 로직**
1. FIFO 검증 구현
2. 오투입 검증 강화
3. 완제품 검증

**Week 7: 추적성 구현**
1. 정방향 추적 (코일 → 제품)
2. 역방향 추적 (제품 → 코일)
3. 드릴다운 UI

**참고 문서**:
- `docs/api/api-server-spec.md` (섹션 2.2.3: 추적성 조회)
- `docs/database/schema.md` (Views 섹션)

**검증**: 전체 공정 추적 확인

---

### Phase 3: 실시간 및 최적화 (2주)

**Week 8: 실시간 통신**
1. WebSocket 구현
2. 실시간 모니터링 화면
3. 실시간 이벤트 알림

**Week 9: 최적화**
1. DB 인덱싱
2. API 성능 최적화
3. 프론트엔드 최적화

**참고 문서**:
- `docs/api/endpoints.md` (WebSocket 이벤트 섹션)
- `docs/database/schema.md` (인덱스 전략)

**검증**: 동시 50명, 초당 10개 스캔 처리

---

### Phase 4: 운영 및 안정화 (2주)

**Week 10-11**
1. 권한 관리
2. 백업 자동화
3. 모니터링 및 알림
4. 문서화 및 사용자 교육

**검증**: 24시간 무정지 운영

---

## 🔧 개발 환경 설정

### API 서버 (FastAPI)

**필수 패키지**:
```bash
pip install fastapi uvicorn sqlalchemy pymysql pydantic python-jose passlib
```

**디렉토리 구조**:
```
api/
├── app/
│   ├── models/      # SQLAlchemy 모델
│   ├── routers/     # API 라우터
│   ├── services/    # 비즈니스 로직
│   ├── schemas/     # Pydantic 스키마
│   └── database.py  # DB 연결
└── main.py          # FastAPI 앱
```

**개발 실행**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### 프론트엔드 (React)

**필수 패키지**:
```bash
npm install react react-dom react-router-dom @tanstack/react-query zustand axios antd socket.io-client
```

**디렉토리 구조**:
```
frontend/src/
├── api/           # API 클라이언트
├── components/    # 재사용 컴포넌트
├── pages/         # 페이지
├── hooks/         # 커스텀 훅
├── store/         # 상태 관리
└── types/         # TypeScript 타입
```

**개발 실행**:
```bash
npm run dev
```

---

### 임베디드 (C/C++)

**필수 라이브러리**:
```bash
sudo apt-get install build-essential cmake libcurl4-openssl-dev libjson-c-dev wiringpi
```

**빌드**:
```bash
mkdir build && cd build
cmake ..
make
```

**배포**:
```bash
sudo systemctl enable ajin-rfid
sudo systemctl start ajin-rfid
```

---

## 📝 코딩 컨벤션

### Python (FastAPI)
- PEP 8 준수
- 타입 힌트 사용
- Docstring (Google 스타일)

```python
from typing import List, Optional
from pydantic import BaseModel

class PalletResponse(BaseModel):
    """팔레트 응답 모델"""
    id: int
    pallet_no: str
    status: str
    
def get_pallets(status: Optional[str] = None) -> List[PalletResponse]:
    """
    팔레트 목록을 조회합니다.
    
    Args:
        status: 필터링할 상태 (선택)
    
    Returns:
        팔레트 목록
    """
    pass
```

### TypeScript (React)
- ESLint + Prettier
- 함수형 컴포넌트
- 타입 우선 (any 금지)

```typescript
interface PalletProps {
  pallet: Pallet;
  onClick?: () => void;
}

export function PalletCard({ pallet, onClick }: PalletProps) {
  // ...
}
```

### C/C++ (Embedded)
- 함수명: snake_case
- 상수: UPPER_CASE
- 구조체: _t 접미사

```c
#define MAX_QUEUE_SIZE 1000

typedef struct {
    char epc[25];
    uint64_t timestamp_ms;
} scan_event_t;

int rfid_reader_init(const char *port, int baudrate);
```

---

## 🧪 테스트

### API 테스트
```bash
cd api
pytest tests/
```

### 프론트엔드 테스트
```bash
cd frontend
npm run test
```

### 통합 테스트
```bash
# API 서버 실행 후
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/pallets
```

---

## 📦 배포

### Docker Compose (프로덕션)
```bash
# 프로덕션 환경 변수 설정
cp .env.example .env.production
nano .env.production

# 프로덕션 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d
```

### 백업
```bash
# 데이터베이스 백업
docker exec ajin-db mysqldump -u root -p ajin_rfid > backup_$(date +%Y%m%d).sql

# 자동 백업 (cron)
0 3 * * * /opt/ajin-rfid/scripts/backup.sh
```

---

## 🐛 트러블슈팅

### Docker 관련
```bash
# 컨테이너 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f api
docker-compose logs -f db

# 캐시 삭제 후 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### API 서버 500 에러
```bash
# API 컨테이너 접속
docker exec -it ajin-api bash

# DB 연결 테스트
python -c "from app.database import engine; print(engine.connect())"
```

### MySQL 연결 실패
```bash
# DB 상태 확인
docker-compose ps db

# DB 로그 확인
docker-compose logs db

# 직접 연결 테스트
docker exec -it ajin-db mysql -u root -p
```

---

## 📊 성능 최적화

### API 서버
1. DB 쿼리 최적화 (EXPLAIN 사용)
2. 인덱스 추가
3. 캐싱 (Redis - 선택 사항)

### 프론트엔드
1. 코드 스플리팅
2. Lazy Loading
3. React.memo 사용

### 데이터베이스
1. 적절한 인덱스
2. 파티셔닝 (대용량 테이블)
3. 정기적인 ANALYZE TABLE

---

## 🔒 보안 체크리스트

- [ ] `.env` 파일 Git에서 제외
- [ ] API 인증 (JWT) 구현
- [ ] HTTPS 적용 (프로덕션)
- [ ] SQL Injection 방어 (ORM 사용)
- [ ] CORS 설정 (특정 도메인만)
- [ ] 비밀번호 해싱 (bcrypt)
- [ ] 감사 로그 기록

---

## 📞 도움말

### 문서 위치
- 시스템 명세: `.specify/specs/rfid-logistics-tracking-system.md`
- 구현 계획: `.specify/plans/implementation-plan.md`
- API 문서: http://localhost:8000/docs (Swagger UI)

### 디버깅 도구
- FastAPI: Swagger UI (`/docs`)
- React: React DevTools
- MySQL: MySQL Workbench

### 유용한 명령어
```bash
# 전체 시스템 상태
docker-compose ps

# 특정 서비스 재시작
docker-compose restart api

# 데이터베이스 백업
./scripts/backup.sh

# 로그 실시간 확인
docker-compose logs -f
```

---

## 🎯 개발 체크리스트

### Phase 1 완료 기준
- [ ] Docker Compose 환경 동작
- [ ] API 서버 `/health` 응답
- [ ] 프론트엔드 화면 로드
- [ ] DB 연결 및 스키마 생성
- [ ] RFID 스캔 → 상태 전이 동작

### Phase 2 완료 기준
- [ ] FIFO 검증 동작
- [ ] 오투입 차단 동작
- [ ] 정방향 추적 조회
- [ ] 역방향 추적 조회
- [ ] 드릴다운 UI 동작

### Phase 3 완료 기준
- [ ] WebSocket 실시간 업데이트
- [ ] 동시 50명 접속 지원
- [ ] 초당 10개 스캔 처리
- [ ] 응답 시간 1초 이내

### Phase 4 완료 기준
- [ ] 24시간 무정지 운영
- [ ] 자동 백업 동작
- [ ] 사용자 교육 자료 완성
- [ ] 롤백 계획 수립

---

이 가이드는 프로젝트 진행 중 계속 업데이트됩니다.
