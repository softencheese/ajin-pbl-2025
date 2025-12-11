# 시스템 설계 가이드

## 개요
AJIN RFID 물류 추적 시스템의 아키텍처 설계 원칙과 주요 설계 결정 사항을 설명합니다.

---

## 1. 전체 아키텍처

### 1.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Floor                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ RFID     │  │ RFID     │  │ RFID     │  │ RFID     │     │
│  │ Reader 1 │  │ Reader 2 │  │ Reader 3 │  │ Reader N │     │
│  │ (샤링)    │  │ (프레스)  │  │ (조립)    │  │ (출하)    │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │ RS-232 / TCP/IP
                      ↓
        ┌─────────────────────────────┐
        │   Raspberry Pi (Embedded)   │
        │   - RFID Interface          │
        │   - API Client              │
        │   - Feedback Control        │
        │   - Local Queue             │
        └──────────────┬──────────────┘
                       │ HTTP/REST
                       ↓
        ┌─────────────────────────────┐
        │      FastAPI Server         │
        │   - Business Logic          │
        │   - State Machine           │
        │   - Validation              │
        │   - WebSocket               │
        └──────────────┬──────────────┘
                       │
              ┌────────┴────────┐
              │                 │
              ↓                 ↓
      ┌──────────────┐   ┌─────────────┐
      │   MySQL 8.0  │   │   React     │
      │   (Volume)   │   │   (Vite)    │
      └──────────────┘   └─────────────┘
```

### 1.2 레이어 아키텍처

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  React Frontend
│  - UI Components                    │  - User Interactions
│  - Real-time Updates (WebSocket)    │  - Data Visualization
└─────────────────────────────────────┘
             ↕ HTTP/REST
┌─────────────────────────────────────┐
│      Application Layer              │  FastAPI Backend
│  - Business Logic                   │  - State Management
│  - Validation                       │  - Traceability Queries
│  - State Machine                    │
└─────────────────────────────────────┘
             ↕ ORM
┌─────────────────────────────────────┐
│      Data Layer                     │  MySQL Database
│  - Persistent Storage               │  - Transactional Data
│  - Traceability Views               │  - Relational Integrity
└─────────────────────────────────────┘
```

---

## 2. 핵심 설계 원칙

### 2.1 데이터 무결성 (Data Integrity)

**원칙**: 추적성을 위한 데이터는 절대 삭제하지 않는다.

**적용**:
- `coil_number`, `lot_no`, `pallet_no`: 추적 키로 절대 삭제/재사용 금지
- `pallet_histories`: 불변 로그, 절대 삭제 금지
- Soft Delete: `is_active`, `deregistered_at` 필드 사용

```sql
-- ❌ 잘못된 예
DELETE FROM lots WHERE id = 123;

-- ✅ 올바른 예
UPDATE pallets SET status = 'Deregistered', deregistered_at = NOW() WHERE id = 123;
```

### 2.2 단일 진실의 원천 (Single Source of Truth)

**원칙**: 포트 정보만으로 공정과 위치를 자동 판별한다.

**적용**:
```python
# 포트 → 공정/위치 자동 매핑
port_name = "COM3"
location = db.query(RFIDReaderLocation).filter_by(port_name=port_name).first()
# → process_id, location_type 자동 결정
```

**이점**:
- 임베디드 시스템은 포트만 전송
- 공정 추가/변경 시 DB 설정만 수정
- 코드 변경 불필요

### 2.3 상태 기계 (State Machine)

**원칙**: 팔레트 상태 전이는 명확한 규칙을 따른다.

**적용**:
```python
class StateMachine:
    TRANSITIONS = {
        ("Stock", "IN"): "Consuming",
        ("Consuming", "IN"): "Deregistered",
        ("Empty", "OUT"): "Producing",
        ("Producing", "OUT"): "Stock",
    }
```

**참고**: `docs/database/pallet-state-machine.md`

### 2.4 장애 복구 (Fault Tolerance)

**원칙**: 네트워크 장애 시에도 데이터 손실 없음.

**적용**:
- 임베디드 시스템: 로컬 큐잉 (최대 1000개)
- 원래 타임스탬프 유지
- 연결 복구 시 자동 재전송

```c
// 큐에 저장
queue_enqueue(epc, port_name, original_timestamp);

// 복구 후 재전송
queue_flush();  // 원래 타임스탬프로 전송
```

### 2.5 확장성 (Scalability)

**원칙**: 공정/리더기 추가 시 코드 변경 없이 설정만으로 가능.

