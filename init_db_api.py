"""
API를 통한 DB 초기화 스크립트
virt_data.json을 읽어서 API 엔드포인트를 호출하여 데이터를 생성합니다.
"""
import json
import os
import sys
import requests
from datetime import date, timedelta
from typing import Optional

VIRT_DATA_PATH = os.path.join(os.path.dirname(__file__), "virt_data.json")

# API 서버 설정
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_USERNAME = os.environ.get("API_USERNAME", "admin")
API_PASSWORD = os.environ.get("API_PASSWORD", "admin123")


class APIClient:
    """API 클라이언트"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.login(username, password)
    
    def login(self, username: str, password: str):
        """로그인하여 토큰 획득"""
        print(f"🔐 로그인 중... ({username})")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ 로그인 성공!")
        except requests.exceptions.RequestException as e:
            print(f"❌ 로그인 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   응답: {e.response.text}")
            exit(1)
    
    def get(self, endpoint: str, **kwargs):
        """GET 요청"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, json_data: dict, **kwargs):
        """POST 요청"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=json_data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, json_data: dict, **kwargs):
        """PUT 요청"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=json_data, **kwargs)
        response.raise_for_status()
        return response.json()


def load_virt_data():
    """virt_data.json 로드"""
    print(f"📂 virt_data.json 로드 중... ({VIRT_DATA_PATH})")
    with open(VIRT_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    
    # item 배열이 있으면 타입별로 분리 (루트 virt_data.json 형식)
    if "item" in data and "raw_items" not in data:
        items = data.get("item", [])
        data["raw_items"] = []
        data["wip_items"] = []
        data["product_items"] = []
        
        for item in items:
            item_type = item.get("type", "")
            if item_type == "RAW":
                data["raw_items"].append(item)
            elif item_type == "WIP":
                data["wip_items"].append(item)
            elif item_type == "PRODUCT":
                data["product_items"].append(item)
    
    # 기본값 설정
    data.setdefault("raw_items", [])
    data.setdefault("wip_items", [])
    data.setdefault("product_items", [])
    
    print("✅ virt_data.json 로드 완료!")
    print(f"   - RAW: {len(data['raw_items'])}개, WIP: {len(data['wip_items'])}개, PRODUCT: {len(data['product_items'])}개")
    return data


def create_processes(client: APIClient, data: dict):
    """공정 생성"""
    print("\n" + "="*60)
    print("📦 공정(Process) 생성")
    print("="*60)
    
    created_count = 0
    skipped_count = 0
    
    for p_data in data["processes"]:
        try:
            # 중복 체크
            existing = client.get(
                "/api/v1/processes",
                params={"per_page": 100}
            )
            exists = any(
                p["process_code"] == p_data["process_code"] 
                for p in existing.get("items", [])
            )
            
            if exists:
                print(f"  ⏭️  {p_data['process_name']} ({p_data['process_code']}) - 이미 존재")
                skipped_count += 1
                continue
            
            # 생성
            result = client.post("/api/v1/processes", p_data)
            print(f"  ✅ {p_data['process_name']} ({p_data['production_line']}) - ID: {result['id']}")
            created_count += 1
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"  ⏭️  {p_data['process_name']} - 이미 존재 (409)")
                skipped_count += 1
            else:
                print(f"  ❌ {p_data['process_name']} - 오류: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"     응답: {e.response.text}")
    
    print(f"\n총 {created_count}개 생성, {skipped_count}개 스킵")


def create_items(client: APIClient, data: dict):
    """품목 생성"""
    print("\n" + "="*60)
    print("📦 품목(Item) 생성")
    print("="*60)
    
    created_count = 0
    skipped_count = 0
    
    # RAW 원자재
    print("\n[원자재 - RAW]")
    for i_data in data["raw_items"]:
        i_data = dict(i_data)
        i_data["item_type"] = "RAW"
        i_data.setdefault("unit", "KG")
        i_data.setdefault("spec", "")
        i_data.setdefault("vehicle_model", None)
        i_data.setdefault("default_supplier", "")
        
        try:
            result = client.post("/api/v1/items", i_data)
            print(f"  ✅ {i_data['item_code']} - ID: {result['id']}")
            created_count += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"  ⏭️  {i_data['item_code']} - 이미 존재")
                skipped_count += 1
            else:
                print(f"  ❌ {i_data['item_code']} - 오류: {e.response.text}")
    
    # WIP 재공품
    print("\n[재공품 - WIP]")
    for w in data["wip_items"]:
        item_code = f"{w['code']}-{w['vehicle_model']}-SH"
        i_data = {
            "item_code": item_code,
            "item_name": w["item_name"],
            "item_type": "WIP",
            "unit": w.get("unit", "EA"),
            "vehicle_model": w["vehicle_model"],
            "spec": w.get("spec_suffix", ""),
        }
        
        try:
            result = client.post("/api/v1/items", i_data)
            print(f"  ✅ {i_data['item_code']} - ID: {result['id']}")
            created_count += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"  ⏭️  {i_data['item_code']} - 이미 존재")
                skipped_count += 1
            else:
                print(f"  ❌ {i_data['item_code']} - 오류: {e.response.text}")
    
    # PRODUCT 완제품
    print("\n[완제품 - PRODUCT]")
    for p in data["product_items"]:
        item_code = f"{p['code']}-{p['vehicle_model']}"
        i_data = {
            "item_code": item_code,
            "item_name": p["item_name"],
            "item_type": "PRODUCT",
            "unit": p.get("unit", "EA"),
            "vehicle_model": p["vehicle_model"],
            "spec": p.get("spec_suffix", ""),
        }
        
        try:
            result = client.post("/api/v1/items", i_data)
            print(f"  ✅ {i_data['item_code']} - ID: {result['id']}")
            created_count += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"  ⏭️  {i_data['item_code']} - 이미 존재")
                skipped_count += 1
            else:
                print(f"  ❌ {i_data['item_code']} - 오류: {e.response.text}")
    
    print(f"\n총 {created_count}개 생성, {skipped_count}개 스킵")


