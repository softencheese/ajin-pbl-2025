-- 아진산업 PBL - 차체 부품 제조 이력 및 물류 관리 시스템
-- RFID 기반 팔레트 추적 시스템 데이터베이스 스키마

-- 1. 원자재 마스터
CREATE TABLE raw_materials (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    coil_number VARCHAR(50) NOT NULL UNIQUE COMMENT '코일 번호 (C059461B) - 원자재 추적 키',
    material_name VARCHAR(100) NOT NULL COMMENT '원자재명',
    supplier VARCHAR(100) COMMENT '공급업체',
    receipt_date DATE COMMENT '입고일자',
    qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_coil_number (coil_number)
) COMMENT '원자재 마스터 - 코일 번호로 추적';

-- 2. 품번 마스터 (부품 정보)
CREATE TABLE parts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    part_number VARCHAR(50) NOT NULL UNIQUE COMMENT '품번 (71412-T6000S, 76211-GI000)',
    part_name VARCHAR(100) NOT NULL COMMENT '품명 (PNL-FR DR INR, LH)',
    part_spec VARCHAR(200) COMMENT '부품 사양/메모 (LH/RH, 색상, 위치, 재질 등)',
    vehicle_model VARCHAR(50) COMMENT '차종 (JX1, NE)',
    is_assembly BOOLEAN DEFAULT FALSE COMMENT '조립품 여부 (TRUE: 조립품, FALSE: 중간품)',
    is_final_product BOOLEAN DEFAULT FALSE COMMENT '최종 완제품 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_part_number (part_number),
    INDEX idx_vehicle_model (vehicle_model),
    INDEX idx_assembly (is_assembly),
    INDEX idx_final (is_final_product)
) COMMENT '품번 마스터';

-- 3. 공정 마스터
CREATE TABLE processes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    process_code VARCHAR(50) NOT NULL UNIQUE COMMENT '공정코드',
    process_name VARCHAR(50) NOT NULL COMMENT '공정명 (샤링, 프레스, 조립, 출하)',
    process_order INT NOT NULL COMMENT '공정 순서',
    production_line VARCHAR(50) COMMENT '생산 라인 (400T, 1500T)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) COMMENT '공정 마스터';

-- 4. LOT (작업전표 정보 - 중간품 전용)
CREATE TABLE lots (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    lot_no VARCHAR(50) NOT NULL UNIQUE COMMENT 'LOT 번호 (바코드)',
    part_id BIGINT NOT NULL COMMENT '품번 ID',
    process_id BIGINT NOT NULL COMMENT '공정 ID',
    material_id BIGINT COMMENT '원자재 ID (원자재 추적용)',
    assembly_level INT DEFAULT 0 COMMENT '조립 레벨 (중간품은 항상 0)',
    quantity INT NOT NULL COMMENT '수량 (400 EA, 40 EA)',
    production_date DATE NOT NULL COMMENT '생산일자 (25-04-26, 25-10-17)',
    worker_name VARCHAR(50) COMMENT '작업자 (최영일, 전재민)',
    qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (material_id) REFERENCES raw_materials(id),
    INDEX idx_production_date (production_date),
    INDEX idx_part_process (part_id, process_id),
    INDEX idx_material (material_id)
) COMMENT 'LOT (작업전표) - 샤링/프레스 등 공정 후 생성되는 중간품';

-- 5. 팔레트 (RFID 추적 단위)
CREATE TABLE pallets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    pallet_no VARCHAR(50) NOT NULL UNIQUE COMMENT '팔레트 번호',
    rfid_epc VARCHAR(100) UNIQUE COMMENT 'RFID EPC 코드',
    lot_id BIGINT COMMENT '연결된 중간품 LOT ID',
    assembly_lot_id BIGINT COMMENT '연결된 조립품 LOT ID',
    status VARCHAR(20) DEFAULT 'Generated' COMMENT '상태 (9가지)',
    current_process_id BIGINT COMMENT '현재 공정',
    quantity INT DEFAULT 0 COMMENT '현재 적재 수량',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lot_id) REFERENCES lots(id),
    FOREIGN KEY (current_process_id) REFERENCES processes(id),
    CHECK (status IN ('Generated', 'Empty', 'Stock', 'Consuming', 'Producing', 'Finished', 'Deregistered', 'Hold', 'Defect')),
    CHECK (
        (lot_id IS NOT NULL AND assembly_lot_id IS NULL) OR
        (lot_id IS NULL AND assembly_lot_id IS NOT NULL) OR
        (lot_id IS NULL AND assembly_lot_id IS NULL)
    ),
    INDEX idx_status (status),
    INDEX idx_lot (lot_id),
    INDEX idx_assembly_lot (assembly_lot_id)
) COMMENT '팔레트 - RFID 태그 매칭 및 상태 관리 (중간품 또는 조립품 적재)';