**적용**:
- 리더기 추가: DB에 레코드 추가만
- 공정 추가: `processes` 테이블에 추가
- 상태 전이 규칙: DB 기반으로 변경 가능 (미래 고려)

---

## 3. 주요 설계 결정

### 3.1 리더기는 고정, 팔레트는 이동

**잘못된 이해**:
```
팔레트가 IN 리더기 → 공정 내부 → OUT 리더기로 이동
```

**올바른 이해**:
```
IN 리더기 (고정):
  - 소비용 팔레트 첫 태깅: Stock → Consuming (투입)
  - 소비용 팔레트 재태깅: Consuming → Deregistered (완료)

OUT 리더기 (고정):
  - 생산용 팔레트 첫 태깅: Empty → Producing (시작)
  - 생산용 팔레트 재태깅: Producing → Stock (완료)
```

**설계 결과**:
- 각 리더기는 특정 역할 수행
- 같은 리더기를 2회 태깅 (시작, 완료)
- 상태 전이 규칙 단순화

### 3.2 검증 레벨 구분

**차단 (Blocking)**:
- 오투입 (Wrong Part): 품번 불일치
- 완제품 검증: `is_final_product = FALSE`인데 Finished 전환

**경고 (Warning)**:
- FIFO 위반: 더 오래된 재고 존재
- 무시하고 진행 가능

**구현**:
```python
if validation_result.is_error:
    return {"success": False, "error": {...}}  # 차단
elif validation_result.is_warning:
    # 경고 + 정상 진행
    proceed_with_warning()
```

### 3.3 추적성 전략

**정방향 (Forward)**:
```
raw_materials.coil_number
  → lots.material_id
  → assembly_components.component_lot_id
  → assembly_lots.id
```

**역방향 (Backward)**:
```
assembly_lots.id
  → assembly_components.assembly_lot_id
  → lots.id
  → raw_materials.id (coil_number)
```

**View 사용**:
- 복잡한 JOIN을 뷰로 추상화
- 애플리케이션 코드 단순화

### 3.4 실시간 업데이트

**WebSocket vs Polling**:
- 선택: WebSocket
- 이유: 즉각적인 업데이트, 서버 부하 감소

**이벤트 타입**:
- `pallet_updated`: 팔레트 상태 변경
- `scan_event`: 스캔 이벤트 발생
- `reader_status`: 리더기 상태 변경

---

## 4. 데이터 모델 설계

### 4.1 팔레트 연결 전략

**문제**: 팔레트는 중간품 LOT 또는 조립품 LOT와 연결

**해결**:
```sql
CREATE TABLE pallets (
  lot_id INT,                     -- 중간품 LOT
  assembly_lot_id INT,            -- 조립품 LOT
  CHECK (
    (lot_id IS NOT NULL AND assembly_lot_id IS NULL) OR
    (lot_id IS NULL AND assembly_lot_id IS NOT NULL) OR
    (lot_id IS NULL AND assembly_lot_id IS NULL)
  )
);
```

**장점**:
- DB 레벨에서 무결성 보장
- 둘 중 하나만 연결 (XOR)

### 4.2 조립 깊이 (Assembly Level)

**문제**: 조립품이 다른 조립품을 포함할 수 있음 (재귀)

**해결**:
```sql
-- 트리거로 자동 계산
CREATE TRIGGER trg_calculate_assembly_level
AFTER INSERT ON assembly_components
FOR EACH ROW
BEGIN
  UPDATE assembly_lots
  SET assembly_level = (
    SELECT MAX(level) + 1
    FROM components
  )
  WHERE id = NEW.assembly_lot_id;
END;
```

**용도**:
- 추적 깊이 제한 (무한 루프 방지)
- BOM 계층 시각화

### 4.3 인덱스 전략

**원칙**: 자주 조회/조인되는 컬럼에 인덱스

**적용**:
```sql
-- 추적 키
CREATE UNIQUE INDEX idx_coil_number ON raw_materials(coil_number);
CREATE UNIQUE INDEX idx_lot_no ON lots(lot_no);
CREATE UNIQUE INDEX idx_pallet_no ON pallets(pallet_no);

-- 필터링
CREATE INDEX idx_status ON pallets(status);
CREATE INDEX idx_production_date ON lots(production_date);

-- 조인 최적화
CREATE INDEX idx_lot_id ON pallets(lot_id);
CREATE INDEX idx_material_id ON lots(material_id);

-- 복합 인덱스
CREATE INDEX idx_process_location ON rfid_reader_locations(process_id, location_type);
```

---

