# API 엔드포인트 명세서

## 개요
AJIN RFID 물류 추적 시스템의 모든 API 엔드포인트를 정의합니다.

**Base URL**: `http://localhost:8000/api/v1`

---

## 1. RFID 스캔 처리

### 1.1 스캔 이벤트 처리
**엔드포인트**: `POST /rfid/scan`

**설명**: RFID 리더기에서 태그를 스캔한 이벤트를 처리하고 팔레트 상태를 전이시킵니다.

**요청**:
```json
{
  "epc": "E2801170000002036B3D8CCD",
  "port_name": "COM3",
  "scan_time": "2025-11-17T09:23:45.123Z",
  "reader_info": {
    "model": "CAEN R4300P",
    "antenna": 1,
    "rssi": -45
  }
}
```

**응답 (성공)**:
```json
{
  "success": true,
  "pallet": {
    "pallet_no": "PLT-2025-001",
    "previous_status": "Stock",
    "current_status": "Consuming",
    "lot_number": "SH-231211-001",
    "item_code": "71412-T6000S"
  },
  "feedback": {
    "pattern": "SUCCESS",
    "count": 1,
    "led_color": "GREEN"
  }
}
```

**응답 (FIFO 경고)**:
```json
{
  "success": true,
  "warning": {
    "type": "FIFO_VIOLATION",
    "message": "더 오래된 재고가 있습니다",
    "oldest_stock": {
      "lot_number": "SH-231209-001",
      "days_old": 2
    }
  },
  "feedback": {
    "pattern": "WARNING",
    "count": 3,
    "led_color": "YELLOW"
  }
}
```

**응답 (오류 - 오투입)**:
```json
{
  "success": false,
  "error": {
    "type": "WRONG_PART",
    "message": "품번 불일치 - 투입 불가",
    "expected_item": "71412-T6000S",
    "actual_item": "76211-GI000"
  },
  "feedback": {
    "pattern": "ERROR",
    "count": 3,
    "led_color": "RED"
  }
}
```

### 1.2 리더기 상태 수신
**엔드포인트**: `POST /rfid/reader-status`

**설명**: 임베디드 시스템에서 리더기 상태를 주기적으로 전송합니다 (Heartbeat).

**요청**:
```json
{
  "port_name": "COM3",
  "status": "CONNECTED",
  "last_scan_time": "2025-11-17T09:23:45.123Z",
  "uptime_seconds": 3600,
  "total_scans": 1234,
  "error_count": 0
}
```

**응답**:
```json
{
  "success": true,
  "message": "Status updated"
}
```

---

## 2. 마스터 데이터 관리

### 2.1 품목 (Items) - 통합 품목 마스터

> **Note**: 기존 `원자재(materials)`와 `품번(parts)`이 `품목(items)`으로 통합되었습니다.

#### 목록 조회
- **GET** `/items`
- **Query Parameters**: 
  - `page`, `per_page`: 페이지네이션
  - `search`: 품목코드/품명 검색
  - `item_type`: `RAW` (원자재), `WIP` (재공품), `PRODUCT` (완제품) 필터

#### 상세 조회
- **GET** `/items/{id}`

#### 등록
- **POST** `/items`
```json
{
  "item_code": "STEEL-SPCC",
  "item_name": "SPCC 냉연강판",
  "item_type": "RAW",
  "unit": "EA",
  "spec": "1.2t x 1219mm",
  "vehicle_model": null,
  "default_supplier": "포스코"
}
```

**item_type 구분**:
- `RAW`: 원자재 (코일, 철판 등)
- `WIP`: 재공품/중간품 (샤링품, 프레스품 등)
- `PRODUCT`: 완제품 (조립 완료 제품)

#### 수정
- **PUT** `/items/{id}`

#### 삭제
- **DELETE** `/items/{id}` (사용 이력 없는 경우만)

---

### 2.2 공정 (Processes)

#### 목록 조회
- **GET** `/processes`