-- 6. 팔레트 이력 (모든 이동 기록)
CREATE TABLE pallet_histories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    pallet_id BIGINT NOT NULL COMMENT '팔레트 ID',
    lot_id BIGINT COMMENT '중간품 LOT ID',
    assembly_lot_id BIGINT COMMENT '조립품 LOT ID',
    process_id BIGINT COMMENT '공정 ID',
    location_type VARCHAR(20) COMMENT '위치 유형 (IN, OUT, HOLD, DEFECT, FINISH)',
    previous_status VARCHAR(20) COMMENT '이전 상태',
    current_status VARCHAR(20) NOT NULL COMMENT '현재 상태',
    event_type VARCHAR(50) NOT NULL COMMENT '이벤트 유형 (TAG_SCAN, STATUS_CHANGE)',
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '이벤트 발생 시간',
    worker_name VARCHAR(50) COMMENT '작업자',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pallet_id) REFERENCES pallets(id),
    FOREIGN KEY (lot_id) REFERENCES lots(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    INDEX idx_pallet_time (pallet_id, event_time),
    INDEX idx_event_time (event_time)
) COMMENT '팔레트 이력 - 모든 상태 변경 및 이동 기록';


-- 7. 조립품 LOT (반제품/완제품)
CREATE TABLE assembly_lots (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    lot_no VARCHAR(50) NOT NULL UNIQUE COMMENT '조립품 LOT 번호 (ASM-XXX)',
    part_id BIGINT NOT NULL COMMENT '조립품 품번 (parts.is_final_product로 최종 완제품 여부 확인)',
    assembly_level INT DEFAULT 0 COMMENT '조립 단계 (트리거로 자동 계산: 최대 하위레벨+1)',
    assembly_date DATE NOT NULL COMMENT '조립 완료일',
    quantity INT NOT NULL COMMENT '조립 수량 (목표 생산량)',
    worker_name VARCHAR(50) COMMENT '작업자',
    qc_passed BOOLEAN DEFAULT FALSE COMMENT 'QC 합격 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (part_id) REFERENCES parts(id),
    INDEX idx_assembly_level (assembly_level),
    INDEX idx_assembly_date (assembly_date)
) COMMENT '조립품 LOT - 반제품 및 완제품 (parts 테이블에서 최종 완제품 여부 확인)';

-- 7. 조립품 구성 요소 (투입된 중간품 또는 하위 조립품)
CREATE TABLE assembly_components (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    assembly_lot_id BIGINT NOT NULL COMMENT '조립품 LOT ID (완제품/반제품)',
    component_lot_id BIGINT COMMENT '투입된 중간품 LOT ID (lots 테이블)',
    component_assembly_id BIGINT COMMENT '투입된 하위 조립품 LOT ID (assembly_lots 테이블)',
    component_pallet_id BIGINT COMMENT '투입 팔레트',
    required_quantity_per_unit INT NOT NULL COMMENT '조립품 1개당 필요한 구성품 수량',
    total_consumed_quantity INT NOT NULL COMMENT '실제 총 소비 수량 (조립품수량 * 단위수량)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assembly_lot_id) REFERENCES assembly_lots(id),
    FOREIGN KEY (component_lot_id) REFERENCES lots(id),
    FOREIGN KEY (component_assembly_id) REFERENCES assembly_lots(id),
    FOREIGN KEY (component_pallet_id) REFERENCES pallets(id),
    CHECK (
        (component_lot_id IS NOT NULL AND component_assembly_id IS NULL) OR
        (component_lot_id IS NULL AND component_assembly_id IS NOT NULL)
    ),
    INDEX idx_assembly (assembly_lot_id),
    INDEX idx_component_lot (component_lot_id),
    INDEX idx_component_asm (component_assembly_id)
) COMMENT '조립품 구성 요소 - 단위당 소비량 및 총 소비량 관리';

