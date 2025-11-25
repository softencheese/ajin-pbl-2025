# RFID 물류 추적 시스템 구현 계획서 (Implementation Plan)

## 문서 정보
- **버전**: 1.0.0
- **작성일**: 2025-11-17
- **기반 명세**: `.specify/specs/rfid-logistics-tracking-system.md`
- **목적**: 기술 스택 선정 및 구체적 구현 계획 수립

---

## 1. 기술 스택 결정

### 1.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                    │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Embedded     │  │ API Server   │  │ Frontend   │ │
│  │ (C/C++)      │  │ (FastAPI)    │  │ (React)    │ │
│  │ + Raspberry  │  │ + Python     │  │ + Vite     │ │
│  │   Pi         │  │   3.11+      │  │            │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │       │
│         └─────────────────┼─────────────────┘       │
│                           │                         │
│                   ┌───────┴────────┐                │
│                   │   MySQL 8.0    │                │
│                   │   + Volume     │                │
│                   └────────────────┘                │
└─────────────────────────────────────────────────────┘
                           │
                 ┌─────────┴─────────┐
                 │  Host Volume      │
                 │  /data/mysql      │
                 │  (Data Pipeline)  │
                 └───────────────────┘
```

### 1.2 컴포넌트별 기술 스택

| 컴포넌트 | 기술 스택 | 선정 이유 |
|---------|----------|----------|
| **임베디드** | C/C++, Raspberry Pi | • 하드웨어 제어 최적화<br>• RFID 리더기 시리얼/네트워크 통신<br>• 저전력 운영 |
| **API 서버** | FastAPI + Python 3.11+ | • 빠른 개발 속도<br>• 자동 API 문서 생성<br>• 비동기 처리 지원<br>• MySQL 연동 용이 |
| **데이터베이스** | MySQL 8.0 | • 트랜잭션 무결성<br>• 복잡한 JOIN 쿼리 최적화<br>• 추적성 뷰 지원<br>• 운영 안정성 |
| **프론트엔드** | React 18 + Vite + TypeScript | • 컴포넌트 재사용성<br>• 풍부한 UI 라이브러리<br>• 빠른 빌드 속도(Vite)<br>• 타입 안정성(TS) |
| **컨테이너** | Docker + Docker Compose | • 일관된 배포 환경<br>• 쉬운 유지보수<br>• 버전 관리 용이 |
| **데이터 보존** | Volume Bind Mount | • 컨테이너 재시작 시 데이터 유지<br>• 호스트 파일시스템 백업 가능 |

### 1.3 추가 라이브러리 및 도구

**API 서버**:
- `sqlalchemy` - ORM (MySQL 연동)
- `pymysql` - MySQL 드라이버
- `pydantic` - 데이터 검증
- `uvicorn` - ASGI 서버
- `python-multipart` - 파일 업로드
- `python-jose` - JWT 인증
- `passlib` - 비밀번호 해싱

**프론트엔드**:
- `@tanstack/react-query` - 서버 상태 관리
- `zustand` - 클라이언트 상태 관리
- `react-router-dom` - 라우팅
- `axios` - HTTP 클라이언트
- `antd` (Ant Design) - UI 컴포넌트
  - antd 대신 tailwindcss 사용 (다른 라이브러리도 고려중)
- `recharts` - 차트 라이브러리
- `socket.io-client` - 실시간 통신 (WebSocket)
- `dayjs` - 날짜 처리

**임베디드 (C/C++)**:
- `libcurl` - HTTP 클라이언트
- `json-c` - JSON 파싱
- `WiringPi` - GPIO 제어 (부저, LED)
- `pthread` - 멀티스레딩

---

## 2. 프로젝트 구조

### 2.1 디렉토리 구조

```
Ajin_Pbl/
├── docker-compose.yml          # 전체 시스템 오케스트레이션
├── .env                         # 환경 변수 (DB 비밀번호 등)
│
├── embedded/                    # 임베디드 시스템 (C/C++)
│   ├── Dockerfile
│   ├── CMakeLists.txt
│   ├── src/
│   │   ├── main.c
│   │   ├── rfid_reader.c       # RFID 리더기 제어
│   │   ├── api_client.c        # API 서버 통신
│   │   ├── feedback.c          # 부저/LED 제어
│   │   ├── queue.c             # 로컬 큐잉
│   │   └── config.c            # 설정 파일 로드
│   ├── include/
│   │   ├── rfid_reader.h
│   │   ├── api_client.h
│   │   ├── feedback.h
│   │   ├── queue.h
│   │   └── config.h
│   ├── config/
│   │   └── config.json         # 리더기 설정
│   └── logs/
│
├── api/                         # FastAPI 서버
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # 설정 관리
│   │   ├── database.py          # DB 연결
│   │   ├── models/              # SQLAlchemy 모델
│   │   │   ├── __init__.py
│   │   │   ├── material.py
│   │   │   ├── part.py
│   │   │   ├── process.py
│   │   │   ├── lot.py
│   │   │   ├── assembly.py
│   │   │   ├── pallet.py
│   │   │   └── rfid.py
│   │   ├── schemas/             # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   ├── rfid.py
│   │   │   ├── pallet.py
│   │   │   └── trace.py
│   │   ├── routers/             # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── rfid.py          # RFID 스캔 처리
│   │   │   ├── materials.py
│   │   │   ├── parts.py
│   │   │   ├── processes.py
│   │   │   ├── lots.py
│   │   │   ├── pallets.py
│   │   │   └── trace.py         # 추적성 조회
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── rfid_service.py  # 스캔 이벤트 처리
│   │   │   ├── state_machine.py # 팔레트 상태 전이
│   │   │   ├── validation.py    # FIFO, 오투입, 완제품 검증
│   │   │   └── trace_service.py # 추적성 로직
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py
│   └── tests/
│       ├── test_rfid.py
│       ├── test_validation.py
│       └── test_trace.py
│
├── frontend/                    # React 애플리케이션
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx             # 엔트리포인트
│   │   ├── App.tsx
│   │   ├── api/                 # API 클라이언트
│   │   │   ├── client.ts        # Axios 인스턴스
│   │   │   ├── rfid.ts
│   │   │   ├── pallets.ts
│   │   │   ├── lots.ts
│   │   │   └── trace.ts
│   │   ├── components/          # 재사용 컴포넌트
│   │   │   ├── Layout/
│   │   │   ├── PalletCard/
│   │   │   ├── ProcessFlow/
│   │   │   └── TraceTree/
│   │   ├── pages/               # 페이지 컴포넌트
│   │   │   ├── Dashboard/
│   │   │   ├── ProcessMapping/
│   │   │   ├── MasterData/
│   │   │   ├── Monitoring/
│   │   │   ├── Traceability/
│   │   │   └── Inventory/
│   │   ├── hooks/               # 커스텀 훅
│   │   │   ├── useWebSocket.ts
│   │   │   ├── usePallets.ts
│   │   │   └── useTrace.ts
│   │   ├── store/               # Zustand 스토어
│   │   │   ├── authStore.ts
│   │   │   └── realtimeStore.ts
│   │   ├── types/               # TypeScript 타입
│   │   │   ├── pallet.ts
│   │   │   ├── lot.ts
│   │   │   └── trace.ts
│   │   └── utils/
│   │       ├── constants.ts
│   │       └── helpers.ts
│   └── public/
│
├── database/                    # 데이터베이스 관련
│   ├── init/
│   │   └── 01-schema.sql       # 초기 스키마 생성
│   └── migrations/              # 마이그레이션 스크립트
│
├── data/                        # 데이터 파이프라인 (호스트 볼륨)
│   ├── mysql/                   # MySQL 데이터 디렉토리
│   └── backups/                 # 백업 디렉토리
│
└── docs/                        # 문서
    ├── embedded-system-spec.md
    ├── api-server-spec.md
    └── web-app-spec.md
