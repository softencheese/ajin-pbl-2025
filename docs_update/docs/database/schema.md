# 데이터베이스 스키마 명세서

## 개요
AJIN RFID 물류 추적 시스템의 데이터베이스 스키마를 정의합니다.

**DBMS**: MySQL 8.0
**Character Set**: utf8mb4
**Collation**: utf8mb4_unicode_ci

---

## 설계 원칙

### 핵심 개념: 품목(Item)과 LOT의 분리

| 개념 | 역할 | 예시 |
|------|------|------|
| **품목 (Item)** | "무엇인가?" - 제품의 종류/규격 정의 | 원자재코드: STEEL-A, 품번: 71412-T6000S |
| **LOT** | "어떤 것인가?" - 실물 인스턴스 추적 | LOT번호: IN-231211-001, SH-1001 |

> [!IMPORTANT]
> - **원자재 코드는 품번과 동일한 개념**입니다. 동일한 코드로 여러 번 입고될 수 있습니다.
> - **LOT 번호는 시스템이 자동 생성**하는 고유 식별자입니다. 입고/생산 시마다 새로 발행됩니다.
> - 원자재 종류는 `item_id` → `items.item_code`로 추적합니다.

---

## 테이블 구조

### 1. 마스터 테이블 (3개)

#### 1.1 items (통합 품목 마스터)
```sql
CREATE TABLE items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  item_code VARCHAR(50) UNIQUE NOT NULL COMMENT '품번 또는 원자재코드 (고유)',
  item_name VARCHAR(200) NOT NULL COMMENT '품명',
  item_type ENUM('RAW', 'WIP', 'PRODUCT') NOT NULL COMMENT 'RAW:원자재, WIP:재공품(중간품), PRODUCT:완제품',
  unit VARCHAR(20) DEFAULT 'EA' COMMENT '단위',
  spec VARCHAR(200) COMMENT '규격 (LH/RH, 색상, 재질 등)',
  vehicle_model VARCHAR(50) COMMENT '적용 차종 (JX1, NE)',
  default_supplier VARCHAR(100) COMMENT '기본 공급사 (원자재인 경우)',
  is_active BOOLEAN DEFAULT TRUE COMMENT '사용 여부',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_item_code (item_code),
  INDEX idx_item_type (item_type),
  INDEX idx_vehicle_model (vehicle_model)
) COMMENT '통합 품목 마스터 (원자재, 재공품, 완제품)';
```

**용도**: 원자재, 중간품, 완제품 모든 품목의 기준 정보 통합 관리

**item_type 구분**:
- `RAW`: 원자재 (코일, 철판 등)
- `WIP`: 재공품/중간품 (샤링품, 프레스품 등)
- `PRODUCT`: 완제품 (조립 완료 제품)

**예시 데이터**:
```sql
INSERT INTO items (item_code, item_name, item_type, spec, vehicle_model) VALUES
('STEEL-SPCC', 'SPCC 냉연강판', 'RAW', '1.2t x 1219mm', NULL),
('71412-T6000S', 'PNL-FR DR INR LH', 'WIP', 'LH', 'JX1'),
('76211-GI000', 'ASSY-FR DR MODULE', 'PRODUCT', 'LH', 'NE');
```

---

#### 1.2 processes (공정)
```sql
CREATE TABLE processes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  process_code VARCHAR(20) UNIQUE NOT NULL COMMENT '공정 코드',
  process_name VARCHAR(50) NOT NULL COMMENT '공정명',
  process_order INT NOT NULL COMMENT '공정 순서',
  production_line VARCHAR(50) COMMENT '생산 라인',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_process_order (process_order),
  INDEX idx_process_code (process_code)
) COMMENT '공정 마스터';
```

**예시 데이터**:
```sql
INSERT INTO processes (process_code, process_name, process_order, production_line) VALUES
('RECEIVING', '입고', 0, '입고장'),
('SHEARING', '샤링', 1, '400T'),
('PRESS', '프레스', 2, '1500T'),
('ASSEMBLY', '조립', 3, '조립 라인 1'),
('SHIPPING', '출하', 4, '출하장');
```

---

#### 1.3 rfid_reader_locations (리더기 위치)
```sql
CREATE TABLE rfid_reader_locations (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  port_name VARCHAR(50) UNIQUE NOT NULL COMMENT '포트 이름 (COM3, READER_01 등)',
  process_id BIGINT COMMENT '공정 ID (미등록 시 NULL)',
  location_type ENUM('IN', 'OUT', 'HOLD', 'DEFECT', 'FINISH', 'RETURN') COMMENT '위치 타입',
  description VARCHAR(200) COMMENT '리더기 설명',
  is_active BOOLEAN DEFAULT TRUE COMMENT '활성 여부',
  last_scan_time DATETIME COMMENT '마지막 스캔 시간',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (process_id) REFERENCES processes(id),
  INDEX idx_port_name (port_name),
  INDEX idx_process_location (process_id, location_type)
) COMMENT 'RFID 리더기 위치 매핑';
```