#### 등록
- **POST** `/processes`
```json
{
  "process_code": "SHEARING",
  "process_name": "샤링",
  "process_order": 1,
  "production_line": "400T"
}
```

#### 순서 변경
- **PUT** `/processes/{id}/order`
```json
{
  "new_order": 2
}
```

---

### 2.3 RFID 리더기 위치 (Reader Locations)

#### 목록 조회
- **GET** `/reader-locations`

#### 등록 (수동)
> **Note**: 일반적으로 리더기는 Heartbeat 수신 시 자동 등록됩니다.

- **POST** `/reader-locations`
```json
{
  "port_name": "READER_01",
  "process_id": 2,
  "location_type": "IN",
  "description": "프레스 1500T 투입구 리더기",
  "is_active": true
}
```

#### 수정
- **PUT** `/reader-locations/{id}`

---

### ~~2.4 RFID 태그 (RFID Tags)~~ - **삭제됨**

> **Note**: `rfid_tags` 테이블이 `pallets`에 통합되었습니다.  
> 태그 상태는 `pallets.tag_status` 필드로 관리합니다.

기존 RFID 태그 API 대신 **Pallets API**를 사용하세요:
- 태그 등록 → `POST /pallets` (rfid_epc 포함)
- 태그 상태 조회 → `GET /pallets/{id}` (tag_status 필드 확인)
- 태그 상태 변경 → `PUT /pallets/{id}/tag-status`

---

### 2.5 팔레트 (Pallets)

#### 목록 조회
- **GET** `/pallets`
- **Query Parameters**: `status`, `process_id`, `search`

#### 상세 조회
- **GET** `/pallets/{id}`

#### 생성
- **POST** `/pallets`
```json
{
  "pallet_no": "PLT-2025-001",
  "rfid_epc": "E2801170000002036B3D8CCD"
}
```

#### LOT 연결
- **PUT** `/pallets/{id}/link-lot`
```json
{
  "lot_id": 123
}
```

#### 상태 강제 변경 (관리자)
- **PUT** `/pallets/{id}/status`
```json
{
  "status": "Hold",
  "reason": "품질 검사 대기"
}
```

#### 태그 상태 변경
> **Note**: 기존 `/rfid-tags/{id}/status` 대체

- **PUT** `/pallets/{id}/tag-status`
```json
{
  "tag_status": "DAMAGED",
  "reason": "물리적 손상"
}
```

**tag_status 값**:
- `AVAILABLE`: 사용 가능
- `IN_USE`: 사용 중
- `DAMAGED`: 손상됨

---

## 3. LOT 관리 (통합)

> **Note**: 기존 `중간품 LOT`와 `조립품 LOT`가 하나의 `LOT` 테이블로 통합되었습니다.

### 3.1 LOT 목록 조회
- **GET** `/lots`
- **Query Parameters**: 
  - `item_id`: 품목 ID 필터
  - `item_type`: RAW, WIP, PRODUCT 필터
  - `process_id`: 공정 ID 필터
  - `status`: LOT 상태 필터 (WAIT, PROCESS, STOCK, CONSUMED, SHIPPED, HOLD, DEFECT)
  - `date_from`, `date_to`: 생산일 범위

### 3.2 LOT 상세 조회
- **GET** `/lots/{id}`

**응답**:
```json
{
  "id": 1,
  "lot_number": "IN-231211-001",
  "barcode": "251018226687",
  "item": {
    "id": 5,
    "item_code": "STEEL-SPCC",
    "item_name": "SPCC 냉연강판",
    "item_type": "RAW"
  },
  "quantity": 100,
  "initial_quantity": 100,
  "status": "STOCK",
  "production_date": "2023-12-11",
  "supplier": "포스코",
  "worker_name": "홍길동",
  "qc_passed": true
}
```

### 3.3 원자재 입고 (LOT 생성)
- **POST** `/lots/receiving`

**설명**: 원자재 입고 시 LOT 생성 (RFID 불필요, 수동 등록)

