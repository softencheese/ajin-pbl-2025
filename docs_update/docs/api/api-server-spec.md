# API 서버 상세 명세서

> **목적**: RFID 물류 추적 시스템 API 서버 구현 명세
> **대상**: Speckit Plan - API 서버 개발

---

## 1. API 서버 역할

### 1.1 개요
- RFID 스캔 이벤트 처리 및 비즈니스 로직 실행
- 포트 기반 공정/위치 자동 식별
- 팔레트 상태 전이 관리
- 검증 로직 실행 (FIFO, 오투입, 완제품)
- 양방향 추적성 제공
- 웹 애플리케이션에 데이터 제공

### 1.2 기술 스택 권장
- **언어**: Node.js (Express) / Python (FastAPI) / Java (Spring Boot)
- **데이터베이스**: MySQL 8.0+
- **캐싱**: Redis (선택 사항)
- **실시간 통신**: WebSocket / Server-Sent Events

---

## 2. API 엔드포인트 명세

### 2.1 RFID 처리

#### 2.1.1 스캔 이벤트 처리
**엔드포인트**: `POST /api/v1/rfid/scan`

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

**처리 로직**:
1. `port_name`으로 `rfid_reader_locations` 조회 → `process_id`, `location_type` 확인
2. EPC로 `pallets` 조회 (없으면 에러)
3. 현재 팔레트 상태 확인
4. 공정 및 위치 타입에 따라 상태 전이 결정
5. 검증 로직 실행 (FIFO, 오투입, 완제품)
6. 트랜잭션 시작:
   - 팔레트 상태 업데이트
   - `pallet_histories` 이력 기록
   - 조립품 구성 요소 기록 (필요 시)
7. 트랜잭션 커밋
8. 피드백 명령 생성 및 반환

**응답 (성공)**:
```json
{
  "success": true,
  "pallet": {
    "pallet_no": "PLT-2025-001",
    "previous_status": "Stock",
    "current_status": "Consuming",
    "lot_no": "LOT-20251017-001",
    "part_number": "71412-T6000S",
    "part_name": "PNL-FR DR INR, LH"
  },
  "feedback": {
    "action": "BUZZER",
    "pattern": "SUCCESS",
    "count": 1,
    "led_color": "GREEN"
  }
}
```

**응답 (FIFO 위반 경고)**:
```json
{
  "success": true,
  "warning": {
    "type": "FIFO_VIOLATION",
    "message": "더 오래된 재고가 있습니다. 무시하고 투입하시겠습니까?",
    "oldest_stock": {
      "lot_no": "LOT-20251015-003",
      "production_date": "2025-10-15",
      "days_old": 2
    }
  },
  "pallet": { ... },
  "feedback": {
    "pattern": "WARNING",
    "count": 3,
    "led_color": "YELLOW"
  }
}
```

**응답 (오투입 차단)**:
```json
{
  "success": false,
  "error": {
    "type": "WRONG_PART",
    "message": "품번 불일치 - 투입 불가",
    "details": {
      "expected_part": "71412-T6000S",
      "actual_part": "76211-GI000",
      "process": "프레스 1500T"
    }
  },
  "feedback": {
    "pattern": "ERROR",
    "count": 3,
    "led_color": "RED"
  }
}
```

#### 2.1.2 리더기 상태 수신
**엔드포인트**: `POST /api/v1/rfid/reader-status`

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

**처리**:
- 리더기 상태 로그 기록
- **자동 등록**: `port_name`이 DB에 없으면 새 레코드 생성 (process_id=NULL)
- 실시간 모니터링 화면에 업데이트 (WebSocket)

**응답**:
```json
{
  "success": true,
  "message": "Status updated"
}
```

---

### 2.2 마스터 데이터 관리

