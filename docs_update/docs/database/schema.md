# 데이터베이스 스키마 명세서

## 개요
AJIN RFID 물류 추적 시스템의 데이터베이스 스키마를 정의합니다.

**DBMS**: MySQL 8.0
**Character Set**: utf8mb4
**Collation**: utf8mb4_unicode_ci

---

## 테이블 구조

### 1. 마스터 테이블 (4개)

#### 1.1 raw_materials (원자재)
```sql
CREATE TABLE raw_materials (
  id INT PRIMARY KEY AUTO_INCREMENT,
  coil_number VARCHAR(50) UNIQUE NOT NULL COMMENT '코일 번호 (추적 키)',
  material_name VARCHAR(100) NOT NULL COMMENT '재질명',
  supplier VARCHAR(100) COMMENT '공급업체',
  receipt_date DATE COMMENT '입고일자',
  qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_coil_number (coil_number),
  INDEX idx_receipt_date (receipt_date)
) COMMENT '원자재(코일) 마스터';
```

**용도**: 원자재 코일 관리 및 추적의 시작점

**제약사항**:
- `coil_number`는 절대 삭제/재사용 금지 (추적성 보장)
- `qc_passed = TRUE`인 경우만 생산 투입 가능

---

#### 1.2 parts (품번)
```sql
CREATE TABLE parts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  part_number VARCHAR(50) UNIQUE NOT NULL COMMENT '품번',
  part_name VARCHAR(200) NOT NULL COMMENT '품명',
  part_spec VARCHAR(100) COMMENT '규격',
  vehicle_model VARCHAR(50) COMMENT '적용 차종',
  is_assembly BOOLEAN DEFAULT FALSE COMMENT '조립품 여부',
  is_final_product BOOLEAN DEFAULT FALSE COMMENT '완제품 여부',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_part_number (part_number),
  INDEX idx_is_assembly (is_assembly),
  INDEX idx_is_final_product (is_final_product)
) COMMENT '품번 마스터';
```

**비즈니스 규칙**:
- `is_assembly = FALSE`: 중간품 (샤링, 프레스 등)
- `is_assembly = TRUE, is_final_product = FALSE`: 하위 조립품
- `is_assembly = TRUE, is_final_product = TRUE`: 최종 완제품

---

#### 1.3 processes (공정)
```sql
CREATE TABLE processes (
  id INT PRIMARY KEY AUTO_INCREMENT,
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
INSERT INTO processes VALUES
(1, 'SHEARING', '샤링', 1, '400T', NOW(), NOW()),
(2, 'PRESS', '프레스', 2, '1500T', NOW(), NOW()),
(3, 'ASSEMBLY', '조립', 3, '조립 라인 1', NOW(), NOW()),
(4, 'SHIPPING', '출하', 4, '출하장', NOW(), NOW());
```

---