def create_reader_locations(client: APIClient, data: dict):
    """리더기 위치 생성"""
    print("\n" + "="*60)
    print("📦 RFID 리더기 위치(ReaderLocation) 생성")
    print("="*60)
    
    created_count = 0
    skipped_count = 0
    
    # process_code -> id 매핑 (process-code 키 지원용)
    processes = client.get("/api/v1/processes", params={"per_page": 100})
    process_map = {p["process_code"]: p["id"] for p in processes.get("items", [])}
    
    for r in data["reader"]["reader-info"]:
        # process-id 또는 process-code 지원
        process_id = r.get("process-id") or process_map.get(r.get("process-code"))
        
        for inner in r.get("inner", []):
            port_name = f"{r['prot-name']}-{inner['prefix-name']}"
            location_type_raw = inner.get("location-type", inner["prefix-name"])
            location_type = location_type_raw if location_type_raw in [
                "IN", "OUT", "HOLD", "HOLD_OUT", "DEFECT", "DEFECT_OUT", "SCRAP", "FINISH", "RETURN", "REG"
            ] else None
            desc = inner.get("description", "")
            
            location_data = {
                "port_name": port_name,
                "process_id": process_id,
                "location_type": location_type,
                "description": desc,
                "is_active": True
            }
            
            try:
                result = client.post("/api/v1/reader-locations", location_data)
                print(f"  ✅ {port_name} -> {desc} ({location_type}) - ID: {result['id']}")
                created_count += 1
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:
                    print(f"  ⏭️  {port_name} - 이미 존재")
                    skipped_count += 1
                else:
                    print(f"  ❌ {port_name} - 오류: {e.response.text}")
    
    print(f"\n총 {created_count}개 생성, {skipped_count}개 스킵")