```

---

## 3. Docker 구성

### 3.1 docker-compose.yml

```yaml
version: '3.8'

services:
  # MySQL 데이터베이스
  db:
    image: mysql:8.0
    container_name: ajin-db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      TZ: Asia/Seoul
    ports:
      - "3306:3306"
    volumes:
      # 호스트 볼륨 마운트 (데이터 보존)
      - ./data/mysql:/var/lib/mysql
      # 초기 스키마 로드
      - ./database/init:/docker-entrypoint-initdb.d
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    networks:
      - ajin-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI 서버
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: ajin-api
    restart: always
    environment:
      DATABASE_URL: mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@db:3306/${MYSQL_DATABASE}
      API_SECRET_KEY: ${API_SECRET_KEY}
      TZ: Asia/Seoul
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
      - ./logs/api:/app/logs
    depends_on:
      db:
        condition: service_healthy
    networks:
      - ajin-network
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # React 프론트엔드
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ajin-frontend
    restart: always
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api
    networks:
      - ajin-network
    command: npm run dev -- --host

  # 임베디드 시스템 (Raspberry Pi에서 직접 실행)
  # Docker Compose에서는 제외 (하드웨어 접근 필요)

networks:
  ajin-network:
    driver: bridge

volumes:
  mysql-data:
    driver: local
