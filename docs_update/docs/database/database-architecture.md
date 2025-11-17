# 데이터베이스 아키텍처 상세 명세

## 개요
아진산업 PBL RFID 기반 팔레트 추적 시스템의 데이터베이스 구조 및 무결성 규칙

---

## 핵심 테이블 구조

### 마스터 데이터 (4개 테이블)

#### 1. 원자재 마스터 (raw_materials)
- **목적**: 코일 번호 기반 원자재 추적
- **주요 컬럼**: 
  - `coil_number` (VARCHAR, UNIQUE): 코일 번호 (예: C059461B)
  - `material_name`: 원자재명
  - `supplier`: 공급업체
  - `receipt_date`: 입고일자
  - `qc_passed`: QC 합격 여부

#### 2. 품번 마스터 (parts)
- **목적**: 품번 정보 관리
- **주요 컬럼**:
  - `part_number` (VARCHAR, UNIQUE): 품번 (예: 71412-T6000S)
  - `part_name`: 품명
  - `vehicle_model`: 차종
  - `is_assembly`: 조립품 여부
  - `is_final_product`: 최종 완제품 여부

#### 3. 공정 마스터 (processes)
- **목적**: 공정 정보 관리
- **주요 컬럼**:
  - `process_code` (VARCHAR, UNIQUE): 공정 코드
  - `process_name`: 공정명 (샤링, 프레스, 조립, 출하)
  - `process_order`: 공정 순서
  - `production_line`: 생산 라인

#### 4. RFID 리더기 위치 (rfid_reader_locations)
- **목적**: 리더기와 공정/위치 매핑
- **주요 컬럼**:
  - `port_name` (VARCHAR, UNIQUE): 리더기 포트 (예: COM3, 192.168.1.100:9001)
  - `process_id`: 연결된 공정 ID
  - `location_type`: 위치 유형 (IN, OUT, HOLD, DEFECT, FINISH)
  - `description`: 설명

---

### 생산 관리 데이터 (3개 테이블)

#### 5. 중간품 LOT (lots)
- **목적**: 작업전표 관리 및 원자재 추적
- **주요 컬럼**:
  - `lot_no` (VARCHAR, UNIQUE): LOT 번호 (바코드)
  - `part_id`: 품번 ID (FK)
  - `process_id`: 공정 ID (FK)
  - `material_id`: 원자재 ID (FK) - 코일 추적용
  - `assembly_level`: 항상 0 (중간품)
  - `quantity`: 수량
  - `production_date`: 생산일자
  - `worker_name`: 작업자
  - `qc_passed`: QC 합격 여부

#### 6. 조립품 LOT (assembly_lots)
- **목적**: 반제품 및 완제품 관리
- **주요 컬럼**:
  - `lot_no` (VARCHAR, UNIQUE): 조립품 LOT 번호
  - `part_id`: 조립품 품번 ID (FK)
  - `assembly_level`: 조립 레벨 (트리거 자동 계산)
  - `assembly_date`: 조립 완료일
  - `quantity`: 조립 수량
  - `worker_name`: 작업자
  - `qc_passed`: QC 합격 여부

#### 7. 조립품 구성 요소 (assembly_components)
- **목적**: 조립품에 투입된 구성품 추적
- **주요 컬럼**:
  - `assembly_lot_id`: 조립품 LOT ID (FK)
  - `component_lot_id`: 투입된 중간품 LOT ID (FK)
  - `component_assembly_id`: 투입된 하위 조립품 LOT ID (FK)
  - `component_pallet_id`: 투입 팔레트 ID (FK)
  - `required_quantity_per_unit`: 단위당 필요 수량
  - `total_consumed_quantity`: 총 소비 수량

---

### RFID 추적 데이터 (3개 테이블)

#### 8. 팔레트 (pallets)
- **목적**: RFID 태그 매칭 및 상태 관리
- **주요 컬럼**:
  - `pallet_no` (VARCHAR, UNIQUE): 팔레트 번호
  - `rfid_epc` (VARCHAR, UNIQUE): RFID EPC 코드 (1:1 매핑)
  - `lot_id`: 연결된 중간품 LOT ID (FK)
  - `assembly_lot_id`: 연결된 조립품 LOT ID (FK)
  - `status`: 팔레트 상태 (9가지)
  - `current_process_id`: 현재 공정 ID (FK)
  - `quantity`: 현재 적재 수량

**상태 흐름**:
- 중간품: Generated → Empty → Producing → Stock → Consuming → Deregistered
- 완제품: Generated → Empty → Producing → Finished → Deregistered
- 예외: Hold, Defect

**제약**:
- `lot_id`와 `assembly_lot_id`는 상호 배타적 (하나만 NOT NULL 또는 둘 다 NULL)
- Finished 상태는 완제품(`parts.is_final_product = TRUE`)만 가능

