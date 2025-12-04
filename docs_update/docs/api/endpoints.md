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
    "lot_no": "LOT-20251017-001",
    "part_number": "71412-T6000S"
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
      "lot_no": "LOT-20251015-003",
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
    "expected_part": "71412-T6000S",
    "actual_part": "76211-GI000"
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

### 2.1 원자재 (Raw Materials)

#### 목록 조회
- **GET** `/materials`
- **Query Parameters**: `page`, `per_page`, `search`

#### 상세 조회
- **GET** `/materials/{id}`

#### 등록
- **POST** `/materials`
```json
{
  "coil_number": "C059461B",
  "material_name": "SPHC 1.6T",
  "supplier": "포스코",
  "receipt_date": "2025-10-15",
  "qc_passed": true
}
```

#### 수정
- **PUT** `/materials/{id}`

#### 삭제
- **DELETE** `/materials/{id}` (사용 이력 없는 경우만)

---

### 2.2 품번 (Parts)

#### 목록 조회
- **GET** `/parts`
- **Query Parameters**: `page`, `per_page`, `search`, `is_assembly`, `is_final_product`

#### 등록
- **POST** `/parts`
```json
{
  "part_number": "71412-T6000S",
  "part_name": "PNL-FR DR INR, LH",
  "part_spec": "LH, 1.6T",
  "vehicle_model": "JX1",
  "is_assembly": false,
  "is_final_product": false
}
```

---

### 2.3 공정 (Processes)

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

### 2.4 RFID 리더기 위치 (Reader Locations)

#### 목록 조회
- **GET** `/reader-locations`

#### 등록 (수동)
> **Note**: 일반적으로 리더기는 Heartbeat 수신 시 자동 등록됩니다. 이 엔드포인트는 수동 등록이 필요한 경우에만 사용합니다.

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

### 2.5 RFID 태그 (RFID Tags)

#### 목록 조회
- **GET** `/rfid-tags`
- **Query Parameters**: `status` (AVAILABLE, IN_USE, DAMAGED)

#### 상세 조회
- **GET** `/rfid-tags/{id}`

#### 등록
- **POST** `/rfid-tags`
```json
{
  "epc": "E2801170000002036B3D8CCD"
}
```

#### 상태 변경
- **PUT** `/rfid-tags/{id}/status`
```json
{
  "status": "DAMAGED",
  "reason": "물리적 손상"
}
```

#### 팔레트 연결 해제
- **POST** `/rfid-tags/{id}/detach`

---

### 2.6 팔레트 (Pallets)

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

---

## 3. 생산 관리

### 3.1 중간품 LOT

#### 생성
- **POST** `/lots`
```json
{
  "lot_no": "LOT-20251017-001",
  "part_id": 10,
  "process_id": 1,
  "material_id": 5,
  "quantity": 400,
  "production_date": "2025-10-17",
  "worker_name": "최영일"
}
```

#### 목록 조회
- **GET** `/lots`
- **Query Parameters**: `part_id`, `process_id`, `date_from`, `date_to`

---

### 3.2 조립품 LOT

#### 생성
- **POST** `/assembly-lots`
```json
{
  "lot_no": "ASM-20251018-001",
  "part_id": 20,
  "assembly_date": "2025-10-18",
  "quantity": 100,
  "worker_name": "전재민"
}
```

#### 구성 요소 추가
- **POST** `/assembly-lots/{id}/components`
```json
{
  "component_lot_id": 123,
  "quantity": 100
}
```

---

## 4. 추적성 조회

### 4.1 정방향 추적 (코일 → 제품)
**엔드포인트**: `GET /trace/forward`

**Query Parameters**: `coil_number`

**응답**:
```json
{
  "coil": {
    "coil_number": "C059461B",
    "material_name": "SPHC 1.6T"
  },
  "intermediate_lots": [
    {
      "lot_no": "LOT-20251017-001",
      "part_number": "71412-T6000S",
      "quantity": 400
    }
  ],
  "assembly_lots": [
    {
      "lot_no": "ASM-20251018-001",
      "part_number": "ASSY-DOOR",
      "quantity": 100
    }
  ]
}
```

---

### 4.2 역방향 추적 (제품 → 코일)
**엔드포인트**: `GET /trace/backward`

**Query Parameters**: `lot_no` or `assembly_lot_no`

**응답**:
```json
{
  "product": {
    "lot_no": "ASM-20251018-001",
    "part_number": "ASSY-DOOR"
  },
  "components": [
    {
      "lot_no": "LOT-20251017-001",
      "part_number": "71412-T6000S",
      "coil_number": "C059461B"
    }
  ]
}
```

---

### 4.3 드릴다운 검색
**엔드포인트**: `GET /trace/drill-down`

**Query Parameters**: `search` (품번, LOT, 코일, 팔레트 번호)

**응답**: 검색어 유형에 따라 정방향/역방향 통합 결과 반환

---

## 5. 모니터링 및 통계

### 5.1 대시보드 요약
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

### 5.2 공정별 현황
- **GET** `/dashboard/process-status`

### 5.3 재고 현황 (FIFO 포함)
- **GET** `/inventory/stock`

**응답**:
```json
[
  {
    "part_number": "71412-T6000S",
    "process_name": "프레스",
    "lots": [
      {
        "lot_no": "LOT-20251015-003",
        "production_date": "2025-10-15",
        "days_old": 5,
        "quantity": 400,
        "status": "urgent"
      }
    ]
  }
]
```

---

## 6. 인증 (Authentication)

### 6.1 로그인
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

### 6.2 토큰 갱신
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

1. **pallet_updated**: 팔레트 상태 변경
```json
{
  "event": "pallet_updated",
  "data": {
    "pallet_id": 123,
    "pallet_no": "PLT-2025-001",
    "status": "Consuming"
  }
}
```

2. **scan_event**: 스캔 이벤트 발생
```json
{
  "event": "scan_event",
  "data": {
    "epc": "E280...",
    "port_name": "COM3",
    "timestamp": "2025-11-17T09:23:45.123Z"
  }
}
```

3. **reader_status**: 리더기 상태 변경
```json
{
  "event": "reader_status",
  "data": {
    "port_name": "COM3",
    "status": "CONNECTED"
  }
}
```

---

## 참고 문서
- API 서버 상세 명세: `api-server-spec.md`
- 시스템 명세: `../.specify/specs/rfid-logistics-tracking-system.md`