```

### 3.2 .env 파일

```bash
# MySQL 설정
MYSQL_ROOT_PASSWORD=ajin_root_2025
MYSQL_DATABASE=ajin_rfid
MYSQL_USER=ajin_user
MYSQL_PASSWORD=ajin_pass_2025

# API 설정
API_SECRET_KEY=your-secret-key-here-change-in-production

# 프론트엔드 설정
VITE_API_URL=http://localhost:8000
```

### 3.3 데이터 파이프라인 전략

**데이터 보존 방법**:
1. **볼륨 바인드 마운트**: `./data/mysql:/var/lib/mysql`
   - Docker 컨테이너 삭제/재생성 시에도 데이터 유지
   - 호스트 파일시스템에 직접 저장

2. **백업 전략**:
   - 일일 자동 백업: `mysqldump`를 cron job으로 실행
   - 백업 위치: `./data/backups/`
   - 보관 기간: 최소 30일

3. **복구 절차**:
   ```bash
   # 백업 생성
   docker exec ajin-db mysqldump -u root -p ajin_rfid > ./data/backups/ajin_rfid_$(date +%Y%m%d).sql
   
   # 복구
   docker exec -i ajin-db mysql -u root -p ajin_rfid < ./data/backups/ajin_rfid_20251117.sql
   ```

---

## 4. 컴포넌트별 구현 계획

### 4.1 임베디드 시스템 (C/C++)

#### 4.1.1 Dockerfile

```dockerfile
# Raspberry Pi용 (ARM 아키텍처)
FROM arm32v7/debian:bullseye-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libcurl4-openssl-dev \
    libjson-c-dev \
    wiringpi \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 소스 복사
COPY . .

# 빌드
RUN mkdir build && cd build && \
    cmake .. && \
    make

# 실행
CMD ["./build/rfid_embedded"]
```

#### 4.1.2 주요 구현 파일

**main.c**:
```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <signal.h>
#include "rfid_reader.h"
#include "api_client.h"
#include "feedback.h"
#include "queue.h"
#include "config.h"

volatile sig_atomic_t keep_running = 1;

void signal_handler(int signum) {
    keep_running = 0;
}