def create_lots(client: APIClient, data: dict):
    print("\n" + "="*60)
    print("📦 LOT 생성")
    print("="*60)

    created_count = 0
    skipped_count = 0
    today = date.today()

    items = client.get("/api/v1/items", params={"per_page": 100})
    item_dict = {item["item_code"]: item for item in items.get("items", [])}

    print("\n[원자재 LOT - RAW]")
    for raw in data["raw_items"]:
        item = item_dict.get(raw["item_code"])
        if not item:
            print(f"  ⚠️  품목 없음: {raw['item_code']}")
            continue

        lot_data = {
            "item_id": item["id"],
            "quantity": 1000,
            "production_date": today.isoformat(),
            "supplier": item.get("default_supplier", ""),
            "notes": "초기 시딩 데이터"
        }

        try:
            result = client.post("/api/v1/lots/receiving", lot_data)
            print(f"  ✅ {result['lot_number']} - ID: {result['id']}")
            created_count += 1

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ {raw['item_code']} - 오류: {e.response.text}")

    print("\n[재공품 LOT - WIP]")
    for wip in data["wip_items"]:
        item_code = f"{wip['code']}-{wip['vehicle_model']}-SH"
        item = item_dict.get(item_code)
        if not item:
            print(f"  ⚠️  품목 없음: {item_code}")
            continue

        process_id = wip.get("process_id")
        if not process_id:
            print(f"  ⚠️  {item_code} - process_id 없음")
            skipped_count += 1
            continue

        lot_data = {
            "item_id": item["id"],
            "quantity": 100,
            "production_date": today.isoformat(),
            "process_id": process_id,
            "worker_name": "가공담당",
            "qc_passed": True,
            "notes": "초기 시딩 데이터 (WIP)",
            "pallet_capacity": wip.get("pallette-capacity", 50)
        }

        try:
            result = client.post("/api/v1/lots", lot_data)
            lot_id = result['id']
            print(f"  ✅ {result['lot_number']} - ID: {lot_id}")
            created_count += 1

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ {item_code} - 오류: {e.response.text}")

    print("\n[완제품 LOT - PRODUCT]")
    for prod in data["product_items"]:
        item_code = f"{prod['code']}-{prod['vehicle_model']}"
        item = item_dict.get(item_code)
        if not item:
            print(f"  ⚠️  품목 없음: {item_code}")
            continue

        process_id = prod.get("process_id")
        if not process_id:
            print(f"  ⚠️  {item_code} - process_id 없음")
            skipped_count += 1
            continue

        lot_data = {
            "item_id": item["id"],
            "quantity": 50,
            "production_date": today.isoformat(),
            "process_id": process_id,
            "worker_name": "조립담당",
            "qc_passed": True,
            "notes": "초기 시딩 데이터 (PRODUCT)",
            "pallet_capacity": prod.get("pallette-capacity", 50)
        }

        try:
            result = client.post("/api/v1/lots", lot_data)
            lot_id = result['id']
            print(f"  ✅ {result['lot_number']} - ID: {lot_id}")
            created_count += 1

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ {item_code} - 오류: {e.response.text}")

    print(f"\n총 {created_count}개 생성, {skipped_count}개 스킵")