#### 2.2.1 원자재 관리
- `GET /api/v1/materials` - 원자재 목록
- `GET /api/v1/materials/:id` - 원자재 상세
- `POST /api/v1/materials` - 원자재 등록
- `PUT /api/v1/materials/:id` - 원자재 수정
- `DELETE /api/v1/materials/:id` - 원자재 삭제 (사용 이력 없는 경우만)

**등록 요청**:
```json
{
  "coil_number": "C059461B",
  "material_name": "SPHC 1.6T",
  "supplier": "포스코",
  "receipt_date": "2025-10-15",
  "qc_passed": true
}
```

#### 2.2.2 품번 관리
- `GET /api/v1/parts` - 품번 목록
- `POST /api/v1/parts` - 품번 등록

**등록 요청**:
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

#### 2.2.3 공정 관리
- `GET /api/v1/processes` - 공정 목록
- `POST /api/v1/processes` - 공정 등록
- `PUT /api/v1/processes/:id/order` - 공정 순서 변경

**등록 요청**:
```json
{
  "process_code": "SHEARING",
  "process_name": "샤링",
  "process_order": 1,
  "production_line": "400T"
}
```

#### 2.2.4 RFID 리더기 위치 관리
- `GET /api/v1/reader-locations` - 리더기 위치 목록 (미등록 포함)
- `PUT /api/v1/reader-locations/:id/register` - 리더기 등록 (공정 매핑)
- `PUT /api/v1/reader-locations/:id` - 리더기 정보 수정

**등록(매핑) 요청**:
```json
{
  "process_id": 2,
  "location_type": "IN",
  "description": "프레스 1500T 투입구 리더기"
}
```

#### 2.2.5 팔레트 관리
- `GET /api/v1/pallets` - 팔레트 목록
- `GET /api/v1/pallets/:id` - 팔레트 상세
- `POST /api/v1/pallets` - 팔레트 생성
- `PUT /api/v1/pallets/:id/link-lot` - LOT 연결
- `PUT /api/v1/pallets/:id/status` - 상태 강제 변경 (관리자)

**생성 요청**:
```json
{
  "pallet_no": "PLT-2025-001",
  "rfid_epc": "E2801170000002036B3D8CCD"
}
```

**LOT 연결 요청**:
```json
{
  "lot_id": 123
}
```

---

### 2.3 생산 관리

#### 2.3.1 중간품 LOT 생성
**엔드포인트**: `POST /api/v1/lots`

**요청**:
```json
{
  "lot_no": "LOT-20251017-001",
  "part_id": 10,
  "process_id": 1,
  "material_id": 5,
  "quantity": 400,
  "production_date": "2025-10-17",
  "worker_name": "최영일",
  "qc_passed": false
}
```

**검증**:
- `material_id` 필수 (원자재 연결)
- `part_id`가 중간품인지 확인 (`is_assembly = FALSE`)
- `lot_no` 중복 체크

**응답**:
```json
{
  "success": true,
  "lot": {
    "id": 123,
    "lot_no": "LOT-20251017-001",
    "assembly_level": 0
  }
}
```

#### 2.3.2 조립품 LOT 생성
**엔드포인트**: `POST /api/v1/assembly-lots`

**요청**:
```json
{
  "lot_no": "ASM-20251018-001",
  "part_id": 20,
  "assembly_date": "2025-10-18",
  "quantity": 100,
  "worker_name": "전재민",
  "qc_passed": false
}
```

**검증**:
- `part_id`가 조립품인지 확인 (`is_assembly = TRUE`)
- `lot_no` 중복 체크

**응답**:
```json
{
  "success": true,
  "assembly_lot": {
    "id": 45,
    "lot_no": "ASM-20251018-001",
    "assembly_level": 0
  }
}
```

#### 2.3.3 조립품 구성 요소 등록
**엔드포인트**: `POST /api/v1/assembly-lots/:id/components`

**요청**:
```json
{
  "component_lot_id": 123,
  "component_pallet_id": 67,
  "required_quantity_per_unit": 2,
  "total_consumed_quantity": 200
}
```