#### 1.4 rfid_reader_locations (리더기 위치)
```sql
CREATE TABLE rfid_reader_locations (
  id INT PRIMARY KEY AUTO_INCREMENT,
  port_name VARCHAR(50) UNIQUE NOT NULL COMMENT '포트 이름 (COM3, READER_01 등)',
  process_id INT COMMENT '공정 ID (미등록 시 NULL)',
  location_type ENUM('IN', 'OUT', 'HOLD', 'DEFECT', 'FINISH', 'RETURN') COMMENT '위치 타입 (미등록 시 NULL)',
  description VARCHAR(200) COMMENT '리더기 설명',
  is_active BOOLEAN DEFAULT TRUE COMMENT '활성 여부',
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

### 2. 생산 테이블 (3개)

#### 2.1 lots (중간품 LOT)
```sql
CREATE TABLE lots (
  id INT PRIMARY KEY AUTO_INCREMENT,
  lot_no VARCHAR(50) UNIQUE NOT NULL COMMENT 'LOT 번호 (추적 키)',
  part_id INT NOT NULL COMMENT '품번 ID',
  process_id INT NOT NULL COMMENT '생산 공정 ID',
  material_id INT NOT NULL COMMENT '원자재 ID (필수)',
  quantity INT NOT NULL COMMENT '수량',
  production_date DATE NOT NULL COMMENT '생산일자',
  worker_name VARCHAR(50) COMMENT '작업자명',
  qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
  assembly_level INT DEFAULT 0 COMMENT '조립 깊이 (0=중간품)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (part_id) REFERENCES parts(id),
  FOREIGN KEY (process_id) REFERENCES processes(id),
  FOREIGN KEY (material_id) REFERENCES raw_materials(id),
  INDEX idx_lot_no (lot_no),
  INDEX idx_part_id (part_id),
  INDEX idx_production_date (production_date),
  INDEX idx_material_id (material_id)
) COMMENT '중간품 LOT (샤링, 프레스 등)';
```

**제약사항**:
- `material_id` 필수 (원자재 추적성)
- `lot_no` 절대 삭제/재사용 금지
- `assembly_level = 0` (조립품은 assembly_lots 사용)

---

#### 2.2 assembly_lots (조립품 LOT)
```sql
CREATE TABLE assembly_lots (
  id INT PRIMARY KEY AUTO_INCREMENT,
  lot_no VARCHAR(50) UNIQUE NOT NULL COMMENT 'LOT 번호 (추적 키)',
  part_id INT NOT NULL COMMENT '품번 ID (조립품)',
  assembly_date DATE NOT NULL COMMENT '조립일자',
  quantity INT NOT NULL COMMENT '수량',
  worker_name VARCHAR(50) COMMENT '작업자명',
  qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
  assembly_level INT DEFAULT 1 COMMENT '조립 깊이 (자동 계산)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (part_id) REFERENCES parts(id),
  INDEX idx_lot_no (lot_no),
  INDEX idx_part_id (part_id),
  INDEX idx_assembly_date (assembly_date),
  INDEX idx_assembly_level (assembly_level)
) COMMENT '조립품 LOT';
```

**assembly_level 계산**:
- 1단계 조립품: 중간품만 사용 (level = 1)
- 2단계 조립품: 1단계 조립품 사용 (level = 2)
- 자동 계산 트리거로 관리

---

#### 2.3 assembly_components (조립품 구성)
```sql
CREATE TABLE assembly_components (
  id INT PRIMARY KEY AUTO_INCREMENT,
  assembly_lot_id INT NOT NULL COMMENT '조립품 LOT ID',
  component_lot_id INT COMMENT '중간품 LOT ID (중간품인 경우)',
  component_assembly_lot_id INT COMMENT '하위 조립품 LOT ID (조립품인 경우)',
  quantity INT NOT NULL COMMENT '투입 수량',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assembly_lot_id) REFERENCES assembly_lots(id),
  FOREIGN KEY (component_lot_id) REFERENCES lots(id),
  FOREIGN KEY (component_assembly_lot_id) REFERENCES assembly_lots(id),
  INDEX idx_assembly_lot_id (assembly_lot_id),
  INDEX idx_component_lot_id (component_lot_id),
  INDEX idx_component_assembly_lot_id (component_assembly_lot_id),
  CHECK (
    (component_lot_id IS NOT NULL AND component_assembly_lot_id IS NULL) OR
    (component_lot_id IS NULL AND component_assembly_lot_id IS NOT NULL)
  )
) COMMENT '조립품 구성 요소 (BOM)';
```

**제약사항**:
- `component_lot_id`와 `component_assembly_lot_id` 중 하나만 NOT NULL
- 중간품 또는 하위 조립품 중 하나만 선택

---

### 3. RFID 추적 테이블 (3개)

#### 3.1 rfid_tags (RFID 태그)
```sql
CREATE TABLE rfid_tags (
  id INT PRIMARY KEY AUTO_INCREMENT,
  epc VARCHAR(100) UNIQUE NOT NULL COMMENT 'EPC 코드',
  tag_type ENUM('PALLET', 'PRODUCT', 'OTHER') DEFAULT 'PALLET',
  is_active BOOLEAN DEFAULT TRUE COMMENT '활성 여부',
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deregistered_at TIMESTAMP NULL COMMENT '등록 해제 시각',
  INDEX idx_epc (epc),
  INDEX idx_is_active (is_active)
) COMMENT 'RFID 태그 마스터';
```

---

#### 3.2 pallets (팔레트)
```sql
CREATE TABLE pallets (
  id INT PRIMARY KEY AUTO_INCREMENT,
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
  lot_id INT COMMENT '중간품 LOT ID',
  assembly_lot_id INT COMMENT '조립품 LOT ID',
  current_process_id INT COMMENT '현재 공정 ID',
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (lot_id) REFERENCES lots(id),
  FOREIGN KEY (assembly_lot_id) REFERENCES assembly_lots(id),
  FOREIGN KEY (current_process_id) REFERENCES processes(id),
  INDEX idx_rfid_epc (rfid_epc),
  INDEX idx_status (status),
  INDEX idx_lot_id (lot_id),
  INDEX idx_assembly_lot_id (assembly_lot_id),
  CHECK (
    (lot_id IS NOT NULL AND assembly_lot_id IS NULL) OR
    (lot_id IS NULL AND assembly_lot_id IS NOT NULL) OR
    (lot_id IS NULL AND assembly_lot_id IS NULL)
  )
) COMMENT '팔레트 (RFID 부착)';
```

**상태 전이 규칙**:
- 상세 내용은 `pallet-state-machine.md` 참조

---

#### 3.3 pallet_histories (팔레트 이력)
```sql
CREATE TABLE pallet_histories (
  id INT PRIMARY KEY AUTO_INCREMENT,
  pallet_id INT NOT NULL COMMENT '팔레트 ID',
  previous_status VARCHAR(20) NOT NULL COMMENT '이전 상태',
  new_status VARCHAR(20) NOT NULL COMMENT '새 상태',
  process_id INT COMMENT '공정 ID',
  location_type VARCHAR(20) COMMENT '위치 타입',
  reader_location_id INT COMMENT '리더기 위치 ID',
  scan_time TIMESTAMP NOT NULL COMMENT '스캔 시각',
  notes TEXT COMMENT '비고 (FIFO 위반 등)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (pallet_id) REFERENCES pallets(id),
  FOREIGN KEY (process_id) REFERENCES processes(id),
  FOREIGN KEY (reader_location_id) REFERENCES rfid_reader_locations(id),
  INDEX idx_pallet_id (pallet_id),
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
  COALESCE(l.lot_no, al.lot_no) AS lot_no,
  COALESCE(lp.part_number, alp.part_number) AS part_number,
  COALESCE(lp.part_name, alp.part_name) AS part_name,
  pr.process_name AS current_process,
  p.updated_at
FROM pallets p
LEFT JOIN lots l ON p.lot_id = l.id
LEFT JOIN assembly_lots al ON p.assembly_lot_id = al.id
LEFT JOIN parts lp ON l.part_id = lp.id
LEFT JOIN parts alp ON al.part_id = alp.id
LEFT JOIN processes pr ON p.current_process_id = pr.id;
```

---

### 2. v_stock_inventory (재고 현황)
```sql
CREATE VIEW v_stock_inventory AS
SELECT 
  p.part_number,
  p.part_name,
  pr.process_name,
  l.lot_no,
  l.production_date,
  DATEDIFF(CURDATE(), l.production_date) AS days_old,
  COUNT(pal.id) AS pallet_count,
  SUM(l.quantity) AS total_quantity
FROM pallets pal
INNER JOIN lots l ON pal.lot_id = l.id
INNER JOIN parts p ON l.part_id = p.id
INNER JOIN processes pr ON l.process_id = pr.id
WHERE pal.status = 'Stock'
GROUP BY p.part_number, pr.process_name, l.lot_no, l.production_date
ORDER BY l.production_date ASC;
```

---

### 3. v_material_forward_trace (정방향 추적)
```sql
CREATE VIEW v_material_forward_trace AS
SELECT 
  rm.coil_number,
  rm.material_name,
  l.lot_no AS intermediate_lot,
  lp.part_number AS intermediate_part,
  ac.assembly_lot_id,
  al.lot_no AS assembly_lot,
  alp.part_number AS assembly_part
FROM raw_materials rm
LEFT JOIN lots l ON rm.id = l.material_id
LEFT JOIN parts lp ON l.part_id = lp.id
LEFT JOIN assembly_components ac ON l.id = ac.component_lot_id
LEFT JOIN assembly_lots al ON ac.assembly_lot_id = al.id
LEFT JOIN parts alp ON al.part_id = alp.id;
```

---

### 4. v_product_backward_trace (역방향 추적)
```sql
CREATE VIEW v_product_backward_trace AS
SELECT 
  al.lot_no AS assembly_lot,
  alp.part_number AS assembly_part,
  ac.component_lot_id,
  l.lot_no AS component_lot,
  lp.part_number AS component_part,
  rm.coil_number,
  rm.material_name
FROM assembly_lots al
INNER JOIN parts alp ON al.part_id = alp.id
LEFT JOIN assembly_components ac ON al.id = ac.assembly_lot_id
LEFT JOIN lots l ON ac.component_lot_id = l.id
LEFT JOIN parts lp ON l.part_id = lp.id
LEFT JOIN raw_materials rm ON l.material_id = rm.id;
```

---

## 트리거 (Triggers)

### 1. assembly_level 자동 계산
```sql
DELIMITER //

CREATE TRIGGER trg_calculate_assembly_level
AFTER INSERT ON assembly_components
FOR EACH ROW
BEGIN
  DECLARE max_level INT DEFAULT 0;
  
  -- 중간품 구성 요소의 최대 레벨 찾기
  IF NEW.component_lot_id IS NOT NULL THEN
    SELECT COALESCE(MAX(l.assembly_level), 0) INTO max_level
    FROM assembly_components ac
    INNER JOIN lots l ON ac.component_lot_id = l.id
    WHERE ac.assembly_lot_id = NEW.assembly_lot_id;
  END IF;
  
  -- 하위 조립품 구성 요소의 최대 레벨 찾기
  IF NEW.component_assembly_lot_id IS NOT NULL THEN
    SELECT COALESCE(MAX(al.assembly_level), 0) INTO max_level
    FROM assembly_components ac
    INNER JOIN assembly_lots al ON ac.component_assembly_lot_id = al.id
    WHERE ac.assembly_lot_id = NEW.assembly_lot_id;
  END IF;
  
  -- assembly_level 업데이트 (최대 레벨 + 1)
  UPDATE assembly_lots
  SET assembly_level = max_level + 1
  WHERE id = NEW.assembly_lot_id;
END //

DELIMITER ;
```

---

## 인덱스 전략

### 검색 최적화
- `lot_no`, `coil_number`, `pallet_no`: UNIQUE 인덱스 (추적 키)
- `production_date`, `assembly_date`: 범위 검색용
- `status`, `is_active`: 필터링용

### 조인 최적화
- 모든 Foreign Key에 인덱스 자동 생성
- 복합 인덱스: `(process_id, location_type)`

---

## 데이터 무결성 규칙

### 1. 추적 키 보호
```sql
-- 절대 삭제 금지
DELETE FROM raw_materials WHERE id = ?;  -- ❌ 금지
DELETE FROM lots WHERE id = ?;           -- ❌ 금지
DELETE FROM pallets WHERE id = ?;        -- ❌ 금지
DELETE FROM pallet_histories WHERE id = ?; -- ❌ 금지
```

### 2. LOT 연결 규칙
- 중간품 LOT: `material_id` 필수
- 팔레트: `lot_id` 또는 `assembly_lot_id` 중 하나만

### 3. 상태 전이 검증
- 애플리케이션 레벨에서 검증 (StateMachine)

---

## 백업 및 복구

### 백업
```bash
# 전체 백업
docker exec ajin-db mysqldump -u root -p ajin_rfid > backup.sql

# 테이블별 백업
docker exec ajin-db mysqldump -u root -p ajin_rfid pallet_histories > histories.sql
```

### 복구
```bash
docker exec -i ajin-db mysql -u root -p ajin_rfid < backup.sql
```

---

## 성능 최적화

### 1. 인덱스 모니터링
```sql
-- 사용되지 않는 인덱스 확인
SELECT * FROM sys.schema_unused_indexes;
```

### 2. 쿼리 최적화
```sql
-- EXPLAIN으로 실행 계획 확인
EXPLAIN SELECT * FROM v_pallet_status WHERE status = 'Stock';
```

### 3. 파티셔닝 (선택 사항)
```sql
-- pallet_histories를 월별로 파티셔닝
ALTER TABLE pallet_histories
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
  PARTITION p202511 VALUES LESS THAN (202512),
  PARTITION p202512 VALUES LESS THAN (202601),
  ...
);
```

---

## 참고 문서
- 데이터베이스 아키텍처: `database-architecture.md`
- 팔레트 상태 기계: `pallet-state-machine.md`
- 시스템 명세: `../.specify/specs/rfid-logistics-tracking-system.md`
