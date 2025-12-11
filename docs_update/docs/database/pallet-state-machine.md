# 팔레트 상태 기계 상세 명세

## 9가지 팔레트 상태 정의

### 1. Generated (생성됨)
- **설명**: 팔레트가 DB에 생성됨 (RFID 태그 매칭 전)
- **진입**: 팔레트 신규 생성 시
- **다음 상태**: Empty
- **물리 상태**: DB에만 존재, 물리적 태그 없음

### 2. Empty (빈 팔레트)
- **설명**: RFID 태그 매칭 완료, 적재 대기 중
- **진입**: RFID 태그와 팔레트 매칭 완료
- **다음 상태**: Producing
- **물리 상태**: 빈 팔레트 + RFID 태그 부착됨

### 3. Stock (재고 보관 중)
- **설명**: 만차 상태, 다음 공정 투입 대기 (중간품만)
- **진입**: 중간품 생산 완료 (OUT 리더기 태깅)
- **다음 상태**: Consuming
- **물리 상태**: 제품 가득 적재됨
- **제약**: 완제품은 Stock 상태 사용 불가

### 4. Consuming (공정 투입 중)
- **설명**: 소비 목적으로 공정 투입됨 (중간품 소비 중)
- **진입**: Stock 팔레트를 IN 리더기에 태깅
- **다음 상태**: Finished (소비 완료 시)
- **물리 상태**: 공정에서 제품 소진 중

### 5. Producing (공정 생산 중)
- **설명**: 생산 목적으로 공정 투입됨 (중간품/완제품 생산 중)
- **진입**: Empty 팔레트를 IN 리더기에 태깅
- **다음 상태**: 
  - Stock (중간품 생산 완료)
  - Finished (완제품 생산 완료)
- **물리 상태**: 공정에서 제품 적재 중

### 6. Finished (완제품 조립 완료)
- **설명**: 납품 대기 중 (완제품 전용 상태)
- **진입**: 완제품 조립 공정 OUT 리더기에서 만차 태깅
- **다음 상태**: Deregistered
- **물리 상태**: 완제품 가득 적재됨
- **제약**: `parts.is_final_product = TRUE`인 경우만 가능

### 7. Deregistered (태그 회수 완료)
- **설명**: RFID 태그 회수, 재사용 대기
- **진입**: 
  - RETURN 리더기에 빈 팔레트 태깅 (완제품 납품 후)
  - Finished 상태에서 소비 완료
- **다음 상태**: 없음 (종료 상태) 또는 재사용 시 Generated
- **물리 상태**: 빈 팔레트, 태그 분리됨

### 8. Hold (일시 차단)
- **설명**: FIFO 위반, 오투입 등으로 일시 차단
- **진입**: 
  - FIFO 검증 실패 시 자동 전환
  - 작업자가 HOLD 리더기에 태깅
- **다음 상태**: 명시적 해제 후 원래 상태로 복귀
- **물리 상태**: 보류 구역에 격리
- **해제**: 관리자 권한 + 사유 기록 필요

### 9. Defect (불량 처리)
- **설명**: 품질 불량으로 판정됨
- **진입**: DEFECT 리더기에 태깅
- **다음 상태**: 없음 (종료 상태)
- **물리 상태**: 불량품 적재소에 격리
- **제약**: 재사용/생산 투입 불가

---

## 상태 전환 흐름

### 첫 공정 흐름 (샤링) - 실제 현장 흐름
```
원자재 입고: LOT만 DB 등록 (팔레트 추적 전)
    ↓
샤링 OUT: 제품을 팔레트에 적재하면서 추적 시작
    ↓
Generated → Empty → Stock
  (생성)   (태그매칭) (OUT태깅)
```

### 중간품 흐름 (프레스 등) - 일반 공정
```
소비: Stock → Consuming → Deregistered
     (다음공정IN)  (소비완료)  (빈팔레트OUT)

생산: Empty → Producing → Stock
     (빈팔레트IN) (적재시작) (만차OUT)
```

### 완제품 흐름 (정상)
```
Generated → Empty → Producing → Finished → Deregistered
           (태그매칭) (적재시작) (만차OUT)  (빈팔레트RETURN)
```

### 예외 흐름
```
Stock → Hold (FIFO 위반)
      → Defect (불량 판정)

Producing → Defect (생산 중 불량)
```

---