int main(int argc, char *argv[]) {
    // 설정 로드
    config_t config;
    if (load_config("config/config.json", &config) != 0) {
        fprintf(stderr, "Failed to load config\n");
        return 1;
    }
    
    // 시그널 핸들러 등록
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // RFID 리더기 초기화
    rfid_reader_t *reader = rfid_reader_init(&config.rfid_reader);
    if (!reader) {
        fprintf(stderr, "Failed to initialize RFID reader\n");
        return 1;
    }
    
    // API 클라이언트 초기화
    api_client_t *api_client = api_client_init(&config.api_server);
    if (!api_client) {
        fprintf(stderr, "Failed to initialize API client\n");
        return 1;
    }
    
    // 피드백 컨트롤러 초기화
    feedback_t *feedback = feedback_init(&config.feedback);
    
    // 큐 초기화
    queue_t *queue = queue_init(config.queue.max_size);
    
    // 메인 루프
    printf("RFID Embedded System started\n");
    
    while (keep_running) {
        // RFID 스캔 폴링 (100ms 주기)
        scan_event_t event;
        if (rfid_reader_poll(reader, &event) == 0) {
            // 스캔 이벤트 발생
            printf("Tag scanned: %s\n", event.epc);
            
            // API 서버로 전송 시도
            api_response_t response;
            if (api_client_send_scan(api_client, &event, &response) == 0) {
                // 성공: 피드백 실행
                feedback_execute(feedback, &response.feedback);
            } else {
                // 실패: 큐에 저장
                printf("API server unavailable, queueing event\n");
                queue_enqueue(queue, &event);
            }
        }
        
        // 큐 플러시 시도 (5초마다)
        static time_t last_flush = 0;
        time_t now = time(NULL);
        if (now - last_flush >= 5) {
            queue_flush(queue, api_client, feedback);
            last_flush = now;
        }
        
        // Heartbeat 전송 (30초마다)
        static time_t last_heartbeat = 0;
        if (now - last_heartbeat >= 30) {
            api_client_send_heartbeat(api_client, reader);
            last_heartbeat = now;
        }
    }
    
    // 정리
    printf("Shutting down...\n");
    rfid_reader_destroy(reader);
    api_client_destroy(api_client);
    feedback_destroy(feedback);
    queue_destroy(queue);
    
    return 0;
}
```

**config.json**:
```json
{
  "api_server": {
    "base_url": "http://192.168.1.100:8000",
    "timeout": 3
  },
  "rfid_reader": {
    "port_name": "COM3",
    "baud_rate": 115200,
    "model": "CAEN R4300P",
    "antennas": [1, 2]
  },
  "queue": {
    "max_size": 1000
  },
  "feedback": {
    "buzzer_gpio": 17,
    "led_gpio_green": 22,
    "led_gpio_yellow": 27,
    "led_gpio_red": 23
  }
}
```

#### 4.1.3 Raspberry Pi 배포

**설치 스크립트** (install.sh):
```bash
#!/bin/bash

# 시스템 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# 필수 패키지 설치
sudo apt-get install -y build-essential cmake libcurl4-openssl-dev libjson-c-dev wiringpi

# 프로젝트 디렉토리 생성
mkdir -p /opt/ajin-rfid
cd /opt/ajin-rfid

# 소스 복사 (여기서는 git clone 또는 scp)
# git clone ...

# 빌드
mkdir build
cd build
cmake ..
make

# Systemd 서비스 등록
sudo cp ../scripts/ajin-rfid.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ajin-rfid
sudo systemctl start ajin-rfid

echo "Installation complete"
```

**Systemd 서비스** (ajin-rfid.service):
```ini
[Unit]
Description=AJIN RFID Embedded System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/ajin-rfid
ExecStart=/opt/ajin-rfid/build/rfid_embedded
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### 4.2 API 서버 (FastAPI)

#### 4.2.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4.2.2 requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-socketio==5.10.0
alembic==1.12.1
```

#### 4.2.3 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import rfid, materials, parts, processes, lots, pallets, trace
from app.config import settings

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AJIN RFID Tracking API",
    description="RFID 기반 물류 추적 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(rfid.router, prefix="/api/v1/rfid", tags=["RFID"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["Materials"])
app.include_router(parts.router, prefix="/api/v1/parts", tags=["Parts"])
app.include_router(processes.router, prefix="/api/v1/processes", tags=["Processes"])
app.include_router(lots.router, prefix="/api/v1/lots", tags=["Lots"])
app.include_router(pallets.router, prefix="/api/v1/pallets", tags=["Pallets"])
app.include_router(trace.router, prefix="/api/v1/trace", tags=["Traceability"])

@app.get("/")
async def root():
    return {"message": "AJIN RFID Tracking API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### 4.2.4 핵심 서비스 구현

**app/services/rfid_service.py**:
```python
from sqlalchemy.orm import Session
from app.models.pallet import Pallet
from app.models.rfid import RFIDReaderLocation, PalletHistory
from app.services.state_machine import StateMachine
from app.services.validation import ValidationService
from app.schemas.rfid import ScanEvent, ScanResponse, Feedback
from datetime import datetime