def create_physical_pallets(client: APIClient, data: dict):
    """실물 팔레트 생성"""
    print("\n" + "="*60)
    print("📦 실물 팔레트(Physical Pallet) 생성")
    print("="*60)
    
    created_count = 0
    skipped_count = 0
    
    # 기존 팔레트 조회
    existing_pallets = client.get("/api/v1/physical-pallets", params={"per_page": 100})
    existing_epcs = {p["epc"] for p in existing_pallets.get("items", []) if p.get("epc")}
    
    idx = 0
    
    # pallette-data 기반 실물 팔레트 생성
    for row in data["pallette-data"]:
        # 두 가지 형식 지원:
        # 1. {"item_id": 1, "pallettes": [[...], [...]]}
        # 2. [[...], [...]]  (리스트 of 리스트)
        if isinstance(row, dict):
            pallettes = row.get("pallettes", [])
        else:
            pallettes = row  # 리스트 형식
        
        for epc, status in pallettes:
            idx += 1
            pallet_code = f"PHY-PLT-{str(idx).zfill(5)}"
            epc_clean = epc.replace(" ", "")
            
            if epc_clean in existing_epcs:
                print(f"  ⏭️  {pallet_code} (EPC: {epc_clean[:12]}...) - 이미 존재")
                skipped_count += 1
                continue
            
            pallet_data = {
                "epc": epc_clean,
                "pallet_code": pallet_code,
                "description": f"초기 시딩 데이터 - {status}"
            }
            
            try:
                result = client.post("/api/v1/physical-pallets", pallet_data)
                print(f"  ✅ {pallet_code} (EPC: {epc_clean[:12]}...) - ID: {result['id']}")
                created_count += 1
            except requests.exceptions.HTTPError as e:
                print(f"  ❌ {pallet_code} - 오류: {e.response.text}")
    
    print(f"\n총 {created_count}개 생성, {skipped_count}개 스킵")


def print_summary(client: APIClient):
    """데이터 요약 출력"""
    print("\n" + "="*60)
    print("📊 데이터 요약")
    print("="*60)
    
    try:
        # 공정
        processes = client.get("/api/v1/processes", params={"per_page": 100})
        process_count = processes.get("total", 0)
        
        # 품목
        items = client.get("/api/v1/items", params={"per_page": 100})
        item_count = items.get("total", 0)
        raw_count = sum(1 for item in items.get("items", []) if item["item_type"] == "RAW")
        wip_count = sum(1 for item in items.get("items", []) if item["item_type"] == "WIP")
        product_count = sum(1 for item in items.get("items", []) if item["item_type"] == "PRODUCT")
        
        # 리더기 위치
        readers = client.get("/api/v1/reader-locations", params={"per_page": 100})
        reader_count = readers.get("total", 0)
        
        # LOT
        lots = client.get("/api/v1/lots", params={"per_page": 100})
        lot_count = lots.get("total", 0)
        
        # 팔레트
        pallets = client.get("/api/v1/pallets", params={"per_page": 100})
        pallet_count = pallets.get("total", 0)
        
        # 실물 팔레트
        physical_pallets = client.get("/api/v1/physical-pallets", params={"per_page": 100})
        physical_pallet_count = physical_pallets.get("total", 0)
        
        print(f"  공정 (Process): {process_count}개")
        print(f"  품목 (Item): {item_count}개")
        print(f"    - 원자재 (RAW): {raw_count}개")
        print(f"    - 재공품 (WIP): {wip_count}개")
        print(f"    - 완제품 (PRODUCT): {product_count}개")
        print(f"  리더기 위치: {reader_count}개")
        print(f"  LOT: {lot_count}개")
        print(f"  팔레트: {pallet_count}개")
        print(f"  실물 팔레트: {physical_pallet_count}개")
        print("="*60)
        
    except Exception as e:
        print(f"  ⚠️  요약 정보 조회 실패: {e}")


def main():
    """메인 함수"""
    print("=" * 60)
    print("  🚀 API 기반 DB 초기화 시작")
    print("=" * 60)
    print(f"  API 서버: {API_BASE_URL}")
    print(f"  사용자: {API_USERNAME}")
    print("=" * 60)
    
    try:
        # API 클라이언트 생성 (로그인 포함)
        client = APIClient(API_BASE_URL, API_USERNAME, API_PASSWORD)
        
        # virt_data.json 로드
        data = load_virt_data()
        
        # 데이터 생성
        create_processes(client, data)
        create_items(client, data)
        create_reader_locations(client, data)
        create_lots(client, data)
        create_physical_pallets(client, data)
        
        # 요약 출력
        print_summary(client)
        
        print("\n✅ API 기반 시딩 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