**처리**:
- 트리거로 `assembly_level` 자동 계산
- 구성 요소의 최대 레벨 + 1

**응답**:
```json
{
  "success": true,
  "component": {
    "id": 89,
    "assembly_lot_id": 45,
    "component_lot_id": 123
  },
  "updated_assembly_level": 1
}
```

---

### 2.4 추적성 조회

#### 2.4.1 정방향 추적 (원자재 → 제품)
**엔드포인트**: `GET /api/v1/trace/forward?coil_number=C059461B`

**쿼리 파라미터**:
- `coil_number` (필수): 코일 번호
- `include_assemblies` (선택, 기본 true): 조립품까지 포함

**응답**:
```json
{
  "coil_number": "C059461B",
  "material_name": "SPHC 1.6T",
  "supplier": "포스코",
  "receipt_date": "2025-10-15",
  "qc_passed": true,
  "produced_lots": [
    {
      "lot_no": "LOT-20251017-001",
      "part_number": "71412-T6000S",
      "part_name": "PNL-FR DR INR, LH",
      "quantity": 400,
      "production_date": "2025-10-17",
      "qc_passed": true,
      "pallets": [
        {
          "pallet_no": "PLT-2025-001",
          "status": "Stock",
          "current_process": "프레스 1500T"
        },
        {
          "pallet_no": "PLT-2025-002",
          "status": "Consuming",
          "current_process": "조립"
        }
      ],
      "used_in_assemblies": [
        {
          "assembly_lot_no": "ASM-20251018-001",
          "assembly_part_number": "76211-GI000",
          "assembly_part_name": "ASSY-DOOR",
          "assembly_level": 2,
          "is_final_product": true,
          "quantity_used": 200
        }
      ]
    }
  ]
}
```

#### 2.4.2 역방향 추적 (제품 → 원자재)
**엔드포인트**: `GET /api/v1/trace/backward?lot_no=ASM-20251018-001`

**쿼리 파라미터**:
- `lot_no` (선택): LOT 번호
- `part_number` (선택): 품번
- `assembly_lot_no` (선택): 조립품 LOT 번호

**응답**:
```json
{
  "lot_no": "ASM-20251018-001",
  "part_number": "76211-GI000",
  "part_name": "ASSY-DOOR",
  "vehicle_model": "JX1",
  "assembly_level": 2,
  "is_final_product": true,
  "components": [
    {
      "component_type": "lot",
      "component_lot_no": "LOT-20251017-001",
      "component_part_number": "71412-T6000S",
      "component_part_name": "PNL-FR DR INR, LH",
      "quantity_used": 200,
      "raw_material": {
        "coil_number": "C059461B",
        "material_name": "SPHC 1.6T",
        "supplier": "포스코",
        "receipt_date": "2025-10-15",
        "qc_passed": true
      }
    },
    {
      "component_type": "assembly",
      "component_assembly_lot_no": "ASM-20251017-002",
      "component_part_number": "71413-T6000S",
      "component_part_name": "PNL-FR DR INR, RH",
      "assembly_level": 1,
      "quantity_used": 200,
      "sub_components": [
        {
          "component_lot_no": "LOT-20251016-005",
          "raw_material": {
            "coil_number": "C059462A",
            "supplier": "포스코"
          }
        }
      ]
    }
  ]
}
```

#### 2.4.3 드릴다운 검색
**엔드포인트**: `GET /api/v1/trace/drill-down?search=71412-T6000S`

**쿼리 파라미터**:
- `search` (필수): 검색어 (품번, 품명, LOT 번호, 코일 번호, 팔레트 번호)

**검색 유형 자동 감지**:
- 품번 패턴: `XXXXX-XXXXXX`
- LOT 번호 패턴: `LOT-YYYYMMDD-XXX`
- 코일 번호 패턴: `CXXXXXX`
- 팔레트 번호 패턴: `PLT-YYYY-XXX`
- 기타: 품명 검색 (LIKE)

**응답**: 정방향 + 역방향 추적 결합