class RFIDService:
    def __init__(self, db: Session):
        self.db = db
        self.state_machine = StateMachine()
        self.validator = ValidationService(db)
    
    def process_scan(self, event: ScanEvent) -> ScanResponse:
        # 1. 포트로 공정/위치 조회
        location = self.db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.port_name == event.port_name
        ).first()
        
        if not location:
            raise ValueError(f"Unknown port: {event.port_name}")
        
        # 2. EPC로 팔레트 조회
        pallet = self.db.query(Pallet).filter(
            Pallet.rfid_epc == event.epc
        ).first()
        
        if not pallet:
            raise ValueError(f"Pallet not found: {event.epc}")
        
        # 3. 상태 전이 결정
        previous_status = pallet.status
        next_status = self.state_machine.get_next_state(
            current_status=previous_status,
            process_code=location.process.process_code,
            location_type=location.location_type
        )
        
        # 4. 검증 로직 실행
        validation_result = self.validator.validate_transition(
            pallet=pallet,
            next_status=next_status,
            location=location
        )
        
        if not validation_result.is_valid:
            # 오투입 차단
            return ScanResponse(
                success=False,
                error={
                    "type": validation_result.error_type,
                    "message": validation_result.message
                },
                feedback=Feedback(
                    pattern="ERROR",
                    count=3,
                    led_color="RED"
                )
            )
        
        # 5. 트랜잭션 처리
        try:
            # 상태 업데이트
            pallet.status = next_status
            pallet.current_process_id = location.process_id
            pallet.updated_at = datetime.utcnow()
            
            # 이력 기록
            history = PalletHistory(
                pallet_id=pallet.id,
                previous_status=previous_status,
                new_status=next_status,
                process_id=location.process_id,
                location_type=location.location_type,
                reader_location_id=location.id,
                scan_time=event.scan_time,
                notes=validation_result.warning_message if validation_result.has_warning else None
            )
            self.db.add(history)
            
            # 조립품 구성 요소 기록 (필요 시)
            if next_status == "Finished" and pallet.assembly_lot_id:
                self._record_assembly_components(pallet)
            
            self.db.commit()
            
            # 6. 피드백 생성
            feedback_pattern = "SUCCESS"
            if validation_result.has_warning:
                feedback_pattern = "WARNING"
            
            return ScanResponse(
                success=True,
                pallet={
                    "pallet_no": pallet.pallet_no,
                    "previous_status": previous_status,
                    "current_status": next_status,
                    "lot_no": pallet.lot.lot_no if pallet.lot else None,
                    "part_number": pallet.lot.part.part_number if pallet.lot else None
                },
                warning=validation_result.warning_message if validation_result.has_warning else None,
                feedback=Feedback(
                    pattern=feedback_pattern,
                    count=1 if feedback_pattern == "SUCCESS" else 3,
                    led_color="GREEN" if feedback_pattern == "SUCCESS" else "YELLOW"
                )
            )
        
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _record_assembly_components(self, pallet: Pallet):
        # 조립품 구성 요소 자동 기록 로직
        # 최근 Consuming 상태였던 팔레트들을 구성 요소로 기록
        pass