#### 9. 팔레트 이력 (pallet_histories)
- **목적**: 모든 상태 변경 불변 로그
- **주요 컬럼**:
  - `pallet_id`: 팔레트 ID (FK)
  - `lot_id`: 중간품 LOT ID (FK)
  - `assembly_lot_id`: 조립품 LOT ID (FK)
  - `process_id`: 공정 ID (FK)
  - `location_type`: 위치 유형
  - `previous_status`: 이전 상태
  - `current_status`: 현재 상태
  - `event_type`: 이벤트 유형
  - `event_time`: 이벤트 발생 시간
  - `worker_name`: 작업자

#### 10. RFID 태그 (rfid_tags)
- **목적**: RFID 태그 자체 관리
- **주요 컬럼**:
  - `epc` (VARCHAR, UNIQUE): RFID EPC 코드
  - `status`: 태그 상태 (AVAILABLE, IN_USE, DAMAGED)
  - `current_pallet_id`: 현재 연결된 팔레트 ID (FK)

---

## 추적성 지원 뷰 (6개)

### 1. v_pallet_status
- **목적**: 팔레트 현황 조회
- **포함**: 팔레트 정보 + LOT 정보 + 품번 + 공정 + 원자재

### 2. v_stock_inventory
- **목적**: 재고 현황 (FIFO용)
- **포함**: Stock 상태 팔레트, 생산일자별 그룹화, 가장 오래된 재고 표시

### 3. v_pallet_trace
- **목적**: 공정 이력 추적
- **포함**: 팔레트별 모든 이벤트 시간순 정렬

### 4. v_assembly_trace
- **목적**: 조립 추적 (완제품 → 구성품)
- **포함**: 조립품과 투입된 중간품/하위 조립품 관계

### 5. v_material_forward_trace
- **목적**: 원자재 정방향 추적 (코일 → 제품)
- **포함**: 특정 코일로 생산된 모든 LOT/팔레트/완제품

### 6. v_product_backward_trace
- **목적**: 제품 역방향 추적 (제품 → 원자재)
- **포함**: 특정 제품에 사용된 LOT 및 코일 정보

---

## 필수 데이터 무결성 규칙

### 1. 원자재 추적
- 모든 중간품 LOT는 `raw_materials.id`와 연결 필수

### 2. 팔레트-LOT 매핑
- 팔레트는 중간품 LOT 또는 조립품 LOT 중 하나와만 연결 (동시 연결 불가)

### 3. 조립 레벨 자동 계산
- `assembly_components` 추가 시 트리거로 최대 구성요소 레벨 + 1로 자동 계산

### 4. FIFO 검증 함수
```sql
CREATE FUNCTION check_fifo(
    p_part_id BIGINT,
    p_production_date DATE
) RETURNS BOOLEAN
```
- 같은 품번의 더 오래된 재고(Stock 상태) 존재 여부 확인
- 위반 시: 경고 표시 + Hold 상태 전환
- Override 가능 (권한 + 사유 기록)

### 5. 오투입 검증
- LOT 품번과 공정 요구 품번 불일치 시 투입 즉시 차단
- Override 불가 (시스템 차단 유지)
- 에러 메시지: "품번 불일치 - 현재 공정: [공정명], 요구 품번: [품번], LOT 품번: [품번]"

### 6. Finished 상태 제약 (완제품 전용)
- Finished 상태 전환 시 `parts.is_final_product = TRUE` 검증 필수
- 중간품 팔레트의 Finished 전환 시도는 에러 발생 및 거부
- 완제품 팔레트는 Stock 상태를 거치지 않고 Producing → Finished로 직접 전환

### 7. RFID 유일성
- RFID EPC 코드는 시스템 전체에서 유일해야 함 (UNIQUE 제약)

### 8. 리더기 위치 매핑
- RETURN 리더기는 `location_type='FINISH'`로 설정
- Finished → Deregistered 전환 담당

---

## 스키마 변경 관리 원칙

1. **이력 데이터 보존**: `pallet_histories` 절대 삭제 금지
2. **참조 무결성**: 외래 키 제약으로 참조 무결성 강제
3. **비즈니스 규칙 강제**: 트리거 및 CHECK 제약 활용
4. **마이그레이션 테스트**: 실제 운영 수준 데이터 볼륨 테스트
5. **타임스탬프 자동화**: `CURRENT_TIMESTAMP`, `ON UPDATE` 사용

---

## 트리거 및 함수

### 조립 레벨 자동 계산 트리거
```sql
CREATE TRIGGER after_insert_assembly_component
AFTER INSERT ON assembly_components
FOR EACH ROW
BEGIN
    -- 최대 구성요소 레벨 찾기
    -- assembly_level = max_component_level + 1
END
```

### FIFO 검증 함수
```sql
CREATE FUNCTION check_fifo(
    p_part_id BIGINT,
    p_production_date DATE
) RETURNS BOOLEAN
```

---

## 참고
- 전체 SQL 스키마: `/home/hakslee/temp/DB/Ajin_DB.sql`
- 헌법 문서: `.specify/memory/constitution.md`
