-- 아진산업 PBL - 차체 부품 제조 이력 및 물류 관리 시스템
-- RFID 기반 팔레트 추적 시스템 데이터베이스 스키마
-- 정규화 버전 (7개 테이블)

-- Character set 설정 (한글 깨짐 방지)
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;
SET CHARACTER_SET_CONNECTION = utf8mb4;
SET CHARACTER_SET_RESULTS = utf8mb4;

-- ============================================
-- 마스터 테이블 (3개)
-- ============================================

-- 1. 통합 품목 마스터 (원자재, 재공품, 완제품)
CREATE TABLE items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_code VARCHAR(50) NOT NULL UNIQUE COMMENT '품번 또는 원자재코드 (고유)',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '통합 품목 마스터 (원자재, 재공품, 완제품)';

-- 2. 공정 마스터
CREATE TABLE processes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    process_code VARCHAR(20) UNIQUE NOT NULL COMMENT '공정 코드',
    process_name VARCHAR(50) NOT NULL COMMENT '공정명',
    process_order INT NOT NULL COMMENT '공정 순서',
    production_line VARCHAR(50) COMMENT '생산 라인',
    allowed_item_types VARCHAR(100) COMMENT '허용 아이템 타입 (RAW,WIP,PRODUCT 쉼표 구분)',
    is_first_process BOOLEAN DEFAULT FALSE COMMENT '첫 공정 여부 (빈 팔레트 → 바로 생산)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_process_order (process_order),
    INDEX idx_process_code (process_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '공정 마스터';

-- 3. RFID 리더기 위치 마스터
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT 'RFID 리더기 위치 매핑';

-- ============================================
-- LOT 관리 테이블 (2개)
-- ============================================

-- 4. 통합 LOT 관리 (원자재, 중간품, 완제품 모두 포함)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '통합 LOT 관리 (원자재, 중간품, 완제품 모두 포함)';

-- 5. LOT 족보 (투입-산출 관계, 추적성 핵심)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT 'LOT 족보 (투입-산출 관계, 추적성 핵심)';

-- ============================================
-- RFID 추적 테이블 (2개) - rfid_tags를 pallets에 통합
-- ============================================

-- 6. 팔레트 (RFID 태그 통합 - 기존 rfid_tags 테이블 흡수)
CREATE TABLE pallets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    pallet_no VARCHAR(50) UNIQUE NOT NULL COMMENT '팔레트 번호',
    rfid_epc VARCHAR(100) UNIQUE COMMENT 'RFID EPC 코드 (1:1 매핑)',
    lot_id BIGINT COMMENT '연결된 LOT ID',
    status ENUM('Generated', 'Empty', 'Stock', 'Consuming', 'Producing', 'Finished', 'Deregistered', 'Hold', 'Defect') DEFAULT 'Generated' COMMENT '팔레트 상태 (9가지)',
    tag_status ENUM('AVAILABLE', 'IN_USE', 'DAMAGED') DEFAULT 'AVAILABLE' COMMENT 'RFID 태그 상태 (기존 rfid_tags.status 통합)',
    current_process_id BIGINT COMMENT '현재 공정',
    quantity INT DEFAULT 0 COMMENT '현재 적재 수량',
    tag_registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'RFID 태그 등록 시각',
    tag_deregistered_at TIMESTAMP NULL COMMENT 'RFID 태그 해제 시각',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lot_id) REFERENCES lots(id),
    FOREIGN KEY (current_process_id) REFERENCES processes(id),
    INDEX idx_pallet_no (pallet_no),
    INDEX idx_rfid_epc (rfid_epc),
    INDEX idx_status (status),
    INDEX idx_tag_status (tag_status),
    INDEX idx_lot (lot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '팔레트 - RFID 태그 통합 관리 (기존 rfid_tags 흡수)';

-- 7. 팔레트 이력 (불변 로그)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '팔레트 상태 변경 이력 (불변 로그)';

-- (rfid_tags 테이블 삭제됨 - pallets.tag_status로 통합)

-- ============================================
-- 초기 데이터 INSERT
-- ============================================

-- Character set 재확인 (INSERT 전)
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;
SET CHARACTER_SET_CONNECTION = utf8mb4;
SET CHARACTER_SET_RESULTS = utf8mb4;

-- 공정 마스터 데이터
INSERT INTO processes (process_code, process_name, process_order, production_line) VALUES
('RECEIVING', '입고', 0, '입고장'),
('SHEARING', '샤링', 1, '400T'),
('PRESS', '프레스', 2, '1500T'),
('ASSEMBLY', '조립', 3, '조립 라인 1'),
('SHIPPING', '출하', 4, '출하장');

-- ============================================
-- 사용자 테이블 (추가)
-- ============================================

-- 8. 사용자 관리
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '사용자 아이디',
    hashed_password VARCHAR(255) NOT NULL COMMENT '해싱된 비밀번호',
    full_name VARCHAR(100) COMMENT '사용자 실명',
    role VARCHAR(20) DEFAULT 'USER' COMMENT '권한 (ADMIN, USER)',
    is_active BOOLEAN DEFAULT TRUE,
    permissions JSON COMMENT '사용자 세부 권한 (JSON)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT '사용자 관리';

-- 기본 Admin 사용자 생성
-- 비밀번호: admin123 (bcrypt 해싱됨)
INSERT INTO users (username, hashed_password, full_name, role, is_active, permissions) VALUES
('admin', '$2b$12$13zfEGam1CcnGzYS6cfGVe30h8eAbWrwv.JirjRp1tzem9Y.aVavi', 'Administrator', 'ADMIN', TRUE, '{}');

-- ============================================
-- 뷰 (Views)
-- ============================================

-- 1. 팔레트 현황 뷰
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

-- 2. 재고 현황 뷰 (FIFO용)
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
JOIN lots l ON p.lot_id = l.id
JOIN items i ON l.item_id = i.id
LEFT JOIN processes pr ON l.process_id = pr.id
WHERE p.status = 'Stock'
GROUP BY i.item_code, i.item_name, i.item_type, pr.process_name, l.lot_number, l.production_date
ORDER BY l.production_date;

-- 3. 정방향 추적 뷰 (원자재 → 완제품)
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

-- 4. 역방향 추적 뷰 (완제품 → 원자재)
CREATE VIEW v_lot_backward_trace AS
WITH RECURSIVE trace AS (
    -- Base case: 완제품 LOT
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

-- 5. LOT 전체 족보 뷰
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

-- ============================================
-- FIFO 검증 함수
-- ============================================

DELIMITER //

CREATE FUNCTION check_fifo(
    p_item_id BIGINT,
    p_production_date DATE
) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE older_stock_count INT;
    
    -- 같은 품목에서 더 오래된 재고가 있는지 확인
    SELECT COUNT(*) INTO older_stock_count
    FROM pallets p
    JOIN lots l ON p.lot_id = l.id
    WHERE l.item_id = p_item_id
      AND l.production_date < p_production_date
      AND p.status = 'Stock';
    
    -- 더 오래된 재고가 없으면 TRUE (FIFO 준수), 있으면 FALSE (FIFO 위반)
    RETURN older_stock_count = 0;
END //

DELIMITER ;

-- ============================================
-- 스키마 요약
-- ============================================

/*
핵심 테이블 7개:

마스터 데이터 (3개):
1. items - 통합 품목 마스터 (원자재, 재공품, 완제품)
2. processes - 공정 마스터
3. rfid_reader_locations - RFID 리더기 위치 매핑

LOT 관리 (2개):
4. lots - 통합 LOT 관리
5. lot_genealogy - LOT 족보 (추적성 핵심)

RFID 추적 (2개):
6. pallets - 팔레트 + RFID 태그 통합 관리 (tag_status 포함)
7. pallet_histories - 팔레트 이력 (불변 로그)

※ rfid_tags 테이블은 pallets에 통합됨 (1:1 관계, 동일 라이프사이클)

추적성 뷰 5개:
- v_pallet_status: 팔레트 현황
- v_stock_inventory: 재고 현황 (FIFO)
- v_lot_forward_trace: 정방향 추적
- v_lot_backward_trace: 역방향 추적
- v_lot_full_genealogy: 전체 족보

핵심 개념:
- 품목(Item): "이건 뭐야?" - 제품의 종류/규격 (마스터)
- LOT: "이건 어떤 거야?" - 실물 인스턴스 (트랜잭션)
- lot_genealogy: 모든 공정 간 부모-자식 관계 기록

원자재 입고 워크플로우 (RFID 불필요):
1. 품목 등록 (items에 RAW 타입)
2. 입고 시 LOT 생성 (lots에 lot_number 자동 생성)
3. 샤링 투입 시 lot_genealogy에 관계 기록
*/

-- -- 스키마 정의 완료

-- ('SHEARING', '샤링', 1, '400T'),
-- 샤링 공정 리더기 등록
INSERT INTO rfid_reader_locations (port_name, process_id, location_type, description) 
SELECT 'COM00_GEN', id, 'IN', '샤링 공정 - 입고 리더기' FROM processes WHERE process_code = 'SHEARING'
UNION ALL
SELECT 'COM00_REG', id, 'OUT', '샤링 공정 - 출고 리더기' FROM processes WHERE process_code = 'SHEARING';

-- 테스트 데이터 삽입
-- 테스트 품목 생성
INSERT INTO items (item_code, item_name, item_type, unit) 
VALUES ('TEST-SHEARING-001', '샤링 테스트 제품', 'WIP', 'EA');

-- LOT 생성 (바코드와 RFID EPC 동일하게)
INSERT INTO lots (item_id, barcode, lot_number, production_date, quantity, initial_quantity, process_id) 
SELECT id, '1D886511091080', 'LOT-TEST-001', CURDATE(), 100, 100, 
       (SELECT id FROM processes WHERE process_code = 'SHEARING')
FROM items WHERE item_code = 'TEST-SHEARING-001';

-- 팔레트 생성 (RFID EPC 설정)
INSERT INTO pallets (pallet_no, lot_id, rfid_epc, current_process_id, status) 
SELECT 'PLT-TEST-001', l.id, '1D886511091080', 
       (SELECT id FROM processes WHERE process_code = 'SHEARING'), 'Empty'
FROM lots l WHERE l.lot_number = 'LOT-TEST-001';