---

### 2.5 모니터링

#### 2.5.1 재고 현황
**엔드포인트**: `GET /api/v1/inventory/stock`

**쿼리 파라미터**:
- `part_number` (선택): 품번 필터
- `process_id` (선택): 공정 필터
- `sort` (선택, 기본 `production_date`): 정렬 기준

**응답**:
```json
{
  "stock_items": [
    {
      "part_number": "71412-T6000S",
      "part_name": "PNL-FR DR INR, LH",
      "vehicle_model": "JX1",
      "process_name": "프레스",
      "production_line": "1500T",
      "production_date": "2025-10-15",
      "pallet_count": 3,
      "total_quantity": 1200,
      "days_old": 5,
      "lot_numbers": ["LOT-20251015-001", "LOT-20251015-002", "LOT-20251015-003"]
    }
  ]
}
```

#### 2.5.2 공정 현황
**엔드포인트**: `GET /api/v1/monitoring/processes`

**응답**:
```json
{
  "processes": [
    {
      "process_id": 2,
      "process_name": "프레스",
      "production_line": "1500T",
      "active_pallets": 8,
      "status_breakdown": {
        "Consuming": 3,
        "Producing": 2,
        "Stock": 3
      }
    }
  ],
  "total_active_pallets": 25,
  "last_updated": "2025-11-17T09:30:00Z"
}
```

#### 2.5.3 리더기 상태
**엔드포인트**: `GET /api/v1/monitoring/readers`

**응답**:
```json
{
  "readers": [
    {
      "id": 1,
      "port_name": "COM3",
      "process_name": "프레스 1500T",
      "location_type": "IN",
      "status": "CONNECTED",
      "last_scan_time": "2025-11-17T09:25:30Z",
      "is_active": true
    },
    {
      "id": 2,
      "port_name": "192.168.1.101:9001",
      "process_name": "조립",
      "location_type": "OUT",
      "status": "DISCONNECTED",
      "error": "Network timeout",
      "is_active": true
    }
  ]
}
```

---

## 3. 상태 전이 로직

### 3.1 샤링 OUT (첫 공정 예외)
- **조건**: `process_id = SHEARING`, `location_type = OUT`
- **전이**: `Empty → Stock`
- **검증**: 없음
- **이력**: "샤링 공정 완료 - 팔레트 적재"

### 3.2 중간품 공정 IN
- **조건**: `process_id != SHEARING`, `location_type = IN`
- **전이 (소비)**: `Stock → Consuming`
  - 검증: FIFO (경고), 오투입 (차단)
- **전이 (생산)**: `Empty → Producing`
  - 검증: 없음

### 3.3 중간품 공정 OUT
- **조건**: `location_type = OUT`, `parts.is_final_product = FALSE`
- **전이 (생산 완료)**: `Producing → Stock`
- **전이 (소비 완료)**: `Consuming → Deregistered`

### 3.4 완제품 조립 OUT
- **조건**: `location_type = OUT`, `parts.is_final_product = TRUE`
- **전이**: `Producing → Finished`
- **검증**: 완제품 여부 확인 (차단)
- **추가 처리**: 조립품 구성 요소 자동 기록

### 3.5 RETURN (빈 팔레트 회수)
- **조건**: `location_type = FINISH`
- **전이**: `Finished → Deregistered`
- **이력**: "완제품 출하 후 빈 팔레트 회수"

---

## 4. 검증 로직

### 4.1 FIFO 검증
**함수**: `check_fifo(part_id, production_date)`

**SQL 쿼리**:
```sql
SELECT COUNT(*) AS older_count
FROM pallets p
JOIN lots l ON p.lot_id = l.id
WHERE l.part_id = :part_id
  AND l.production_date < :production_date
  AND p.status = 'Stock';
```

**결과**:
- `older_count > 0`: FIFO 위반 → 경고 + 무시 가능
- `older_count = 0`: 통과

