# 데이터베이스 아키텍처 상세 명세

## 개요
아진산업 PBL RFID 기반 팔레트 추적 시스템의 데이터베이스 구조 및 무결성 규칙

---

## 설계 철학

### 품목(Item)과 LOT의 분리

```
┌─────────────────┐     ┌─────────────────┐
│     ITEMS       │     │      LOTS       │
│  (무엇인가?)      │◄────│   (어떤 것인가?)   │
│                 │     │                 │
│ - 품번           │     │ - LOT 번호       │
│ - 원자재코드       │     │ - 수량           │
│ - 제품 규격       │     │ - 생산일자        │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  LOT_GENEALOGY  │
                        │ (어떻게 만들어졌나?) │
                        │                 │
                        │ - 투입 LOT       │
                        │ - 산출 LOT       │
                        └─────────────────┘
```

> [!IMPORTANT]
> - **원자재 코드는 품번과 동일한 개념**입니다. 동일한 코드로 여러 번 입고될 수 있습니다.
> - **LOT 번호는 시스템이 자동 생성**하는 고유 식별자입니다.
> - 원자재 종류는 `item_id` → `items.item_code`로 추적합니다.

---

## 핵심 테이블 구조

### 마스터 데이터 (3개 테이블)

#### 1. 통합 품목 마스터 (items)
- **목적**: 원자재, 중간품, 완제품 모든 품목의 기준 정보 통합 관리
- **주요 컬럼**: 
  - `item_code` (VARCHAR, UNIQUE): 품번 또는 원자재코드
  - `item_name`: 품명
  - `item_type`: 품목 유형 (RAW/WIP/PRODUCT)
  - `spec`: 규격 (LH/RH, 색상, 재질 등)
  - `vehicle_model`: 적용 차종
  - `default_supplier`: 기본 공급사 (원자재)

**item_type 구분**:
| 값 | 설명 | 예시 |
|---|------|------|
| `RAW` | 원자재 | 코일, 철판, 볼트 |
| `WIP` | 재공품/중간품 | 샤링품, 프레스품 |
| `PRODUCT` | 완제품 | 조립 완료 제품 |

#### 2. 공정 마스터 (processes)
- **목적**: 공정 정보 관리
- **주요 컬럼**:
  - `process_code` (VARCHAR, UNIQUE): 공정 코드
  - `process_name`: 공정명 (입고, 샤링, 프레스, 조립, 출하)
  - `process_order`: 공정 순서
  - `production_line`: 생산 라인

#### 3. RFID 리더기 위치 (rfid_reader_locations)
- **목적**: 리더기와 공정/위치 매핑
- **주요 컬럼**:
  - `port_name` (VARCHAR, UNIQUE): 리더기 포트
  - `process_id`: 연결된 공정 ID
  - `location_type`: 위치 유형 (IN, OUT, HOLD, DEFECT, FINISH, RETURN)
  - `description`: 설명

---

### LOT 관리 데이터 (2개 테이블)

#### 4. 통합 LOT 관리 (lots)
- **목적**: 모든 실물 인스턴스의 추적 단위
- **주요 컬럼**:
  - `lot_number` (VARCHAR, UNIQUE): 시스템 생성 LOT 번호 (고유)
  - `item_id`: 품목 ID (FK → items) - 원자재 코드는 여기서 참조
  - `quantity`: 현재 수량
  - `initial_quantity`: 초기 수량
  - `status`: LOT 상태 (WAIT, PROCESS, STOCK, CONSUMED, SHIPPED, HOLD, DEFECT)
  - `production_date`: 생산/입고일
  - `process_id`: 생성 공정 ID
  - `supplier`: 공급사 (원자재 입고 시, 기본 공급사와 다를 경우)
  - `worker_name`: 작업자
  - `qc_passed`: QC 합격 여부

**LOT 번호 생성 규칙**:
```
원자재 입고:  IN-YYMMDD-SEQ  (예: IN-231211-001)
샤링 생산:   SH-YYMMDD-SEQ  (예: SH-231211-001)
프레스 생산: PR-YYMMDD-SEQ  (예: PR-231211-001)
조립 생산:   AS-YYMMDD-SEQ  (예: AS-231211-001)
```

#### 5. LOT 족보 (lot_genealogy)
- **목적**: 모든 공정 간 투입-산출 관계 기록 (추적성 핵심)
- **주요 컬럼**:
  - `input_lot_id`: 투입 LOT ID (부모)
  - `output_lot_id`: 산출 LOT ID (자식)
  - `process_id`: 발생 공정 ID
  - `quantity_consumed`: 투입 수량

**추적 흐름 예시**:
```
원자재 LOT (IN-231211-001)
    ↓ [샤링 공정]
샤링품 LOT (SH-231211-001)
    ↓ [프레스 공정]
프레스품 LOT (PR-231211-001)
    ↓ [조립 공정] ← 다른 부품 LOT도 투입
완제품 LOT (AS-231211-001)
```

**원자재 입고 워크플로우** (RFID 불필요):
1. **입고 등록**: 사용자가 품목, 수량, 입고일, 공급사 입력 → LOT 자동 생성 (status: STOCK)
2. **샤링 투입**: 작업자가 원자재 LOT 선택 → 샤링품 LOT 생성 → lot_genealogy에 관계 기록
3. **상태 업데이트**: 원자재 전량 소비 시 status → CONSUMED

