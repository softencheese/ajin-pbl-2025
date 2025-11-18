# AJIN RFID 물류 추적 시스템

차체 부품 제조 공정에서 RFID 팔레트를 이용한 원자재부터 완제품까지 전체 추적 시스템

## 시스템 구성

```
Raspberry Pi (C/C++) ──► FastAPI (Python) ──► MySQL
                                  │
                                  └──► React (TypeScript)
```

## 기술 스택

- **임베디드**: C/C++ (Raspberry Pi + RFID Reader)
- **백엔드**: FastAPI + Python 3.11+
- **프론트엔드**: React 18 + Vite + TypeScript
- **데이터베이스**: MySQL 8.0
- **컨테이너**: Docker + Docker Compose

## 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집 (비밀번호 변경)
nano .env
```

### 2. Docker Compose 실행

```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 재시작
docker-compose restart api
```

### 3. 접속

- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **프론트엔드**: http://localhost:5173
- **데이터베이스**: localhost:3306

### 4. 개발 모드

```bash
# API 개발
cd src/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# 프론트엔드 개발
cd src/frontend
npm install
npm run dev
```

## 프로젝트 구조

```
Ajin_Pbl/
├── src/                          # 구현 코드 (모든 소스 코드)
│   ├── api/                      # FastAPI 서버
│   │   ├── main.py               # 서버 엔트리포인트
│   │   ├── requirements.txt      # Python 의존성
│   │   └── Dockerfile            # API 서버 컨테이너
│   ├── frontend/                 # React 프론트엔드
│   │   ├── src/                  # React 소스 코드
│   │   ├── package.json          # Node 의존성
│   │   ├── vite.config.ts        # Vite 설정
│   │   └── Dockerfile            # 프론트엔드 컨테이너
│   ├── embedded/                 # C/C++ 임베디드 코드
│   │   └── README.md             # 빌드 가이드
│   ├── database/                 # 데이터베이스
│   │   └── init/                 # 초기화 SQL
│   │       └── 01-schema.sql     # DB 스키마
│   ├── data/                     # 데이터 영구 저장소
│   │   └── mysql/                # MySQL 데이터 (호스트 볼륨)
│   └── logs/                     # 로그 파일
├── docs/                         # 문서
│   ├── api/                      # API 명세
│   ├── database/                 # DB 스키마
│   ├── embedded/                 # 임베디드 인터페이스
│   ├── frontend/                 # 프론트엔드 가이드
│   └── guides/                   # 개발 가이드
├── .specify/                     # Speckit 명세
│   ├── specs/                    # 시스템 명세서
│   └── plans/                    # 구현 계획서
├── docker-compose.yml            # Docker Compose 설정
├── .env.example                  # 환경 변수 예제
├── setup.sh                      # 초기 설정 스크립트
└── README.md                     # 이 파일
```

## 핵심 문서

### 시스템 문서
- **시스템 명세**: `.specify/specs/rfid-logistics-tracking-system.md`
- **구현 계획**: `.specify/plans/implementation-plan.md`
- **설계 가이드**: `docs/guides/design-guide.md`
- **프로젝트 가이드**: `docs/guides/project-guide.md`

### 기술 문서
- **API 엔드포인트**: `docs/api/endpoints.md`
- **DB 스키마**: `docs/database/schema.md`
- **임베디드 인터페이스**: `docs/embedded/interface.md`
- **프론트엔드 컴포넌트**: `docs/frontend/components.md`

## 개발 워크플로우

### Phase 1: MVP (4주)
- [x] 프로젝트 구조 설정
- [ ] Docker 환경 구축
- [ ] 기본 RFID 추적 기능

### Phase 2: 추적성 (3주)
- [ ] FIFO 검증
- [ ] 양방향 추적
- [ ] 드릴다운 UI

### Phase 3: 실시간 (2주)
- [ ] WebSocket 연동
- [ ] 실시간 모니터링

### Phase 4: 운영 (2주)
- [ ] 백업 자동화
- [ ] 권한 관리
- [ ] 문서화

## 데이터 보존

MySQL 데이터는 호스트 볼륨에 저장되어 Docker 컨테이너 삭제/재생성 시에도 유지됩니다:

```bash
# 백업 생성
docker exec ajin-db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ajin_rfid > ./data/backups/backup_$(date +%Y%m%d).sql

# 복구
docker exec -i ajin-db mysql -u root -p${MYSQL_ROOT_PASSWORD} ajin_rfid < ./data/backups/backup_20251117.sql
```

## 테스트

```bash
# API 테스트
cd src/api
pytest tests/

# 프론트엔드 테스트
cd src/frontend
npm run test
```

## 트러블슈팅

### Docker Compose 실행 오류

```bash
# 컨테이너 중지 및 삭제
docker-compose down

# 볼륨까지 삭제 (주의: 데이터 손실)
docker-compose down -v

# 재시작
docker-compose up -d
```

### MySQL 연결 오류

```bash
# DB 헬스체크 확인
docker-compose ps

# DB 로그 확인
docker-compose logs db

# 직접 연결 테스트
docker exec -it ajin-db mysql -u root -p
```

## 라이선스

이 프로젝트는 아진산업 내부 프로젝트입니다.

## 문의

프로젝트 관련 문의: [팀 연락처]