**위치 타입 설명**:
- `IN`: 소비용 팔레트 투입구 (Stock → Consuming)
- `OUT`: 생산용 팔레트 출구 (Empty → Producing, Producing → Stock/Finished)
- `HOLD`: 보류 처리
- `DEFECT`: 불량 처리
- `FINISH`: 완제품 완료
- `RETURN`: 빈 팔레트 회수

---

### 2. LOT 관리 테이블 (2개)

#### 2.1 lots (통합 LOT 관리)
```sql
CREATE TABLE lots (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  lot_number VARCHAR(50) UNIQUE NOT NULL COMMENT 'LOT 번호 (시스템 자동 생성, 고유)',
  barcode VARCHAR(100) COMMENT '실물 바코드 번호 (라벨 스캔용)',
  item_id BIGINT NOT NULL COMMENT '품목 ID',
  quantity INT NOT NULL COMMENT '현재 수량',
  initial_quantity INT NOT NULL COMMENT '초기 수량',
  status ENUM('WAIT', 'PROCESS', 'STOCK', 'CONSUMED', 'SHIPPED', 'HOLD', 'DEFECT') DEFAULT 'WAIT' COMMENT 'LOT 상태',
  production_date DATE NOT NULL COMMENT '생산일 또는 입고일',
  process_id BIGINT COMMENT '생성된 공정 ID',
  supplier VARCHAR(100) COMMENT '공급사 (원자재 입고 시, 기본 공급사와 다를 경우)',
  worker_name VARCHAR(50) COMMENT '작업자',
  qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
  notes TEXT COMMENT '비고',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (item_id) REFERENCES items(id),
  FOREIGN KEY (process_id) REFERENCES processes(id),
  INDEX idx_lot_number (lot_number),
  INDEX idx_item_id (item_id),
  INDEX idx_production_date (production_date),
  INDEX idx_status (status)
) COMMENT '통합 LOT 관리 (원자재, 중간품, 완제품 모두 포함)';
```

**용도**: 모든 실물 인스턴스의 추적 단위

**LOT 번호 생성 규칙** (예시):
- 원자재 입고: `IN-YYMMDD-SEQ` (예: `IN-231211-001`)
- 샤링 생산: `SH-YYMMDD-SEQ` (예: `SH-231211-001`)
- 프레스 생산: `PR-YYMMDD-SEQ` (예: `PR-231211-001`)
- 조립 생산: `AS-YYMMDD-SEQ` (예: `AS-231211-001`)

**status 상태값**:
- `WAIT`: 대기 (입고 후 QC 대기 등)
- `PROCESS`: 공정 진행 중
- `STOCK`: 재고 (생산 완료, 다음 공정 대기)
- `CONSUMED`: 소비 완료
- `SHIPPED`: 출하 완료
- `HOLD`: 보류
- `DEFECT`: 불량

**중요 규칙**:
- `lot_number`는 시스템이 자동 생성하는 **유일 식별자** (절대 중복 불가)
- 원자재 종류는 `item_id` → `items.item_code`로 추적
- 원자재 입고 시에도 반드시 LOT 생성 필요 (추적성 시작점)

**원자재 입고 워크플로우** (RFID 불필요):
```
1. 원자재 입고 등록 (수동)
   ├─ 사용자 입력: 품목(item_id), 수량, 입고일, 공급사
   ├─ 시스템: LOT 번호 자동 생성 (예: IN-231211-001)
   └─ 결과: lots 테이블에 새 LOT 생성 (status: STOCK)

2. 샤링 공정 투입
   ├─ 작업자: 원자재 LOT 선택 (드롭다운 or 바코드)
   ├─ 작업자: 샤링품 품목 선택, 생산 수량 입력
   ├─ 시스템: 새 샤링품 LOT 생성 (예: SH-231211-001)
   └─ 시스템: lot_genealogy에 관계 기록
             (input: IN-231211-001 → output: SH-231211-001)

3. 원자재 LOT 상태 업데이트
   └─ 전량 소비 시: status → CONSUMED
```

---

