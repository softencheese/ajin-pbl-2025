# Lot Genealogy (LOT 족보)

## 개요

Lot Genealogy는 제조 공정에서 원자재부터 완제품까지의 LOT 간 투입-산출 관계를 추적하는 핵심 기능입니다. 이 시스템은 역방향 추적(완제품 → 원자재)과 정방향 추적(원자재 → 완제품)을 모두 지원합니다.

---

## 데이터 모델

### LotGenealogy (SQLAlchemy Model)

**파일**: `implementation/api/app/models/lot_genealogy.py`

```python
class LotGenealogy(BaseModel):
    """LOT 족보 (투입-산출 관계, 추적성 핵심)"""
    __tablename__ = "lot_genealogy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_lot_id = Column(BigInteger, ForeignKey("lots.id"), nullable=False, index=True)
    output_lot_id = Column(BigInteger, ForeignKey("lots.id"), nullable=False, index=True)
    process_id = Column(BigInteger, ForeignKey("processes.id"), nullable=False, index=True)
    quantity_consumed = Column(Integer, nullable=False)

    # Relationships
    input_lot = relationship("Lot", foreign_keys=[input_lot_id], backref="children_genealogy")
    output_lot = relationship("Lot", foreign_keys=[output_lot_id], backref="parent_genealogy")
    process = relationship("Process")
```

**필드 설명**:
- `input_lot_id`: 투입 LOT ID (부모 LOT)
- `output_lot_id`: 생성 LOT ID (자식 LOT)
- `process_id`: 해당 관계가 발생한 공정 ID
- `quantity_consumed`: 투입 수량

---

## API 엔드포인트

### 1. LOT 족보 조회 (GET /api/v1/lot-genealogy/{lot_id})

**파일**: `implementation/api/app/routers/lot_genealogy.py`

특정 LOT의 부모(투입)와 자식(산출) LOT 정보를 조회합니다.

**동작 방식**:
1. LOT 존재 여부 확인
2. 부모 LOT 조회: `LotGenealogy.output_lot_id == lot_id`로 필터링
3. 자식 LOT 조회: `LotGenealogy.input_lot_id == lot_id`로 필터링
4. 각 관계에서 LOT 번호, 품목코드, 품목 유형, 소비 수량 정보 추출

**응답 구조**:
```json
{
  "lot": {
    "id": 1,
    "lot_number": "LOT-001",
    "item_code": "ITEM-001"
  },
  "parents": [
    {
      "lot_number": "RAW-001",
      "item_code": "RAW-ITEM",
      "item_type": "RAW",
      "quantity_consumed": 100
    }
  ],
  "children": [
    {
      "lot_number": "WIP-001",
      "item_code": "WIP-ITEM",
      "item_type": "WIP",
      "quantity_consumed": 50
    }
  ]
}
```

**권한**: `lots:read`

---

### 2. LOT 족보 수동 생성 (POST /api/v1/lot-genealogy)

**파일**: `implementation/api/app/routers/lot_genealogy.py`

LOT 간 투입-산출 관계를 수동으로 생성합니다.

**요청 본문**:
```json
{
  "input_lot_id": 1,
  "output_lot_id": 2,
  "process_id": 3,
  "quantity_consumed": 100
}
```

**유효성 검사**:
1. 투입 LOT 존재 여부 확인
2. 출력 LOT 존재 여부 확인
3. 공정 존재 여부 확인
4. 순환 참조 방지: `input_lot_id != output_lot_id`

**권한**: `lots:write`

---

## LOT 생성 시 자동 Genealogy 생성

**파일**: `implementation/api/app/routers/lots.py` (lines 311-341)

생산 LOT을 생성할 때 `input_lots` 정보가 제공되면 자동으로 LotGenealogy 레코드가 생성됩니다.

**동작 순서**:
1. 새로운 LOT 생성
2. 각 투입 LOT에 대해:
   - `FOR UPDATE` 락으로 투입 LOT 조회 (동시성 문제 방지)
   - 수량 부족 체크: `input_lot.quantity >= quantity_consumed`
   - LotGenealogy 레코드 생성
   - 투입 LOT 수량 차감
   - 수량이 0이 되면 상태를 `CONSUMED`로 변경

```python
if data.input_lots:
    for input_info in data.input_lots:
        input_lot = db.query(Lot).filter(
            Lot.id == input_info.lot_id
        ).with_for_update().first()
        
        if input_lot.quantity < input_info.quantity_consumed:
            raise HTTPException(
                status_code=400, 
                detail="재고가 부족합니다"
            )
        
        genealogy = LotGenealogy(
            input_lot_id=input_info.lot_id,
            output_lot_id=lot.id,
            process_id=data.process_id,
            quantity_consumed=input_info.quantity_consumed
        )
        db.add(genealogy)
        
        input_lot.quantity -= input_info.quantity_consumed
        if input_lot.quantity <= 0:
            input_lot.status = "CONSUMED"
```

---

## LOT 삭제 시 Genealogy 참조 확인

