#!/usr/bin/env python3
"""
자동 실행 테스트 스크립트 - virt-reader와 API 연동 테스트
"""

import subprocess
import time
import json
import requests
from datetime import datetime

# API 엔드포인트
API_BASE = "http://localhost:8000/api/v1"

# 테스트 EPC 코드 (virt_data.json과 일치)
TEST_EPCS = {
    "raw": "E2801160200005001",     # RAW 원자재
    "shear": "E2801160200005002",   # 샤링품
    "press": "E2801160200005003",   # 프레스품
    "assembly": "E2801160200005004", # 조립품
}

# 리더 포트 매핑
READER_PORTS = {
    "shearing": "SHEARING-OUT",
    "press_in": "PRESS-IN",
    "press_out": "PRESS-OUT",
    "assembly_in": "ASSEMBLY-IN",
    "assembly_out": "ASSEMBLY-OUT",
    "shipping_in": "SHIPPING-IN",
    "shipping_out": "SHIPPING-OUT",
}

class VirtReaderContainer:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.process = None

    def start(self):
        """Docker 컨테이너 시작"""
        try:
            self.process = subprocess.Popen(
                ['docker', 'run', '-i', '--rm', '--name', self.name,
                 '--network', 'host', '-e', f'COM_PORT_BASE_NAME={self.name}',
                 'embedded_virt_reader'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            # 초기화 대기
            time.sleep(2)
            print(f"✅ {self.name} 컨테이너 시작됨")
            return True
        except Exception as e:
            print(f"❌ {self.name} 시작 실패: {e}")
            return False

    def send_command(self, command):
        """컨테이너에 명령 전송"""
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
                print(f"  [{self.name}] > {command}")
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"❌ {self.name} 명령 전송 실패: {e}")
                return False
        return False

    def stop(self):
        """컨테이너 종료"""
        if self.process:
            try:
                self.process.stdin.write('exit\n')
                self.process.stdin.flush()
                self.process.wait(timeout=2)
            except:
                self.process.kill()

def get_pallet_status(epc):
    """API에서 팔레트 상태 조회"""
    url = f"{API_BASE}/pallets?per_page=100"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        for pallet in data.get('items', []):
            if pallet.get('rfid_epc') == epc:
                return pallet
    return None

def scan_rfid(reader_name, epc, port_name):
    """RFID 스캔 시뮬레이션"""
    scan_time = datetime.now().isoformat()
    payload = {
        "epc": epc,
        "port_name": port_name,
        "scan_time": scan_time
    }
    res = requests.post(f"{API_BASE}/rfid/scan", json=payload)
    return res.json()

def print_section(title):
    """섹션 헤더 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("RFID 물류 추적 시스템 - 자동 실행 테스트")

    # 1. 컨테이너 시작
    print("Step 1: virt-reader 컨테이너 시작")
    readers = [
        VirtReaderContainer("COM01", "SHEARING"),
        VirtReaderContainer("COM02", "PRESS"),
        VirtReaderContainer("COM03", "ASSEMBLY"),
        VirtReaderContainer("COM04", "SHIPPING"),
    ]

    for reader in readers:
        if not reader.start():
            print(f"❌ {reader.name} 시작 실패로 인해 테스트 중단")
            return

    time.sleep(2)

    # 2. 초기 상태 확인
    print_section("Step 2: 초기 팔레트 상태 확인")
    for name, epc in TEST_EPCS.items():
        pallet = get_pallet_status(epc)
        if pallet:
            print(f"  {name:10} - EPC: {epc} - Status: {pallet['status']:15} - Lot: {pallet.get('lot_number') or 'None'}")
        else:
            print(f"  {name:10} - EPC: {epc} - Status: NOT FOUND")

    # 3. 샤링 공정 (Shearing)
    print_section("Step 3: 샤링 공정 (COM01 - SHEARING-OUT)")

    # 샤링 팔레트에 Lot 연결 후 생산 완료
    print("  3.1 샤링 팔레트 생산 완료 스캔...")
    result = scan_rfid("COM01", TEST_EPCS["shear"], "SHEARING-OUT")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    shear_pallet = get_pallet_status(TEST_EPCS["shear"])
    print(f"     팔레트 상태: {shear_pallet['status'] if shear_pallet else 'Unknown'}")

    # 4. 프레스 공정 (Press)
    print_section("Step 4: 프레스 공정 (COM02)")

    # 4.1 프레스 투입 (PRESS-IN)
    print("  4.1 프레스 투입 스캔 (PRESS-IN)...")
    result = scan_rfid("COM02", TEST_EPCS["shear"], "PRESS-IN")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    shear_pallet = get_pallet_status(TEST_EPCS["shear"])
    print(f"     샤링 팔레트 상태: {shear_pallet['status'] if shear_pallet else 'Unknown'}")

    # 4.2 한 번 더 스캔하여 소비 완료
    print("  4.2 소비 완료 스캔 (PRESS-IN)...")
    result = scan_rfid("COM02", TEST_EPCS["shear"], "PRESS-IN")
    print(f"     API 응답: success={result.get('success')}")

    # 4.3 프레스 배출 (PRESS-OUT)
    print("  4.3 프레스 배출 스캔 (PRESS-OUT)...")
    result = scan_rfid("COM02", TEST_EPCS["press"], "PRESS-OUT")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    press_pallet = get_pallet_status(TEST_EPCS["press"])
    print(f"     프레스 팔레트 상태: {press_pallet['status'] if press_pallet else 'Unknown'}")

    # 5. 조립 공정 (Assembly)
    print_section("Step 5: 조립 공정 (COM03)")

    # 5.1 조립 투입 (ASSEMBLY-IN)
    print("  5.1 조립 투입 스캔 (ASSEMBLY-IN)...")
    result = scan_rfid("COM03", TEST_EPCS["press"], "ASSEMBLY-IN")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    press_pallet = get_pallet_status(TEST_EPCS["press"])
    print(f"     프레스 팔레트 상태: {press_pallet['status'] if press_pallet else 'Unknown'}")

    # 5.2 소비 완료 스캔
    print("  5.2 소비 완료 스캔 (ASSEMBLY-IN)...")
    result = scan_rfid("COM03", TEST_EPCS["press"], "ASSEMBLY-IN")
    print(f"     API 응답: success={result.get('success')}")

    # 5.3 조립 배출 (ASSEMBLY-OUT)
    print("  5.3 조립 배출 스캔 (ASSEMBLY-OUT)...")
    result = scan_rfid("COM03", TEST_EPCS["assembly"], "ASSEMBLY-OUT")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    assembly_pallet = get_pallet_status(TEST_EPCS["assembly"])
    print(f"     조립 팔레트 상태: {assembly_pallet['status'] if assembly_pallet else 'Unknown'}")

    # 6. 출하 공정 (Shipping)
    print_section("Step 6: 출하 공정 (COM04)")

    # 6.1 출하 투입 (SHIPPING-IN)
    print("  6.1 출하 투입 스캔 (SHIPPING-IN)...")
    result = scan_rfid("COM04", TEST_EPCS["assembly"], "SHIPPING-IN")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)
    assembly_pallet = get_pallet_status(TEST_EPCS["assembly"])
    print(f"     조립 팔레트 상태: {assembly_pallet['status'] if assembly_pallet else 'Unknown'}")

    # 6.2 소비 완료 스캔
    print("  6.2 소비 완료 스캔 (SHIPPING-IN)...")
    result = scan_rfid("COM04", TEST_EPCS["assembly"], "SHIPPING-IN")
    print(f"     API 응답: success={result.get('success')}")

    # 6.3 출하 완료 (SHIPPING-OUT)
    print("  6.3 출하 완료 스캔 (SHIPPING-OUT)...")
    result = scan_rfid("COM04", TEST_EPCS["assembly"], "SHIPPING-OUT")
    print(f"     API 응답: success={result.get('success')}")

    time.sleep(1)

    # 7. 최종 상태 확인
    print_section("Step 7: 최종 팔레트 상태 확인")
    print("전체 생산 플로우 완료 후 상태:")
    print(f"{'공정':12} {'EPC':20} {'최종 상태':15} {'상태 코드':15}")
    print("-"*60)
    for name, epc in TEST_EPCS.items():
        pallet = get_pallet_status(epc)
        if pallet:
            print(f"{name:12} {epc:20} {pallet['status']:15} OK")
        else:
            print(f"{name:12} {epc:20} {'Unknown':15} ERR")

    # 8. 컨테이너 종료
    print_section("Step 8: 컨테이너 종료")
    for reader in readers:
        reader.stop()

    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 테스트 오류: {e}")