```

**app/services/state_machine.py**:
```python
class StateMachine:
    """팔레트 상태 전이 규칙"""
    
    # 상태 전이 테이블
    TRANSITIONS = {
        # 샤링 OUT (특수 케이스)
        ("Empty", "SHEARING", "OUT"): "Empty",  # 첫 태깅: 매칭 확인
        ("Empty", "SHEARING", "OUT"): "Stock",   # 재태깅: 적재 완료
        
        # 중간품 IN (소비)
        ("Stock", None, "IN"): "Consuming",      # 첫 태깅: 투입
        ("Consuming", None, "IN"): "Deregistered", # 재태깅: 소비 완료
        
        # 중간품 OUT (생산)
        ("Empty", None, "OUT"): "Producing",     # 첫 태깅: 적재 시작
        ("Producing", None, "OUT"): "Stock",     # 재태깅: 적재 완료
        
        # 완제품 OUT (조립)
        ("Producing", "ASSEMBLY", "OUT"): "Finished",  # 재태깅: 완제품
        
        # RETURN (출하)
        ("Finished", None, "RETURN"): "Deregistered",
        
        # 불량/보류
        (None, None, "DEFECT"): "Defect",
        (None, None, "HOLD"): "Hold",
    }
    
    def get_next_state(self, current_status: str, process_code: str, location_type: str) -> str:
        """다음 상태 결정"""
        key = (current_status, process_code, location_type)
        
        # 정확한 키 매치
        if key in self.TRANSITIONS:
            return self.TRANSITIONS[key]
        
        # 공정 무관 매치 (None 와일드카드)
        wildcard_key = (current_status, None, location_type)
        if wildcard_key in self.TRANSITIONS:
            return self.TRANSITIONS[wildcard_key]
        
        raise ValueError(f"Invalid transition: {key}")
