-- 품목(Items) 샘플 데이터
-- 원자재(RAW), 재공품(WIP), 완제품(PRODUCT)

-- Character set 설정 (한글 깨짐 방지)
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;
SET CHARACTER_SET_CONNECTION = utf8mb4;
SET CHARACTER_SET_RESULTS = utf8mb4;

-- 기존 샘플 데이터 삭제 (중복 방지)
DELETE FROM items WHERE item_code LIKE 'STEEL-%'
   OR item_code LIKE 'AL-%'
   OR item_code LIKE 'STS-%'
   OR item_code LIKE 'PP-%'
   OR item_code LIKE 'ABS-%'
   OR item_code LIKE '71412-%'
   OR item_code LIKE '71413-%'
   OR item_code LIKE '71420-%'
   OR item_code LIKE '71421-%'
   OR item_code LIKE '71430-%'
   OR item_code LIKE '71431-%'
   OR item_code LIKE '71440-%'
   OR item_code LIKE '76211-%'
   OR item_code LIKE '76212-%'
   OR item_code LIKE '77211-%'
   OR item_code LIKE '77212-%'
   OR item_code LIKE '77300-%'
   OR item_code LIKE '67110-%'
   OR item_code LIKE '76801-%'
   OR item_code LIKE '76802-%'
   OR item_code LIKE '64710-%'
   OR item_code LIKE '64720-%';

-- ============================================
-- 원자재 (RAW)
-- ============================================

-- 강판 (철강)
INSERT INTO items (item_code, item_name, item_type, unit, spec, vehicle_model, default_supplier, is_active) VALUES
('STEEL-SPCC-1.6T', 'SPCC 냉연강판 1.6T', 'RAW', 'KG', '1.6T, 1000x2000mm', NULL, '포스코', TRUE),
('STEEL-SPCC-2.0T', 'SPCC 냉연강판 2.0T', 'RAW', 'KG', '2.0T, 1000x2000mm', NULL, '포스코', TRUE),
('STEEL-SPHC-1.8T', 'SPHC 열연강판 1.8T', 'RAW', 'KG', '1.8T, 1000x2000mm', NULL, '현대제철', TRUE),
('STEEL-SPHC-2.3T', 'SPHC 열연강판 2.3T', 'RAW', 'KG', '2.3T, 1000x2000mm', NULL, '현대제철', TRUE),

-- 알루미늄
('AL-5052-1.5T', '알루미늄 5052 1.5T', 'RAW', 'KG', '1.5T, 1000x2000mm', NULL, '한국알루미늄', TRUE),
('AL-6061-2.0T', '알루미늄 6061 2.0T', 'RAW', 'KG', '2.0T, 1000x2000mm', NULL, '한국알루미늄', TRUE),

-- 스테인리스
('STS-304-1.2T', '스테인리스 304 1.2T', 'RAW', 'KG', '1.2T, 1000x2000mm', NULL, '포스코', TRUE),
('STS-430-1.5T', '스테인리스 430 1.5T', 'RAW', 'KG', '1.5T, 1000x2000mm', NULL, '포스코', TRUE),

-- 수지/플라스틱 원재료
('PP-BLACK', 'PP 수지 블랙', 'RAW', 'KG', 'Pellet, Black', NULL, '롯데케미칼', TRUE),
('ABS-WHITE', 'ABS 수지 화이트', 'RAW', 'KG', 'Pellet, White', NULL, '롯데케미칼', TRUE);

-- ============================================
-- 재공품 (WIP) - 중간 가공품
-- ============================================

-- 샤링 공정 (Shearing) 결과물
INSERT INTO items (item_code, item_name, item_type, unit, spec, vehicle_model, is_active) VALUES
('71412-T6000S-SH', 'PNL-FR DR INR LH (샤링)', 'WIP', 'EA', 'LH, 샤링완료', 'JX1', TRUE),
('71413-T6000S-SH', 'PNL-FR DR INR RH (샤링)', 'WIP', 'EA', 'RH, 샤링완료', 'JX1', TRUE),
('71420-T5000-SH', 'PNL-FR DR OTR LH (샤링)', 'WIP', 'EA', 'LH, 샤링완료', 'K9', TRUE),
('71421-T5000-SH', 'PNL-FR DR OTR RH (샤링)', 'WIP', 'EA', 'RH, 샤링완료', 'K9', TRUE),