-- FK 추가 (테이블 순서 의존성으로 나중에 추가)
ALTER TABLE pallets ADD CONSTRAINT fk_pallets_assembly_lot FOREIGN KEY (assembly_lot_id) REFERENCES assembly_lots(id);
ALTER TABLE pallet_histories ADD CONSTRAINT fk_pallet_histories_assembly_lot FOREIGN KEY (assembly_lot_id) REFERENCES assembly_lots(id);

-- 8. RFID 태그 (태그 자체 관리)
CREATE TABLE rfid_tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    epc VARCHAR(100) NOT NULL UNIQUE COMMENT 'RFID EPC 코드',
    status VARCHAR(20) DEFAULT 'AVAILABLE' COMMENT '상태 (AVAILABLE, IN_USE, DAMAGED)',
    current_pallet_id BIGINT COMMENT '현재 연결된 팔레트 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (current_pallet_id) REFERENCES pallets(id),
    CHECK (status IN ('AVAILABLE', 'IN_USE', 'DAMAGED'))
) COMMENT 'RFID 태그 관리';

-- 9. RFID 리더기 위치 마스터
CREATE TABLE rfid_reader_locations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    port_name VARCHAR(100) NOT NULL UNIQUE COMMENT '리더기 포트 식별자 (예: COM3, READER_01 등)',
    process_id BIGINT COMMENT '연결된 공정 ID (미등록 시 NULL)',
    location_type VARCHAR(20) COMMENT '위치 유형 (IN, OUT, HOLD, DEFECT, FINISH)',
    description VARCHAR(255) COMMENT '설명 (예: 프레스 1500T 투입구 리더기)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    last_scan_time TIMESTAMP NULL COMMENT '마지막 스캔 시간 (대시보드 조회용)',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (process_id) REFERENCES processes(id),
    CHECK (location_type IN ('IN', 'OUT', 'HOLD', 'DEFECT', 'FINISH')),
    INDEX idx_process_location (process_id, location_type)
) COMMENT '고정형 RFID 리더기와 공정 위치 매핑';

-- ============================================
-- 트리거 (assembly_level 자동 계산)
-- ============================================

DELIMITER $$

-- 조립품 구성 요소 추가 시 assembly_level 자동 계산
CREATE TRIGGER after_insert_assembly_component
AFTER INSERT ON assembly_components
FOR EACH ROW
BEGIN
    DECLARE max_component_level INT;
    
    -- 투입된 구성 요소 중 가장 높은 level 찾기
    SELECT COALESCE(MAX(
        CASE 
            WHEN ac.component_lot_id IS NOT NULL THEN l.assembly_level
            WHEN ac.component_assembly_id IS NOT NULL THEN al.assembly_level
            ELSE 0
        END
    ), 0) INTO max_component_level
    FROM assembly_components ac
    LEFT JOIN lots l ON ac.component_lot_id = l.id
    LEFT JOIN assembly_lots al ON ac.component_assembly_id = al.id
    WHERE ac.assembly_lot_id = NEW.assembly_lot_id;
    
    -- 현재 조립품의 레벨 = 최대 구성요소 레벨 + 1
    UPDATE assembly_lots 
    SET assembly_level = max_component_level + 1
    WHERE id = NEW.assembly_lot_id;
END$$

DELIMITER ;

-- ============================================
-- 초기 데이터 INSERT
-- ============================================

-- 공정 마스터 데이터
INSERT INTO processes (process_code, process_name, process_order, production_line) VALUES
('SHEARING', '샤링', 1, '400T'),
('PRESS', '프레스', 2, '1500T'),
('ASSEMBLY', '조립', 3, NULL),
('SHIPPING', '출하', 4, NULL);

-- ============================================
-- 뷰 생성
-- ============================================

-- 1. 팔레트 현황 뷰
CREATE VIEW v_pallet_status AS
SELECT 
    p.pallet_no,
    p.rfid_epc,
    p.status,
    p.quantity AS pallet_quantity,
    COALESCE(l.lot_no, al.lot_no) AS lot_no,
    CASE 
        WHEN l.id IS NOT NULL THEN '중간품'
        WHEN al.id IS NOT NULL THEN CONCAT('조립품(Lv', al.assembly_level, ')')
        ELSE NULL
    END AS lot_type,
    l.production_date,
    COALESCE(l.worker_name, al.worker_name) AS worker_name,
    COALESCE(l.qc_passed, al.qc_passed) AS qc_passed,
    pt.part_number,
    pt.part_name,
    pt.vehicle_model,
    pt.is_final_product,
    pr.process_name AS current_process,
    pr.production_line,
    rm.coil_number,
    rm.qc_passed AS material_qc_passed,
    p.updated_at