## 상태 전환 트리거

### IN 리더기 (공정 투입)
- **Empty → Producing**: 빈 팔레트 투입 (적재용)
- **Stock → Consuming**: 만차 팔레트 투입 (소비용)
- **검증**: 
  - 오투입 검사 (품번 일치) → 실패 시 차단
  - FIFO 검사 (더 오래된 재고 존재) → 실패 시 Hold

### OUT 리더기 (공정 완료)
- **Producing → Stock**: 중간품 생산 완료 (만차)
- **Producing → Finished**: 완제품 생산 완료 (만차)
- **Consuming → Deregistered**: 소비 완료 (빈 팔레트)

### HOLD 리더기 (일시 차단)
- **Any → Hold**: 작업자가 명시적으로 보류 구역 이동

### DEFECT 리더기 (불량 처리)
- **Any → Defect**: 불량품 적재소 이동

### FINISH 리더기 (빈 팔레트 회수, RETURN)
- **Finished → Deregistered**: 완제품 납품 후 빈 팔레트 반환

---

## 상태 전환 제약

### 허용되지 않는 전환
- ❌ Stock → Finished (중간품은 Finished 불가)
- ❌ Finished → Stock (완제품은 Stock 불가)
- ❌ Deregistered → Any (재사용 시 새로 Generated)
- ❌ Defect → Any (불량은 재사용 불가)
- ❌ Hold → Producing/Consuming (명시적 해제 필요)

### 필수 검증
- Empty → Producing: 팔레트가 실제로 비어있는지
- Stock → Consuming: FIFO 검증 (경고)
- Producing → Finished: `parts.is_final_product = TRUE` 검증 (차단)

---

## 상태별 부저 및 피드백

| 상태 전환 | 부저 | 메시지 | 추가 동작 |
|----------|------|--------|----------|
| Empty → Stock | 1회 | "재고 등록" | 중간품 OUT 태깅 |
| Stock → Consuming | 1회 | "투입 완료" | FIFO 검증 (경고만) |
| Consuming → Deregistered | 1회 | "공정 완료" | 빈 팔레트 회수 |
| Empty → Finished | 1회 | "완제품 완료" | 완제품 전용 |
| FIFO 위반 경고 | 3회 | "FIFO 위반 - 확인 필요" | 무시하고 투입 가능 |
| 오투입 차단 | 3회 | "품번 불일치 - 투입 불가" | 투입 차단 |
| 불량 판정 | 2회 | "불량 처리" | Defect 전환 |

---

## 팔레트 빠른 회수 원칙

**중요**: 팔레트는 **이전 공정 OUT → 진행 공정 IN 까지만 사용**되고 즉시 회수됩니다.

### 예시 1: 샤링 OUT (첫 공정)
```
1. 샤링 공정 외부에서 제품을 팔레트에 적재
2. 팔레트 생성 + RFID 태그 매칭: Generated → Empty
3. 샤링 OUT 리더기 태깅: Empty → Stock (적재는 이미 완료됨)
```

### 예시 2: 프레스 공정 (중간품 소비)
```
1. 샤링에서 온 Stock 팔레트
2. 프레스 공정 IN 리더기: Stock → Consuming
3. 프레스 공정에서 제품 소비
4. 프레스 공정 IN 리더기 (빈 팔레트): Consuming → Deregistered
5. 빈 팔레트 회수 (태그 분리)
```

### 예시 3: 프레스 공정 (중간품 생산)
```
1. 빈 팔레트 준비
2. 프레스 공정 OUT 리더기: Empty → Producing
3. 프레스 공정에서 제품 적재
4. 프레스 공정 OUT 리더기 (만차): Producing → Stock
5. 다음 공정으로 이동
```

### 예시 4: 조립 공정 (완제품)
```
1. 조립 공정 IN 리더기에 빈 팔레트: Empty → Producing
2. 조립 공정에서 완제품 적재
3. 조립 공정 OUT 리더기: Producing → Finished
4. 완제품 납품
5. RETURN 리더기에 빈 팔레트: Finished → Deregistered
```

**효과**:
- 팔레트가 공정을 넘어 장기간 머물지 않음
- RFID 태그 자원 효율성 증대
- 공정 간 병목 방지

---

## 참고
- 헌법 문서: `docs/constitution.md`
- DB 아키텍처: `docs/database/database-architecture.md`