#### 2.2 lot_genealogy (LOT 족보)
```sql
CREATE TABLE lot_genealogy (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  input_lot_id BIGINT NOT NULL COMMENT '투입 LOT ID (부모)',
  output_lot_id BIGINT NOT NULL COMMENT '생성 LOT ID (자식)',
  process_id BIGINT NOT NULL COMMENT '발생 공정 ID',
  quantity_consumed INT NOT NULL COMMENT '투입 수량',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (input_lot_id) REFERENCES lots(id),
  FOREIGN KEY (output_lot_id) REFERENCES lots(id),
  FOREIGN KEY (process_id) REFERENCES processes(id),
  INDEX idx_input_lot (input_lot_id),
  INDEX idx_output_lot (output_lot_id),
  INDEX idx_process (process_id)
) COMMENT 'LOT 족보 (투입-산출 관계, 추적성 핵심)';
```

**용도**: 모든 공정 간 부모-자식 관계 기록 (추적성의 핵심)

**추적 시나리오**:
1. **정방향 추적** (원자재 → 완제품): `input_lot_id`로 검색
   - "이 원자재 LOT가 어디에 사용되었는가?"
2. **역방향 추적** (완제품 → 원자재): `output_lot_id`로 검색
   - "이 완제품은 어떤 원자재로 만들어졌는가?"

**예시**:
```sql
-- 샤링 공정: 원자재 IN-231211-001 → 샤링품 SH-231211-001
INSERT INTO lot_genealogy (input_lot_id, output_lot_id, process_id, quantity_consumed)
VALUES (1, 2, 2, 100);

-- 프레스 공정: 샤링품 SH-231211-001 → 프레스품 PR-231211-001
INSERT INTO lot_genealogy (input_lot_id, output_lot_id, process_id, quantity_consumed)
VALUES (2, 3, 3, 100);

-- 조립 공정: 프레스품 PR-231211-001 + 부품 LOT → 완제품 AS-231211-001
INSERT INTO lot_genealogy (input_lot_id, output_lot_id, process_id, quantity_consumed)
VALUES (3, 5, 4, 50);
INSERT INTO lot_genealogy (input_lot_id, output_lot_id, process_id, quantity_consumed)
VALUES (4, 5, 4, 50);
```

---

### 3. RFID 추적 테이블 (3개)

#### 3.1 rfid_tags (RFID 태그)
```sql
CREATE TABLE rfid_tags (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  epc VARCHAR(100) UNIQUE NOT NULL COMMENT 'EPC 코드',
  tag_type ENUM('PALLET', 'PRODUCT', 'OTHER') DEFAULT 'PALLET',
  status ENUM('AVAILABLE', 'IN_USE', 'DAMAGED') DEFAULT 'AVAILABLE' COMMENT '태그 상태',
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deregistered_at TIMESTAMP NULL COMMENT '등록 해제 시각',
  INDEX idx_epc (epc),
  INDEX idx_status (status)
) COMMENT 'RFID 태그 마스터';
```

---

#### 3.2 pallets (팔레트)
```sql
CREATE TABLE pallets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pallet_no VARCHAR(50) UNIQUE NOT NULL COMMENT '팔레트 번호',
  rfid_epc VARCHAR(100) UNIQUE NOT NULL COMMENT 'RFID EPC',
  status ENUM(
    'Generated',      -- 생성됨 (등록만)
    'Empty',          -- 빈 팔레트
    'Stock',          -- 재고 (만차)
    'Consuming',      -- 소비 중
    'Producing',      -- 생산 중
    'Finished',       -- 완제품
    'Deregistered',   -- 등록 해제 (회수)
    'Hold',           -- 보류
    'Defect'          -- 불량
  ) DEFAULT 'Generated',
  lot_id BIGINT COMMENT 'LOT ID (현재 적재된 LOT)',
  current_process_id BIGINT COMMENT '현재 공정 ID',
  quantity INT DEFAULT 0 COMMENT '현재 적재 수량',
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (lot_id) REFERENCES lots(id),
  FOREIGN KEY (current_process_id) REFERENCES processes(id),
  INDEX idx_rfid_epc (rfid_epc),
  INDEX idx_status (status),
  INDEX idx_lot_id (lot_id)
) COMMENT '팔레트 (RFID 부착)';
```

**변경 사항**:
- 기존 `lot_id`, `assembly_lot_id` 분리 → **`lot_id` 하나로 통합**
- 모든 LOT가 `lots` 테이블에 통합되었으므로 단일 FK로 충분

**상태 전이 규칙**:
- 상세 내용은 `pallet-state-machine.md` 참조

---