-- 프레스 공정 (Press) 결과물
('71412-T6000S-PR', 'PNL-FR DR INR LH (프레스)', 'WIP', 'EA', 'LH, 프레스완료', 'JX1', TRUE),
('71413-T6000S-PR', 'PNL-FR DR INR RH (프레스)', 'WIP', 'EA', 'RH, 프레스완료', 'JX1', TRUE),
('71420-T5000-PR', 'PNL-FR DR OTR LH (프레스)', 'WIP', 'EA', 'LH, 프레스완료', 'K9', TRUE),
('71421-T5000-PR', 'PNL-FR DR OTR RH (프레스)', 'WIP', 'EA', 'RH, 프레스완료', 'K9', TRUE),

-- 용접 공정 결과물
('71430-WD-LH', 'REINF-FR DR LH (용접)', 'WIP', 'EA', 'LH, 용접완료', 'JX1', TRUE),
('71431-WD-RH', 'REINF-FR DR RH (용접)', 'WIP', 'EA', 'RH, 용접완료', 'JX1', TRUE),

-- 도장 전 준비품
('71440-PREP', 'ASSY-DR MODULE (도장전)', 'WIP', 'EA', '조립완료, 도장대기', 'JX1', TRUE);

-- ============================================
-- 완제품 (PRODUCT) - 최종 조립품
-- ============================================

-- 프론트 도어 모듈 (Front Door Module)
INSERT INTO items (item_code, item_name, item_type, unit, spec, vehicle_model, is_active) VALUES
('76211-GI000', 'ASSY-FR DR MODULE LH', 'PRODUCT', 'EA', 'LH, 완제품', 'JX1', TRUE),
('76212-GI000', 'ASSY-FR DR MODULE RH', 'PRODUCT', 'EA', 'RH, 완제품', 'JX1', TRUE),

-- K9 프론트 도어 모듈
('76211-K9000', 'ASSY-FR DR MODULE LH K9', 'PRODUCT', 'EA', 'LH, K9 전용', 'K9', TRUE),
('76212-K9000', 'ASSY-FR DR MODULE RH K9', 'PRODUCT', 'EA', 'RH, K9 전용', 'K9', TRUE),

-- 리어 도어 모듈 (Rear Door Module)
('77211-GI000', 'ASSY-RR DR MODULE LH', 'PRODUCT', 'EA', 'LH, 완제품', 'JX1', TRUE),
('77212-GI000', 'ASSY-RR DR MODULE RH', 'PRODUCT', 'EA', 'RH, 완제품', 'JX1', TRUE),

-- 테일게이트 모듈 (Tailgate Module)
('77300-GI000', 'ASSY-TAILGATE MODULE', 'PRODUCT', 'EA', '완제품', 'JX1', TRUE),

-- 루프 패널 (Roof Panel)
('67110-NE000', 'ASSY-ROOF PANEL', 'PRODUCT', 'EA', '완제품', 'NE', TRUE),

-- 사이드 실 패널
('76801-GI000', 'PNL-SIDE SILL LH', 'PRODUCT', 'EA', 'LH, 완제품', 'JX1', TRUE),
('76802-GI000', 'PNL-SIDE SILL RH', 'PRODUCT', 'EA', 'RH, 완제품', 'JX1', TRUE),

-- 크로스 멤버 (Cross Member)
('64710-GI000', 'MBR-CROSS FR', 'PRODUCT', 'EA', '완제품', 'JX1', TRUE),
('64720-GI000', 'MBR-CROSS RR', 'PRODUCT', 'EA', '완제품', 'JX1', TRUE);

-- ============================================
-- 샘플 데이터 요약
-- ============================================
/*
원자재 (RAW): 10개
- 강판 4종 (SPCC, SPHC)
- 알루미늄 2종
- 스테인리스 2종
- 수지/플라스틱 2종

재공품 (WIP): 11개
- 샤링 공정품 4종
- 프레스 공정품 4종
- 용접 공정품 2종
- 도장 전 준비품 1종

완제품 (PRODUCT): 12개
- 프론트 도어 모듈 4종
- 리어 도어 모듈 2종
- 테일게이트 모듈 1종
- 루프 패널 1종
- 사이드 실 패널 2종
- 크로스 멤버 2종

총 33개 품목
*/
