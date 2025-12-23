INSERT INTO processes (process_code, process_name, process_order, production_line) VALUES
('RECEIVING', '입고', 0, '입고장'),
('SHEARING', '샤링', 1, '400T'),
('PRESS', '프레스', 2, '1500T'),
('ASSEMBLY', '조립', 3, '조립 라인 1'),
('SHIPPING', '출하', 4, '출하장');

-- rfid 연결용 샘플 데이터
INSERT INTO rfid_reader_locations 
(port_name, process_id, location_type, description, is_active) 
VALUES 
('COM00_REG', (SELECT id FROM processes WHERE process_code = 'RECEIVING'), 'IN', '입고 자재 태그 등록 리더기', TRUE),
('COM00_GEN', (SELECT id FROM processes WHERE process_code = 'SHIPPING'), 'FINISH', '완제품 정보 생성 및 출하 리더기', TRUE);