```json
{
  "item_id": 5,
  "quantity": 100,
  "production_date": "2023-12-11",
  "supplier": "포스코",
  "barcode": "251018226687",
  "notes": "비고"
}
```

**응답**:
```json
{
  "id": 1,
  "lot_number": "IN-231211-001",
  "barcode": "251018226687",
  "item_code": "STEEL-SPCC",
  "status": "STOCK"
}
```

### 3.4 생산 LOT 생성
- **POST** `/lots`

**설명**: 샤링, 프레스, 조립 등 생산 공정에서 새 LOT 생성 + 투입 LOT 연결

```json
{
  "item_id": 10,
  "process_id": 2,
  "quantity": 400,
  "production_date": "2023-12-11",
  "worker_name": "최영일",
  "input_lots": [
    {
      "lot_id": 1,
      "quantity_consumed": 100
    }
  ],
  "barcode": "SH-BARCODE-001"
}
```

**응답**:
```json
{
  "id": 2,
  "id": 2,
  "lot_number": "SH-231211-001",
  "barcode": "SH-BARCODE-001",
  "item_code": "71412-T6000S",
  "status": "STOCK",
  "genealogy": [
    {
      "input_lot_number": "IN-231211-001",
      "quantity_consumed": 100
    }
  ]
}
```

### 3.5 LOT 상태 변경
- **PUT** `/lots/{id}/status`
```json
{
  "status": "CONSUMED",
  "notes": "전량 소비"
}
```

---

## 4. LOT 족보 (Genealogy)

### 4.1 족보 조회 (특정 LOT)
- **GET** `/lot-genealogy/{lot_id}`

**응답**:
```json
{
  "lot": {
    "id": 2,
    "lot_number": "SH-231211-001",
    "item_code": "71412-T6000S"
  },
  "parents": [
    {
      "lot_number": "IN-231211-001",
      "item_code": "STEEL-SPCC",
      "item_type": "RAW",
      "quantity_consumed": 100
    }
  ],
  "children": [
    {
      "lot_number": "PR-231211-001",
      "item_code": "71412-T6000S-PR",
      "item_type": "WIP",
      "quantity_consumed": 400
    }
  ]
}
```

### 4.2 족보 수동 추가
- **POST** `/lot-genealogy`
```json
{
  "input_lot_id": 1,
  "output_lot_id": 2,
  "process_id": 2,
  "quantity_consumed": 100
}
```

---

## 5. 추적성 조회

### 5.1 정방향 추적 (원자재 → 완제품)
**엔드포인트**: `GET /trace/forward`

**Query Parameters**: `lot_number` 또는 `lot_id`

**응답**:
```json
{
  "root_lot": {
    "lot_number": "IN-231211-001",
    "item_code": "STEEL-SPCC",
    "item_type": "RAW"
  },
  "trace_path": [
    {
      "depth": 1,
      "lot_number": "SH-231211-001",
      "item_code": "71412-T6000S",
      "item_type": "WIP",
      "process_name": "샤링"
    },
    {
      "depth": 2,
      "lot_number": "PR-231211-001",
      "item_code": "71412-T6000S-PR",
      "item_type": "WIP",
      "process_name": "프레스"
    },
    {
      "depth": 3,
      "lot_number": "AS-231211-001",
      "item_code": "ASSY-DOOR",
      "item_type": "PRODUCT",
      "process_name": "조립"
    }
  ]
}
```

---

### 5.2 역방향 추적 (완제품 → 원자재)
**엔드포인트**: `GET /trace/backward`

**Query Parameters**: `lot_number` 또는 `lot_id`

**응답**:
```json
{
  "leaf_lot": {
    "lot_number": "AS-231211-001",
    "item_code": "ASSY-DOOR",
    "item_type": "PRODUCT"
  },
  "trace_path": [
    {
      "depth": 1,
      "lot_number": "PR-231211-001",
      "item_code": "71412-T6000S-PR",
      "item_type": "WIP"
    },
    {
      "depth": 2,
      "lot_number": "SH-231211-001",
      "item_code": "71412-T6000S",
      "item_type": "WIP"
    },
    {
      "depth": 3,
      "lot_number": "IN-231211-001",
      "item_code": "STEEL-SPCC",
      "item_type": "RAW"
    }
  ]
}
```