**파일**: `implementation/api/app/routers/lots.py` (lines 537-545)

LOT을 삭제하기 전에 해당 LOT이 LotGenealogy에서 참조되는지 확인합니다.

```python
genealogy_count = db.query(LotGenealogy).filter(
    (LotGenealogy.input_lot_id == lot_id) | (LotGenealogy.output_lot_id == lot_id)
).count()

if genealogy_count > 0:
    raise HTTPException(
        status_code=409, 
        detail=f"해당 LOT이 족보에서 {genealogy_count}번 참조됩니다. 삭제할 수 없습니다."
    )
```

---

## 추적성 서비스 (Trace Service)

**파일**: `implementation/api/app/services/trace_service.py`

### 정방향 추적 (Forward Trace)

투입 LOT에서 시작하여 모든 하위 산출 LOT을 재귀적으로 추적합니다.

**동작 방식**:
1. `LotGenealogy.input_lot_id == root_lot.id`로 직계 자식 조회
2. 각 자식 LOT에 대해 `_trace_children()` 재귀 호출
3. 각 LOT의 팔레트 정보와 자식 LOT 정보 수집

```python
def _trace_children(self, parent_lot: Lot, produced_lots_map: dict):
    if parent_lot.id in produced_lots_map:
         return

    # 팔레트 조회
    pallets = self.db.query(Pallet).filter(Pallet.lot_id == parent_lot.id).all()
    
    # 하위 자식들 조회
    child_genes = self.db.query(LotGenealogy).filter(
        LotGenealogy.input_lot_id == parent_lot.id
    ).all()
    
    for cg in child_genes:
        self._trace_children(cg.output_lot, produced_lots_map)
```

### 역방향 추적 (Backward Trace)

산출 LOT에서 시작하여 모든 상위 투입 LOT을 재귀적으로 추적합니다.

**동작 방식**:
1. `LotGenealogy.output_lot_id == lot_id`로 직계 부모 조회
2. 각 부모 LOT에 대해 `_trace_parents_recursive()` 재귀 호출
3. 방문한 LOT을 `visited` 세트로 관리하여 순환 참조 방지

```python
def _trace_parents_recursive(self, lot_id: int, result: list, visited: set):
    if lot_id in visited:
        return
    visited.add(lot_id)
    
    genealogies = self.db.query(LotGenealogy).filter(
        LotGenealogy.output_lot_id == lot_id
    ).all()
    
    for gen in genealogies:
        result.append(ParentLotInfo(...))
        self._trace_parents_recursive(gen.input_lot.id, result, visited)
```

---

## 프론트엔드 연동

### API 클라이언트

**파일**: `implementation/frontend/src/api/genealogy.ts`

```typescript
export interface LotGenealogyItem {
  lot_number: string;
  item_code: string;
  item_type: string;
  quantity_consumed?: number;
}

export interface LotGenealogyResponse {
  lot: {
    id: number;
    lot_number: string;
    item_code: string | null;
  };
  parents: LotGenealogyItem[];
  children: LotGenealogyItem[];
}

export const genealogyApi = {
  async getByLotId(lotId: number) {
    const { data } = await apiClient.get<LotGenealogyResponse>(`/lot-genealogy/${lotId}`);
    return data;
  },
};
```

### LOT 추적 페이지

**파일**: `implementation/frontend/src/pages/Traceability/LotTrackingPage.tsx`

**주요 기능**:
1. LOT 검색 시 각 LOT의 genealogy 정보 조회
2. 부모 LOT(투입)과 자식 LOT(산출)을 트리 구조로 표시
3. 상세 모달에서 역방향/정방향 추적 정보 표시

**Genealogy 활용 코드**:
```typescript
// LOT 데이터 변환 시 genealogy 조회
const transformLot = async (lot: Lot): Promise<LotTraceData | null> => {
  let genealogy: LotGenealogyResponse | null = null;
  try {
    genealogy = await genealogyApi.getByLotId(lot.id);
  } catch (error) {
    console.warn(`Failed to fetch genealogy for lot ${lot.id}:`, error);
  }

  return {
    // ... other fields
    parents: genealogy?.parents?.map(p => p.lot_number) || [],
    childLotNumbers: genealogy?.children?.map(c => c.lot_number) || [],
  };
};

// 상세 모달에서 부모/자식 LOT 표시
{detailModal.genealogy?.parents && (
  <div>
    <h3>⬅️ 투입 LOT (역방향 추적)</h3>
    {detailModal.genealogy.parents.map((parent, idx) => (
      <Card key={idx}>
        <strong>{parent.lot_number}</strong> - {parent.item_code}
        <div>유형: {parent.item_type} | 소비량: {parent.quantity_consumed}</div>
      </Card>
    ))}
  </div>
)}
```

---

## 스키마 정의

**파일**: `implementation/api/app/schemas/lot_genealogy.py`