#### 3.3 pallet_histories (팔레트 이력)
```sql
CREATE TABLE pallet_histories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pallet_id BIGINT NOT NULL COMMENT '팔레트 ID',
  lot_id BIGINT COMMENT 'LOT ID',
  previous_status VARCHAR(20) NOT NULL COMMENT '이전 상태',
  new_status VARCHAR(20) NOT NULL COMMENT '새 상태',
  process_id BIGINT COMMENT '공정 ID',
  location_type VARCHAR(20) COMMENT '위치 타입',
  reader_location_id BIGINT COMMENT '리더기 위치 ID',
  event_type VARCHAR(50) COMMENT '이벤트 유형 (SCAN, STATUS_CHANGE, FIFO_VIOLATION 등)',
  scan_time TIMESTAMP NOT NULL COMMENT '스캔 시각',
  worker_name VARCHAR(50) COMMENT '작업자',
  notes TEXT COMMENT '비고 (FIFO 위반 등)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (pallet_id) REFERENCES pallets(id),
  FOREIGN KEY (lot_id) REFERENCES lots(id),
  FOREIGN KEY (process_id) REFERENCES processes(id),
  FOREIGN KEY (reader_location_id) REFERENCES rfid_reader_locations(id),
  INDEX idx_pallet_id (pallet_id),
  INDEX idx_lot_id (lot_id),
  INDEX idx_scan_time (scan_time),
  INDEX idx_process_id (process_id)
) COMMENT '팔레트 상태 변경 이력 (불변 로그)';
```

**중요**:
- **절대 삭제 금지** (추적성 보장)
- 모든 상태 전이를 기록
- FIFO 위반, 오투입 등 이벤트 기록

---

## 뷰 (Views)

### 1. v_pallet_status (팔레트 현황)
```sql
CREATE VIEW v_pallet_status AS
SELECT 
  p.id,
  p.pallet_no,
  p.rfid_epc,
  p.status,
  l.lot_number,
  i.item_code,
  i.item_name,
  i.item_type,
  pr.process_name AS current_process,
  p.quantity,
  p.updated_at
FROM pallets p
LEFT JOIN lots l ON p.lot_id = l.id
LEFT JOIN items i ON l.item_id = i.id
LEFT JOIN processes pr ON p.current_process_id = pr.id;
```

---

### 2. v_stock_inventory (재고 현황)
```sql
CREATE VIEW v_stock_inventory AS
SELECT 
  i.item_code,
  i.item_name,
  i.item_type,
  pr.process_name,
  l.lot_number,
  l.production_date,
  DATEDIFF(CURDATE(), l.production_date) AS days_old,
  COUNT(p.id) AS pallet_count,
  SUM(p.quantity) AS total_quantity
FROM pallets p
INNER JOIN lots l ON p.lot_id = l.id
INNER JOIN items i ON l.item_id = i.id
LEFT JOIN processes pr ON l.process_id = pr.id
WHERE p.status = 'Stock'
GROUP BY i.item_code, i.item_name, i.item_type, pr.process_name, l.lot_number, l.production_date
ORDER BY l.production_date ASC;
```

---

### 3. v_lot_forward_trace (정방향 추적: 원자재 → 완제품)
```sql
CREATE VIEW v_lot_forward_trace AS
WITH RECURSIVE trace AS (
  -- Base case: 원자재 LOT
  SELECT 
    l.id AS lot_id,
    l.lot_number,
    i.item_code,
    i.item_type,
    l.id AS root_lot_id,
    0 AS depth
  FROM lots l
  JOIN items i ON l.item_id = i.id
  WHERE i.item_type = 'RAW'
  
  UNION ALL
  
  -- Recursive case: 자식 LOT 추적
  SELECT 
    l.id AS lot_id,
    l.lot_number,
    i.item_code,
    i.item_type,
    t.root_lot_id,
    t.depth + 1
  FROM trace t
  JOIN lot_genealogy g ON t.lot_id = g.input_lot_id
  JOIN lots l ON g.output_lot_id = l.id
  JOIN items i ON l.item_id = i.id
)
SELECT * FROM trace;
```

---

### 4. v_lot_backward_trace (역방향 추적: 완제품 → 원자재)
```sql
CREATE VIEW v_lot_backward_trace AS
WITH RECURSIVE trace AS (
  -- Base case: 완제품 또는 특정 LOT
  SELECT 
    l.id AS lot_id,
    l.lot_number,
    i.item_code,
    i.item_type,
    l.id AS leaf_lot_id,
    0 AS depth
  FROM lots l
  JOIN items i ON l.item_id = i.id
  WHERE i.item_type = 'PRODUCT'
  
  UNION ALL
  
  -- Recursive case: 부모 LOT 추적
  SELECT 
    l.id AS lot_id,
    l.lot_number,
    i.item_code,
    i.item_type,
    t.leaf_lot_id,
    t.depth + 1
  FROM trace t
  JOIN lot_genealogy g ON t.lot_id = g.output_lot_id
  JOIN lots l ON g.input_lot_id = l.id
  JOIN items i ON l.item_id = i.id
)
SELECT * FROM trace;
```

