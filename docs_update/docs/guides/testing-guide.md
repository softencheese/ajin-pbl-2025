# 🧪 RFID 물류 추적 시스템 테스트 가이드

이 가이드는 Docker 환경에서 시스템을 실행하고, 필수 데이터를 생성한 후, RFID 스캔 기능을 테스트하는 절차를 설명합니다.

## 1. 시스템 실행

`docker-compose`를 사용하여 전체 시스템(DB, API, Frontend)을 실행합니다.

```bash
# 프로젝트 루트 디렉토리에서 실행
docker-compose up -d
```

실행 후 다음 주소에서 서비스 상태를 확인하세요:
- **API 문서 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **프론트엔드**: [http://localhost:5173](http://localhost:5173)

---

## 2. 테스트 데이터 생성 (초기 설정)

시스템이 처음 실행되면 `processes`(공정) 데이터만 존재합니다. RFID 스캔 테스트를 위해 다음 순서대로 데이터를 생성해야 합니다.
**Swagger UI**(`http://localhost:8000/docs`)를 사용하면 편리합니다.

### 2.1 리더기 위치 등록 (Reader Location)
RFID 리더기가 어느 공정의 어떤 위치(투입/배출)에 있는지 정의합니다.

- **API**: `POST /api/v1/reader-locations`
- **설명**: `COM3` 포트를 `PRESS`(프레스) 공정의 `IN`(투입) 위치로 등록

```json
{
  "port_name": "COM3",
  "process_id": 2,
  "location_type": "IN",
  "description": "프레스 투입구 리더기",
  "is_active": true
}
```
> **참고**: `process_id: 2`는 초기 데이터에 의해 '프레스' 공정으로 설정되어 있습니다.

### 2.2 팔레트 등록 (Pallet)
테스트할 팔레트와 RFID 태그를 매핑합니다.

- **API**: `POST /api/v1/pallets`
- **설명**: `PLT-001` 팔레트에 태그 `E280...` 매핑

```json
{
  "pallet_no": "PLT-001",
  "rfid_epc": "E2801170000002036B3D8CCD"
}
```

---

## 3. RFID 스캔 테스트

이제 설정된 리더기(`COM3`)에서 등록된 태그(`E280...`)가 스캔되는 상황을 시뮬레이션합니다.

### 3.1 스캔 요청 전송
- **API**: `POST /api/v1/rfid/scan`
- **설명**: 리더기가 태그를 읽었음을 서버에 알림

```json
{
  "epc": "E2801170000002036B3D8CCD",
  "port_name": "COM3",
  "scan_time": "2025-12-01T10:00:00Z",
  "reader_info": {
    "model": "Simulated Reader",
    "antenna": 1,
    "rssi": -60
  }
}
```

### 3.2 응답 확인
정상적으로 처리되면 다음과 같은 응답을 받습니다.

```json
{
  "success": true,
  "pallet": {
    "pallet_no": "PLT-001",
    "previous_status": "Generated",
    "current_status": "Stock",  
    ...
  },
  "feedback": {
    "pattern": "SUCCESS",
    "count": 1,
    "led_color": "GREEN"
  }
}
```
> **결과**: 팔레트의 상태가 `Generated` → `Stock` (또는 로직에 따라 적절한 상태)으로 변경됩니다.

---

## 4. 데이터 확인

테스트 후 데이터가 잘 반영되었는지 확인합니다.

1. **팔레트 조회**: `GET /api/v1/pallets`
   - 상태가 변경되었는지 확인
2. **이력 조회**: `GET /api/v1/trace/{pallet_no}` (예: `PLT-001`)
   - 팔레트의 현재 상태와 이력을 확인할 수 있습니다.

## 5. (심화) 전체 프로세스 테스트

더 완벽한 테스트를 위해서는 다음 데이터도 순서대로 생성해보세요.

1. **원자재 등록**: `POST /api/v1/materials`
2. **품번 등록**: `POST /api/v1/items`
3. **LOT 생성**: `POST /api/v1/lots`
4. **팔레트에 LOT 연결**: `PUT /api/v1/pallets/{id}/link-lot`
5. **스캔 테스트**: 위와 동일하게 스캔 수행 시, 이제 LOT 정보까지 포함된 응답이 오는지 확인