---

### RFID 추적 데이터 (3개 테이블)

#### 6. 팔레트 (pallets)
- **목적**: RFID 태그 매칭 및 상태 관리
- **주요 컬럼**:
  - `pallet_no` (VARCHAR, UNIQUE): 팔레트 번호
  - `rfid_epc` (VARCHAR, UNIQUE): RFID EPC 코드 (1:1 매핑)
  - `lot_id`: 연결된 LOT ID (FK → lots)
  - `status`: 팔레트 상태 (9가지)
  - `current_process_id`: 현재 공정 ID
  - `quantity`: 현재 적재 수량

**상태 흐름**:
- 중간품: Generated → Empty → Producing → Stock → Consuming → Deregistered
- 완제품: Generated → Empty → Producing → Finished → Deregistered
- 예외: Hold, Defect

#### 7. 팔레트 이력 (pallet_histories)
- **목적**: 모든 상태 변경 불변 로그
- **주요 컬럼**:
  - `pallet_id`: 팔레트 ID
  - `lot_id`: LOT ID
  - `process_id`: 공정 ID
  - `previous_status`: 이전 상태
  - `new_status`: 현재 상태
  - `event_type`: 이벤트 유형
  - `scan_time`: 스캔 시간
  - `notes`: 비고

#### 8. RFID 태그 (rfid_tags)
- **목적**: RFID 태그 자체 관리
- **주요 컬럼**:
  - `epc` (VARCHAR, UNIQUE): RFID EPC 코드
  - `status`: 태그 상태 (AVAILABLE, IN_USE, DAMAGED)

---

## 추적성 지원 뷰 (5개)

### 1. v_pallet_status
- **목적**: 팔레트 현황 조회
- **포함**: 팔레트 정보 + LOT 정보 + 품목 정보 + 공정

### 2. v_stock_inventory
- **목적**: 재고 현황 (FIFO용)
- **포함**: Stock 상태 팔레트, 생산일자별 그룹화, 경과일수

### 3. v_lot_forward_trace
- **목적**: 정방향 추적 (원자재 → 완제품)
- **포함**: 특정 원자재 LOT로 생산된 모든 하위 LOT

### 4. v_lot_backward_trace
- **목적**: 역방향 추적 (완제품 → 원자재)
- **포함**: 특정 완제품에 사용된 모든 상위 LOT

### 5. v_lot_full_genealogy
- **목적**: LOT 전체 족보 조회
- **포함**: 모든 투입-산출 관계 조인 정보

---

## 필수 데이터 무결성 규칙

### 1. LOT 추적성
- 모든 LOT는 `items.id`와 연결 필수
- 공정 완료 시 `lot_genealogy`에 투입-산출 관계 기록 필수

### 2. LOT 번호 규칙
- `lot_number`: 시스템 자동 생성 (UNIQUE, 절대 중복 불가)
- `external_lot_no`: 외부 참조용 (중복 가능, 코일번호 등)

### 3. 팔레트-LOT 매핑
- 팔레트는 하나의 LOT만 적재 가능 (`lot_id` 단일 FK)
- LOT 변경 시 반드시 이력 기록

### 4. FIFO 검증 함수
```sql
CREATE FUNCTION check_fifo(
    p_item_id BIGINT,
    p_production_date DATE
) RETURNS BOOLEAN
```
- 같은 품목의 더 오래된 재고(Stock 상태) 존재 여부 확인
- 위반 시: 경고 표시 + 이력 기록 (투입은 허용)

### 5. 오투입 검증
- LOT 품목과 공정 요구 품목 불일치 시 투입 즉시 차단
- Override 불가 (시스템 차단 유지)
- 에러 메시지: "품번 불일치 - 현재 공정: [공정명], 요구 품번: [품번], LOT 품번: [품번]"

### 6. RFID 유일성
- RFID EPC 코드는 시스템 전체에서 유일해야 함 (UNIQUE 제약)

---

## 스키마 변경 관리 원칙

1. **이력 데이터 보존**: `pallet_histories`, `lot_genealogy` 절대 삭제 금지
2. **참조 무결성**: 외래 키 제약으로 참조 무결성 강제
3. **비즈니스 규칙 강제**: CHECK 제약 및 애플리케이션 레벨 검증
4. **마이그레이션 테스트**: 실제 운영 수준 데이터 볼륨 테스트
5. **타임스탬프 자동화**: `CURRENT_TIMESTAMP`, `ON UPDATE` 사용

---

## 테이블 요약

| 분류 | 테이블명 | 설명 |
|------|----------|------|
| 마스터 | `items` | 통합 품목 마스터 (RAW/WIP/PRODUCT) |
| 마스터 | `processes` | 공정 마스터 |
| 마스터 | `rfid_reader_locations` | 리더기 위치 매핑 |
| LOT | `lots` | 통합 LOT 관리 |
| LOT | `lot_genealogy` | LOT 족보 (추적성 핵심) |
| RFID | `rfid_tags` | RFID 태그 마스터 |
| RFID | `pallets` | 팔레트 상태 관리 |
| RFID | `pallet_histories` | 팔레트 이력 로그 |

**총 8개 테이블**

---

## 참고
- 전체 SQL 스키마: `docs/database/schema.md`
- 팔레트 상태 기계: `docs/database/pallet-state-machine.md`
- 헌법 문서: `docs/constitution.md`