FROM pallets p
LEFT JOIN lots l ON p.lot_id = l.id
LEFT JOIN assembly_lots al ON p.assembly_lot_id = al.id
LEFT JOIN parts pt ON COALESCE(l.part_id, al.part_id) = pt.id
LEFT JOIN processes pr ON p.current_process_id = pr.id
LEFT JOIN raw_materials rm ON l.material_id = rm.id
WHERE p.status != 'Deregistered';

-- 2. 재고 현황 뷰 (Stock 상태, FIFO용)
CREATE VIEW v_stock_inventory AS
SELECT 
    pt.part_number,
    pt.part_name,
    pt.vehicle_model,
    pr.process_name,
    pr.production_line,
    l.production_date,
    COUNT(p.id) AS pallet_count,
    SUM(p.quantity) AS total_quantity,
    MIN(l.production_date) AS oldest_date,
    GROUP_CONCAT(l.lot_no ORDER BY l.production_date) AS lot_numbers
FROM pallets p
JOIN lots l ON p.lot_id = l.id
JOIN parts pt ON l.part_id = pt.id
JOIN processes pr ON l.process_id = pr.id
WHERE p.status = 'Stock'
GROUP BY pt.part_number, pt.part_name, pt.vehicle_model, pr.process_name, pr.production_line, l.production_date
ORDER BY oldest_date;

-- 3. 공정 이력 추적 뷰
CREATE VIEW v_pallet_trace AS
SELECT 
    ph.id,
    p.pallet_no,
    l.lot_no,
    pt.part_number,
    pt.vehicle_model,
    pr.process_name,
    pr.production_line,
    rm.coil_number,
    ph.location_type,
    ph.previous_status,
    ph.current_status,
    ph.event_type,
    ph.event_time,
    ph.worker_name
FROM pallet_histories ph
JOIN pallets p ON ph.pallet_id = p.id
LEFT JOIN lots l ON ph.lot_id = l.id
LEFT JOIN parts pt ON l.part_id = pt.id
LEFT JOIN processes pr ON ph.process_id = pr.id
LEFT JOIN raw_materials rm ON l.material_id = rm.id
ORDER BY ph.event_time DESC;

-- 4. 조립 추적 뷰 (완제품/반제품 → 투입된 구성 요소)
CREATE VIEW v_assembly_trace AS
SELECT 
    al.lot_no AS assembly_lot,
    al.quantity AS assembly_quantity,
    al.assembly_level,
    apt.is_final_product,
    apt.part_number AS assembly_part,
    apt.part_name AS assembly_name,
    CASE 
        WHEN ac.component_lot_id IS NOT NULL THEN l.lot_no
        WHEN ac.component_assembly_id IS NOT NULL THEN cal.lot_no
    END AS component_lot,
    CASE 
        WHEN ac.component_lot_id IS NOT NULL THEN lpt.part_number
        WHEN ac.component_assembly_id IS NOT NULL THEN capt.part_number
    END AS component_part,
    CASE 
        WHEN ac.component_lot_id IS NOT NULL THEN lpt.part_name
        WHEN ac.component_assembly_id IS NOT NULL THEN capt.part_name
    END AS component_name,
    CASE 
        WHEN ac.component_lot_id IS NOT NULL THEN '중간품(LOT)'
        WHEN ac.component_assembly_id IS NOT NULL THEN CONCAT('조립품(Level ', cal.assembly_level, ')')
    END AS component_type,
    ac.required_quantity_per_unit AS per_unit,
    ac.total_consumed_quantity AS total_consumed,
    al.assembly_date,
    al.worker_name,
    p.pallet_no AS component_pallet
FROM assembly_components ac
JOIN assembly_lots al ON ac.assembly_lot_id = al.id
JOIN parts apt ON al.part_id = apt.id
LEFT JOIN lots l ON ac.component_lot_id = l.id
LEFT JOIN parts lpt ON l.part_id = lpt.id
LEFT JOIN assembly_lots cal ON ac.component_assembly_id = cal.id
LEFT JOIN parts capt ON cal.part_id = capt.id
LEFT JOIN pallets p ON ac.component_pallet_id = p.id
ORDER BY al.assembly_level DESC, al.assembly_date DESC;