```

---

### 4.3 프론트엔드 (React + Vite)

#### 4.3.1 Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm install

# 소스 복사
COPY . .

# 개발 서버 실행 (프로덕션에서는 빌드 후 nginx)
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

#### 4.3.2 package.json

```json
{
  "name": "ajin-rfid-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.8.4",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "socket.io-client": "^4.6.0",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
```

#### 4.3.3 주요 컴포넌트 구현

**src/api/client.ts**:
```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (인증 토큰 추가)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 인증 만료 처리
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**src/hooks/useWebSocket.ts**:
```typescript
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useWebSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(WS_URL, {
      transports: ['websocket'],
    });

    socketInstance.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return { socket, isConnected };
}
```

**src/pages/Monitoring/MonitoringPage.tsx**:
```typescript
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Tabs } from 'antd';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { Pallet, ScanEvent } from '../../types';

export function MonitoringPage() {
  const { socket, isConnected } = useWebSocket();
  const [pallets, setPallets] = useState<Pallet[]>([]);
  const [recentEvents, setRecentEvents] = useState<ScanEvent[]>([]);

  useEffect(() => {
    if (!socket) return;

    // 팔레트 상태 업데이트 수신
    socket.on('pallet_updated', (pallet: Pallet) => {
      setPallets((prev) =>
        prev.map((p) => (p.id === pallet.id ? pallet : p))
      );
    });

    // 스캔 이벤트 수신
    socket.on('scan_event', (event: ScanEvent) => {
      setRecentEvents((prev) => [event, ...prev].slice(0, 20));
    });

    return () => {
      socket.off('pallet_updated');
      socket.off('scan_event');
    };
  }, [socket]);

  const columns = [
    {
      title: '팔레트',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
    },
    {
      title: 'LOT',
      dataIndex: ['lot', 'lot_no'],
      key: 'lot_no',
    },
    {
      title: '품번',
      dataIndex: ['lot', 'part', 'part_number'],
      key: 'part_number',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = {
          Stock: 'green',
          Consuming: 'orange',
          Producing: 'blue',
          Finished: 'purple',
        }[status];
        return <Tag color={color}>{status}</Tag>;
      },
    },
  ];

  return (
    <div>
      <h1>실시간 모니터링</h1>
      <Card
        title="연결 상태"
        extra={<Tag color={isConnected ? 'green' : 'red'}>{isConnected ? '연결됨' : '연결 끊김'}</Tag>}
      >
        <Tabs
          items={[
            {
              key: 'pallets',
              label: '팔레트 현황',
              children: <Table dataSource={pallets} columns={columns} rowKey="id" />,
            },
            {
              key: 'events',
              label: '최근 이벤트',
              children: (
                <div>
                  {recentEvents.map((event, i) => (
                    <div key={i}>
                      {event.scan_time} - {event.pallet_no} - {event.status}
                    </div>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
```

---

## 5. 데이터베이스 초기화

### 5.1 database/init/01-schema.sql

```sql
-- temp/DB/Ajin_DB.sql 파일을 여기에 복사
-- Docker 컨테이너 최초 실행 시 자동으로 실행됨

CREATE DATABASE IF NOT EXISTS ajin_rfid CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ajin_rfid;

-- 원자재 테이블
CREATE TABLE raw_materials (
  id INT PRIMARY KEY AUTO_INCREMENT,
  coil_number VARCHAR(50) UNIQUE NOT NULL COMMENT '코일 번호 (추적 키)',
  material_name VARCHAR(100) NOT NULL COMMENT '재질명',
  supplier VARCHAR(100) COMMENT '공급업체',
  receipt_date DATE COMMENT '입고일자',
  qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_coil_number (coil_number)
) COMMENT '원자재(코일) 마스터';

-- ... (나머지 테이블은 temp/DB/Ajin_DB.sql 참조)
```

---

## 6. 개발 워크플로우

### 6.1 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd Ajin_Pbl

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (비밀번호 등)

# 3. 데이터 디렉토리 생성
mkdir -p data/mysql data/backups

# 4. Docker Compose 실행
docker-compose up -d

# 5. 로그 확인
docker-compose logs -f

# 6. 접속 확인
# - API: http://localhost:8000/docs (Swagger UI)
# - Frontend: http://localhost:5173
# - DB: localhost:3306 (MySQL Workbench 등)
```

### 6.2 개발 사이클

```bash
# API 개발 시
cd api
# 코드 수정
docker-compose restart api
docker-compose logs -f api

# Frontend 개발 시
cd frontend
# 코드 수정 (Hot Reload 자동)
# 브라우저에서 http://localhost:5173 확인

# DB 스키마 변경 시
docker exec -i ajin-db mysql -u root -p ajin_rfid < database/migrations/002-add-column.sql
```

### 6.3 테스트

```bash
# API 테스트
cd api
pytest tests/

# Frontend 테스트 (선택 사항)
cd frontend
npm run test
```

---

## 7. 배포 계획

### 7.1 프로덕션 배포

**프로덕션 docker-compose.yml**:
```yaml
version: '3.8'

services:
  db:
    # ... (동일)
    
  api:
    # ... (기본 동일)
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4  # 프로덕션 설정
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod  # 프로덕션 Dockerfile
    ports:
      - "80:80"
    # nginx로 빌드된 정적 파일 서빙
```

**frontend/Dockerfile.prod**:
```dockerfile
# 빌드 스테이지
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 프로덕션 스테이지
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 7.2 백업 자동화

**backup.sh**:
```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ajin-rfid/data/backups"
DB_NAME="ajin_rfid"

# MySQL 백업
docker exec ajin-db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${DB_NAME} > ${BACKUP_DIR}/ajin_rfid_${DATE}.sql

# 30일 이상 된 백업 삭제
find ${BACKUP_DIR} -name "*.sql" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}/ajin_rfid_${DATE}.sql"
```

**Cron job 등록**:
```bash
# 매일 새벽 3시 백업
0 3 * * * /opt/ajin-rfid/scripts/backup.sh >> /var/log/ajin-backup.log 2>&1
```

---

## 8. Phase별 구현 순서

### Phase 1: MVP (4주)

**Week 1-2: 인프라 및 기본 구조**
- [ ] Docker Compose 환경 구축
- [ ] MySQL 스키마 생성 및 초기 데이터
- [ ] FastAPI 기본 구조 (라우터, 모델)
- [ ] React 기본 구조 (라우팅, 레이아웃)

**Week 3-4: 핵심 RFID 기능**
- [ ] 임베디드: RFID 스캔 → API 전송
- [ ] API: 스캔 처리, 상태 전이, 기본 검증
- [ ] 웹: 팔레트 등록, 리더기 매핑, 기본 모니터링

**검증**: 샤링 → 프레스 단일 공정 흐름 동작

### Phase 2: 추적성 및 검증 (3주)

**Week 5-6: 검증 로직**
- [ ] FIFO 검증
- [ ] 오투입 검증
- [ ] 완제품 검증

**Week 7: 추적성**
- [ ] 정방향 추적 (코일 → 제품)
- [ ] 역방향 추적 (제품 → 코일)
- [ ] 드릴다운 UI

**검증**: 전체 공정 추적 확인

### Phase 3: 실시간 및 최적화 (2주)

**Week 8: 실시간 통신**
- [ ] WebSocket 구현
- [ ] 실시간 모니터링 화면

**Week 9: 최적화**
- [ ] DB 인덱싱
- [ ] API 성능 최적화
- [ ] 프론트엔드 최적화

**검증**: 성능 테스트 (동시 50명, 초당 10개 스캔)

### Phase 4: 운영 및 확장 (2주)

**Week 10: 운영 기능**
- [ ] 권한 관리
- [ ] 감사 로그
- [ ] 백업 자동화

**Week 11: 안정화**
- [ ] 버그 수정
- [ ] 문서화
- [ ] 사용자 교육 자료

**검증**: 24시간 무정지 운영 테스트

---

## 9. 추가 고려사항

### 9.1 보안

- **API 인증**: JWT 기반
- **DB 비밀번호**: 환경 변수로 관리 (절대 Git 커밋 금지)
- **HTTPS**: 프로덕션에서 Let's Encrypt + nginx 리버스 프록시
- **CORS**: 프로덕션에서 특정 도메인만 허용

### 9.2 모니터링

- **로그 수집**: Docker 로그 → 파일 저장 → 분석
- **알림**: 장애 발생 시 이메일/SMS (선택 사항)
- **헬스체크**: `/health` 엔드포인트로 서비스 상태 확인

### 9.3 확장성

- **수평 확장**: API 서버 복제 (로드 밸런서 필요)
- **DB 레플리카**: 읽기 성능 향상 (필요 시)
- **캐싱**: Redis 도입 (필요 시)

---

## 10. 체크리스트

### 개발 시작 전
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] Git 저장소 생성
- [ ] `.env` 파일 생성 및 비밀번호 설정
- [ ] 팀 개발 환경 통일 (IDE, 코딩 컨벤션)

### MVP 완료 기준
- [ ] RFID 스캔 → API → 상태 전이 동작
- [ ] 웹에서 팔레트 등록 및 상태 확인 가능
- [ ] 샤링 → 프레스 흐름 정상 동작
- [ ] Docker Compose로 전체 시스템 실행 가능

### 프로덕션 배포 전
- [ ] 모든 테스트 통과
- [ ] 성능 테스트 통과 (동시 50명, 초당 10개 스캔)
- [ ] 보안 검토 (비밀번호, HTTPS)
- [ ] 백업 자동화 설정
- [ ] 사용자 교육 자료 준비
- [ ] 롤백 계획 수립

---

## 11. 관련 문서

- **명세서**: `.specify/specs/rfid-logistics-tracking-system.md`
- **임베디드 상세**: `docs/embedded-system-spec.md`
- **API 상세**: `docs/api-server-spec.md`
- **웹 상세**: `docs/web-app-spec.md`
- **DB 스키마**: `temp/DB/Ajin_DB.sql`
- **헌법**: `.specify/memory/constitution.md`

---

## 문서 이력
- v1.0.0 (2025-11-17): 초안 작성 - 기술 스택 선정 및 구현 계획 수립