```python
class LotGenealogyBase(BaseModel):
    input_lot_id: int
    output_lot_id: int
    process_id: int
    quantity_consumed: int

class LotGenealogyCreate(LotGenealogyBase):
    pass

class LotGenealogyResponse(LotGenealogyBase):
    id: int
    created_at: datetime

class LotGenealogyWithDetails(BaseModel):
    id: int
    input_lot_number: str
    input_item_code: str
    input_item_type: str
    output_lot_number: str
    output_item_code: str
    output_item_type: str
    process_name: str
    quantity_consumed: int
    created_at: datetime
```

---

## 라우터 등록

**파일**: `implementation/api/app/main.py` (line 72)

```python
app.include_router(lot_genealogy_router, prefix="/api/v1/lot-genealogy", tags=["Lot Genealogy"])
```

---

## 테스트

**파일**: `implementation/api/tests/test_lot_management.py` (lines 67-95)

```python
def test_create_lot_genealogy_manual(client: TestClient, db_session: Session):
    """족보 수동 생성 테스트 (POST /lot-genealogy)"""
    process = db_session.query(Process).first()
    item = db_session.query(Item).first()
    
    l1 = Lot(lot_number="G-IN-001", item_id=item.id, quantity=100, ...)
    l2 = Lot(lot_number="G-OUT-001", item_id=item.id, quantity=50, ...)
    db_session.add_all([l1, l2])
    db_session.commit()
    
    payload = {
        "input_lot_id": l1.id,
        "output_lot_id": l2.id,
        "process_id": process.id,
        "quantity_consumed": 10
    }
    
    response = client.post("/api/v1/lot-genealogy", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["input_lot_id"] == l1.id
    assert data["output_lot_id"] == l2.id
    assert data["quantity_consumed"] == 10
```

---

## 데이터베이스 시딩 (init_db_api.py)

**파일**: `init_db_api.py`

초기 데이터 생성 시 LOT 간 Genealogy 관계를 자동으로 설정합니다.

### 동작 흐름

```
RAW LOT 생성 → ID 저장 (raw_lots_map)
     ↓
WIP LOT 생성 → input_lots에 RAW LOT ID 연결 → ID 저장 (wip_lots_map)
     ↓
PRODUCT LOT 생성 → input_lots에 WIP LOT ID 연결
```

### 핵심 코드

```python
def create_lots(client: APIClient, data: dict):
    raw_lots_map = {}  # item_code -> [lot_id, ...]
    wip_lots_map = {}  # item_code -> [lot_id, ...]

    # RAW LOT 생성 및 ID 저장
    for raw in data["raw_items"]:
        result = client.post("/api/v1/lots/receiving", lot_data)
        raw_lots_map.setdefault(raw["item_code"], []).append(result['id'])

    # WIP LOT 생성 - input_lots 연결
    for wip in data["wip_items"]:
        input_lots = []
        for child in wip.get("child", []):
            parent_code = find_parent_item_code(child["id"], data["raw_items"])
            if parent_code in raw_lots_map:
                input_lots.append({
                    "lot_id": raw_lots_map[parent_code][0],
                    "quantity_consumed": child["quantity"]
                })

        lot_data = {
            "item_id": item["id"],
            "quantity": 100,
            "process_id": process_id,
            "input_lots": input_lots  # ← Genealogy 생성 트리거
        }
        result = client.post("/api/v1/lots", lot_data)
        wip_lots_map.setdefault(item_code, []).append(result['id'])

    # PRODUCT LOT 생성 - input_lots 연결
    for prod in data["product_items"]:
        input_lots = []
        for child in prod.get("child", []):
            parent_code = find_parent_item_code(child["id"], data["wip_items"])
            if parent_code in wip_lots_map:
                input_lots.append({
                    "lot_id": wip_lots_map[parent_code][0],
                    "quantity_consumed": child["quantity"]
                })

        lot_data = {
            "item_id": item["id"],
            "quantity": 50,
            "process_id": process_id,
            "input_lots": input_lots  # ← Genealogy 생성 트리거
        }
        client.post("/api/v1/lots", lot_data)
```

### BOM 구조 매핑

`virt_data.json`의 `child` 필드를 사용하여 부품 구조를 매핑합니다:

```json
{
  "item": [
    {
      "id": 2,
      "code": "71411",
      "item_name": "반제품A-샤링",
      "type": "WIP",
      "child": [{"id": 1, "quantity": 1}]  // id=1인 RAW 품목 1개 투입
    },
    {
      "id": 4,
      "code": "ASSY-76211",
      "item_name": "완제품A",
      "type": "PRODUCT",
      "child": [{"id": 3, "quantity": 1}]  // id=3인 WIP 품목 1개 투입
    }
  ]
}
```

---

## 데이터베이스 인덱스

LotGenealogy 테이블은 다음 필드에 인덱스가 설정되어 있습니다:
- `input_lot_id`: 부모 LOT 기반 조회 최적화
- `output_lot_id`: 자식 LOT 기반 조회 최적화
- `process_id`: 공정 기반 조회 최적화

이 인덱스들은 정방향/역방향 추적 쿼리의 성능을 보장합니다.