---

### 5. v_lot_full_genealogy (LOT 전체 족보)
```sql
CREATE VIEW v_lot_full_genealogy AS
SELECT 
  g.id AS genealogy_id,
  il.lot_number AS input_lot_number,
  ii.item_code AS input_item_code,
  ii.item_type AS input_item_type,
  ol.lot_number AS output_lot_number,
  oi.item_code AS output_item_code,
  oi.item_type AS output_item_type,
  p.process_name,
  g.quantity_consumed,
  g.created_at
FROM lot_genealogy g
JOIN lots il ON g.input_lot_id = il.id
JOIN items ii ON il.item_id = ii.id
JOIN lots ol ON g.output_lot_id = ol.id
JOIN items oi ON ol.item_id = oi.id
JOIN processes p ON g.process_id = p.id
ORDER BY g.created_at;
```

---

## 데이터 무결성 규칙

### 1. 추적 키 보호
```sql
-- 절대 삭제 금지
DELETE FROM lots WHERE id = ?;           -- ❌ 금지
DELETE FROM lot_genealogy WHERE id = ?;  -- ❌ 금지
DELETE FROM pallets WHERE id = ?;        -- ❌ 금지
DELETE FROM pallet_histories WHERE id = ?; -- ❌ 금지
```

### 2. LOT 생성 규칙
- 원자재 입고 시: 반드시 `lots` 테이블에 새 LOT 생성
- LOT 번호는 시스템이 자동 생성 (중복 불가)
- 외부 코일번호는 `external_lot_no`에 참조용으로 저장 (중복 가능)

### 3. 족보 기록 규칙
- 공정 완료 시 반드시 `lot_genealogy`에 투입-산출 관계 기록
- 조립품의 경우 여러 투입 LOT와 하나의 산출 LOT 연결 가능

### 4. 팔레트-LOT 매핑
- 팔레트는 하나의 LOT만 적재 가능 (`lot_id` 단일 FK)
- LOT 변경 시 이력 기록 필수

### 5. FIFO 검증
- 같은 품목의 더 오래된 재고(Stock 상태) 존재 여부 확인
- 위반 시: 경고 표시 (투입은 가능, 이력에 기록)

### 6. 오투입 검증
- LOT 품목과 공정 요구 품목 불일치 시 투입 차단
- Override 불가 (시스템 차단 유지)

---

## 인덱스 전략

### 검색 최적화
- `lot_number`: UNIQUE 인덱스 (추적 키)
- `external_lot_no`: 일반 인덱스 (중복 허용, 검색용)
- `production_date`: 범위 검색용
- `status`: 필터링용

### 조인 최적화
- 모든 Foreign Key에 인덱스 자동 생성
- 복합 인덱스: `(process_id, location_type)`

---

## 백업 및 복구

### 백업
```bash
# 전체 백업
docker exec ajin-db mysqldump -u root -p ajin_rfid > backup.sql

# 테이블별 백업
docker exec ajin-db mysqldump -u root -p ajin_rfid pallet_histories lot_genealogy > trace_backup.sql
```

### 복구
```bash
docker exec -i ajin-db mysql -u root -p ajin_rfid < backup.sql
```

---

## 테이블 요약

| 분류 | 테이블명 | 설명 | 비고 |
|------|----------|------|------|
| 마스터 | `items` | 통합 품목 마스터 | RAW/WIP/PRODUCT 구분 |
| 마스터 | `processes` | 공정 마스터 | 기존과 동일 |
| 마스터 | `rfid_reader_locations` | 리더기 위치 | 기존과 동일 |
| LOT | `lots` | 통합 LOT 관리 | 원자재~완제품 모두 |
| LOT | `lot_genealogy` | LOT 족보 | 추적성 핵심 |
| RFID | `rfid_tags` | RFID 태그 | 기존과 동일 |
| RFID | `pallets` | 팔레트 | lot_id 단일화 |
| RFID | `pallet_histories` | 팔레트 이력 | 기존과 동일 |

**총 8개 테이블** (기존 10개에서 통합으로 감소)

---

## 참고 문서
- 데이터베이스 아키텍처: `database-architecture.md`
- 팔레트 상태 기계: `pallet-state-machine.md`
- 시스템 명세: `../rfid-logistics-tracking-system.md`
- 시스템 헌법: `../constitution.md`