-- 5. 원자재 역추적 뷰 (불량 원자재 → 생산된 모든 제품)
CREATE VIEW v_material_forward_trace AS
SELECT 
    rm.coil_number,
    rm.material_name,
    rm.supplier,
    rm.qc_passed AS material_qc_passed,
    rm.receipt_date,
    l.lot_no,
    pt.part_number,
    pt.part_name,
    pt.vehicle_model,
    pr.process_name,
    pr.production_line,
    l.production_date,
    l.worker_name,
    l.qc_passed AS lot_qc_passed,
    p.pallet_no,
    p.status AS pallet_status
FROM raw_materials rm
JOIN lots l ON rm.id = l.material_id
JOIN parts pt ON l.part_id = pt.id
JOIN processes pr ON l.process_id = pr.id
LEFT JOIN pallets p ON l.id = p.lot_id
ORDER BY rm.coil_number, l.production_date;

-- 6. 제품 역추적 뷰 (불량 제품 → 사용된 원자재)
CREATE VIEW v_product_backward_trace AS
SELECT 
    l.lot_no,
    pt.part_number,
    pt.part_name,
    pt.vehicle_model,
    pr.process_name,
    pr.production_line,
    l.production_date,
    l.qc_passed AS lot_qc_passed,
    rm.coil_number,
    rm.material_name,
    rm.supplier,
    rm.receipt_date,
    rm.qc_passed AS material_qc_passed,
    p.pallet_no,
    p.status AS pallet_status
FROM lots l
JOIN parts pt ON l.part_id = pt.id
JOIN processes pr ON l.process_id = pr.id
LEFT JOIN raw_materials rm ON l.material_id = rm.id
LEFT JOIN pallets p ON l.id = p.lot_id
ORDER BY l.production_date DESC;

-- ============================================
-- FIFO 검증 함수 (선입선출 체크)
-- ============================================

DELIMITER //

CREATE FUNCTION check_fifo(
    p_part_id BIGINT,
    p_production_date DATE
) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE older_stock_count INT;
    
    -- 같은 품번에서 더 오래된 재고가 있는지 확인
    SELECT COUNT(*) INTO older_stock_count
    FROM pallets p
    JOIN lots l ON p.lot_id = l.id
    WHERE l.part_id = p_part_id
      AND l.production_date < p_production_date
      AND p.status = 'Stock';
    
    -- 더 오래된 재고가 없으면 TRUE (통과), 있으면 FALSE (실패)
    RETURN older_stock_count = 0;
END //

DELIMITER ;

-- ============================================
-- 코멘트 정리
-- ============================================

/*
핵심 테이블 10개:
1. raw_materials - 원자재 마스터 (코일 번호 추적)
2. parts - 품번 마스터
3. processes - 공정 마스터  
4. lots - 작업전표 (LOT) + 원자재 연결
5. pallets - RFID 팔레트
6. pallet_histories - 팔레트 이력
7. assembly_lots - 조립품 LOT (반제품/완제품)
8. assembly_components - 조립품 구성 요소
9. rfid_tags - RFID 태그
10. rfid_reader_locations - RFID 리더기 위치 마스터

핵심 흐름:
1. 원자재 입고 (코일 번호: C059461B)
2. 샤링 공정 → LOT 생성 (전표 1) + 원자재 연결
3. 프레스 공정 → LOT 생성 (전표 2) → Stock 상태
4. FIFO 검증 → 조립 공정 투입 → assembly_components 기록
5. 팔레트: Generated → Empty → Producing → Stock → Consuming → Finished → Deregistered

원자재 추적:
- 정방향: 불량 원자재(코일) → 해당 원자재로 생산된 모든 제품 (v_material_forward_trace)
- 역방향: 불량 제품 → 사용된 원자재 확인 (v_product_backward_trace)

RFID 리더기 위치 매핑:
- 각 고정형 RFID 리더기를 공정 및 위치 유형(IN/OUT/HOLD/DEFECT/FINISH)과 매핑
- 포트 식별자(COM3, IP:PORT 등)로 리더기를 식별하고 자동으로 공정 및 위치 판단
*/