## 5. API 설계 원칙

### 5.1 RESTful 규칙

```
GET    /api/v1/pallets          # 목록 조회
GET    /api/v1/pallets/{id}     # 상세 조회
POST   /api/v1/pallets          # 생성
PUT    /api/v1/pallets/{id}     # 전체 수정
PATCH  /api/v1/pallets/{id}     # 부분 수정
DELETE /api/v1/pallets/{id}     # 삭제 (사용 금지)
```

### 5.2 응답 형식 통일

**성공**:
```json
{
  "success": true,
  "data": {...}
}
```

**실패**:
```json
{
  "success": false,
  "error": {
    "type": "ERROR_TYPE",
    "message": "에러 메시지",
    "details": {}
  }
}
```

### 5.3 피드백 명령 포함

RFID 스캔 API는 임베디드 시스템을 위한 피드백 명령을 포함:

```json
{
  "success": true,
  "pallet": {...},
  "feedback": {
    "pattern": "SUCCESS",
    "count": 1,
    "led_color": "GREEN"
  }
}
```

---

## 6. 보안 설계

### 6.1 인증 (Authentication)

- JWT 기반
- Access Token + Refresh Token
- 만료 시간: 1시간

### 6.2 권한 (Authorization)

- 역할 기반 (RBAC)
- 작업자: 읽기 전용
- 관리자: 쓰기 권한

### 6.3 데이터 보호

- 전송: HTTPS (프로덕션)
- 저장: 비밀번호 해싱 (bcrypt)
- 백업: 암호화 (선택 사항)

---

## 7. 성능 설계

### 7.1 목표

- RFID 스캔 → 피드백: 500ms 이내
- API 응답: 1초 이내
- 추적성 조회: 3초 이내
- 동시 접속: 50명 이상

### 7.2 최적화 전략

**데이터베이스**:
- 적절한 인덱스
- View 사용 (복잡한 JOIN)
- Connection Pooling

**API 서버**:
- 비동기 처리 (async/await)
- 캐싱 (Redis - 선택 사항)
- 쿼리 최적화

**프론트엔드**:
- 코드 스플리팅
- Lazy Loading
- WebSocket (Polling 대신)

---

## 8. 확장성 고려사항

### 8.1 수평 확장

**API 서버**:
- Stateless 설계
- 로드 밸런서 추가 가능

**데이터베이스**:
- 읽기 레플리카 (필요 시)
- 파티셔닝 (대용량 테이블)

### 8.2 기능 확장

**향후 추가 가능 기능**:
- ERP 연동
- 모바일 앱
- 고급 분석 (BI)
- AI 기반 예측

---

## 9. 운영 설계

### 9.1 모니터링

- 리더기 상태: Heartbeat (30초)
- API 서버: Health Check
- DB: Connection Pool 상태

### 9.2 백업 전략

- 일일 자동 백업
- 보관 기간: 30일
- 복구 테스트: 월 1회

### 9.3 로깅

**레벨**:
- DEBUG: 개발 환경
- INFO: 정상 동작
- WARNING: 주의 필요
- ERROR: 즉시 조치

**보관**:
- 파일 로테이션 (일별)
- 최소 6개월 보관

---

## 10. 설계 패턴

### 10.1 Repository Pattern

```python
class PalletRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: int) -> Pallet:
        return self.db.query(Pallet).filter_by(id=id).first()
    
    def get_all(self, filters: dict) -> List[Pallet]:
        query = self.db.query(Pallet)
        # 필터 적용
        return query.all()
```

### 10.2 Service Layer

```python
class RFIDService:
    def __init__(self, db: Session):
        self.pallet_repo = PalletRepository(db)
        self.state_machine = StateMachine()
    
    def process_scan(self, event: ScanEvent) -> ScanResponse:
        # 비즈니스 로직
        pass
```

### 10.3 Strategy Pattern (검증)

```python
class ValidationStrategy:
    def validate(self, pallet, location) -> ValidationResult:
        pass

class FIFOValidation(ValidationStrategy):
    def validate(self, pallet, location):
        # FIFO 검증 로직
        pass

class WrongPartValidation(ValidationStrategy):
    def validate(self, pallet, location):
        # 오투입 검증 로직
        pass
```

---

## 참고 문서

- 시스템 명세: `../docs/rfid-logistics-tracking-system.md`
- 구현 계획: `../docs/implementation-plan.md`
- DB 스키마: `../database/schema.md`
- 상태 기계: `../database/pallet-state-machine.md`
- API 엔드포인트: `../api/endpoints.md`