**의사 코드**:
```javascript
function checkFIFO(partId, productionDate) {
  const olderStock = db.query(`
    SELECT lot_no, production_date, pallet_no
    FROM pallets p
    JOIN lots l ON p.lot_id = l.id
    WHERE l.part_id = ? AND l.production_date < ? AND p.status = 'Stock'
    ORDER BY l.production_date LIMIT 1
  `, [partId, productionDate]);
  
  if (olderStock.length > 0) {
    return {
      violation: true,
      oldest: olderStock[0],
      daysOld: daysDiff(olderStock[0].production_date, productionDate)
    };
  }
  
  return { violation: false };
}
```

### 4.2 오투입 검증
**함수**: `validate_part_number(pallet_id, process_id)`

**로직**:
1. 팔레트의 LOT 품번 확인
2. 공정에서 요구하는 품번 확인 (비즈니스 규칙)
3. 일치 여부 확인

**의사 코드**:
```javascript
function validatePartNumber(palletId, processId) {
  const pallet = db.query(`
    SELECT l.part_id, pt.part_number, pt.part_name
    FROM pallets p
    LEFT JOIN lots l ON p.lot_id = l.id
    LEFT JOIN assembly_lots al ON p.assembly_lot_id = al.id
    JOIN parts pt ON COALESCE(l.part_id, al.part_id) = pt.id
    WHERE p.id = ?
  `, [palletId]);
  
  // 공정별 허용 품번 조회 (예시: 별도 테이블 또는 설정)
  const allowedParts = getAllowedPartsForProcess(processId);
  
  if (!allowedParts.includes(pallet.part_id)) {
    throw new ValidationError({
      type: 'WRONG_PART',
      message: '품번 불일치 - 투입 불가',
      expected: allowedParts,
      actual: pallet.part_number
    });
  }
  
  return true;
}
```

### 4.3 완제품 검증
**함수**: `validate_finished_state(pallet_id)`

**SQL 쿼리**:
```sql
SELECT pt.is_final_product
FROM pallets p
LEFT JOIN lots l ON p.lot_id = l.id
LEFT JOIN assembly_lots al ON p.assembly_lot_id = al.id
JOIN parts pt ON COALESCE(l.part_id, al.part_id) = pt.id
WHERE p.id = :pallet_id;
```

**검증**:
- `is_final_product = FALSE`: Finished 전환 불가 → 에러
- `is_final_product = TRUE`: 통과

---

## 5. 성능 최적화

### 5.1 데이터베이스 인덱싱
- `pallets.rfid_epc` (UNIQUE)
- `pallets.status`
- `lots.production_date`
- `lots.part_id, process_id` (복합)
- `pallet_histories.pallet_id, event_time` (복합)

### 5.2 캐싱 (Redis)
- 리더기 위치 매핑 (port_name → process_id, location_type)
- 활성 팔레트 목록 (TTL: 10초)
- 재고 현황 (TTL: 30초)

### 5.3 Connection Pool
- 최소: 10
- 최대: 50
- 타임아웃: 30초

---

## 6. 보안

### 6.1 인증
- JWT 기반
- Access Token (1시간) + Refresh Token (7일)
- `/api/v1/auth/login` - 로그인
- `/api/v1/auth/refresh` - 토큰 갱신

### 6.2 권한
- **작업자**: 모니터링 조회, 추적성 조회
- **관리자**: 마스터 데이터 등록, 팔레트 상태 강제 변경

### 6.3 감사 로그
- 모든 POST/PUT/DELETE 요청 기록
- 로그 내용: 사용자, 엔드포인트, 요청 데이터, 응답, 타임스탬프

---

## 7. 관련 문서
- **시스템 명세**: `.specify/specs/rfid-logistics-tracking-system.md`
- **임베디드 명세**: `docs/embedded-system-spec.md`
- **웹 앱 명세**: `docs/web-app-spec.md`
- **DB 아키텍처**: `docs/database-architecture.md`