---

### 5.3 드릴다운 검색
**엔드포인트**: `GET /trace/search`

**Query Parameters**: `q` (품목코드, LOT번호, 팔레트 번호)

**응답**: 검색어 유형에 따라 정방향/역방향 통합 결과 반환

---

## 6. 모니터링 및 통계

### 6.1 대시보드 요약
- **GET** `/dashboard/summary`

**응답**:
```json
{
  "active_pallets": 125,
  "total_stock": 3450,
  "today_production": 890,
  "reader_status": {
    "connected": 12,
    "total": 13
  }
}
```

### 6.2 공정별 현황
- **GET** `/dashboard/process-status`

### 6.3 재고 현황 (FIFO 포함)
- **GET** `/inventory/stock`

**응답**:
```json
[
  {
    "item_code": "71412-T6000S",
    "item_name": "PNL-FR DR INR, LH",
    "item_type": "WIP",
    "process_name": "프레스",
    "lots": [
      {
        "lot_number": "PR-231209-001",
        "production_date": "2023-12-09",
        "days_old": 5,
        "quantity": 400,
        "status": "urgent"
      }
    ]
  }
]
```

---

## 7. 인증 (Authentication)

### 7.1 로그인
- **POST** `/auth/login`
```json
{
  "username": "admin",
  "password": "password"
}
```

**응답**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 7.2 토큰 갱신
- **POST** `/auth/refresh`

---

## HTTP 상태 코드

| 코드 | 의미 | 사용 |
|------|------|------|
| 200 | OK | 정상 처리 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 (검증 실패) |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복 (예: LOT 번호 중복) |
| 422 | Unprocessable Entity | 비즈니스 로직 오류 (예: 오투입) |
| 500 | Internal Server Error | 서버 오류 |

---

## 에러 응답 형식

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

---

## 페이지네이션

목록 조회 API는 다음 형식을 따릅니다:

**Query Parameters**:
- `page`: 페이지 번호 (기본값: 1)
- `per_page`: 페이지당 항목 수 (기본값: 20, 최대: 100)

**응답**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

---

## WebSocket 이벤트

실시간 업데이트를 위한 WebSocket 엔드포인트: `ws://localhost:8000/ws`

### 이벤트 타입

1. **pallet_updated**: 팔레트 상태 변경 (생성, LOT 연결, 상태 강제 변경)
```json
{
  "event": "pallet_updated",
  "data": {
    "pallet_id": 123,
    "pallet_no": "PLT-2025-001",
    "status": "Consuming",
    "tag_status": "AVAILABLE"
  }
}
```

2. **scan_event**: 스캔 이벤트 발생 (성공 시)
```json
{
  "event": "scan_event",
  "data": {
    "type": "SCAN",
    "pbl_location": "IN",
    "process_code": "PRESS",
    "scan_time": "2025-11-17T09:23:45.123456",
    "pallet_no": "PLT-2025-001",
    "status": "Consuming",
    "epc": "E2801170000002036B3D8CCD",
    "port_name": "COM3",
    "success": true
  }
}
```

3. **reader_status**: 리더기 상태 변경
```json
{
  "event": "reader_status",
  "data": {
    "port_name": "COM3",
    "status": "CONNECTED",
    "timestamp": "2025-11-17T09:23:45.123456"
  }
}
```

4. **scan_error**: 스캔 에러 발생
```json
{
  "event": "scan_error",
  "data": {
    "type": "WRONG_PART",
    "port_name": "COM3",
    "epc": "E280...",
    "message": "오투입 감지..."
  }
}
```

---

## 참고 문서
- API 서버 상세 명세: `api-server-spec.md`
- 시스템 명세: `../rfid-logistics-tracking-system.md`
- DB 스키마: `../database/schema.md`
