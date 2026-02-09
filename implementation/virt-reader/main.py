import json
from time import sleep
import sys
import subprocess
import threading
import requests
try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical, Container, Horizontal
    from textual.widgets import Header, Footer, Static, Input, Log, Label, Button
    from textual.binding import Binding
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'textual'], check=True)
    sys.exit(0)

def API(endpoint="/"):
    print("API called")
    url = "http://localhost:8000/api/v1/" + endpoint
    
    print(f"Requesting URL: {url}")
    try:
        res = requests.get(url)
        res.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    return res


class ConfigData:
    num_reader = 0
    reader_info = []
    pallette_id = []
    
    def __init__(self, file_path):

        try:
            with open(file_path, 'r') as file:
                config = json.load(file)
        except Exception as e:
            raise RuntimeError(f"Error loading {file_path}\n - {e}")

        readers_config = config.get('reader', {})
        self.reader_info = readers_config.get('reader-info', [])
        # Use actual info length instead of potentially buggy num-reader
        self.num_reader = len(self.reader_info)
        self.pallette_id = config.get('pallette-data', [])
        
    def print_config(self):
        print(f"Number of readers: {self.num_reader}")
        for i in range(self.num_reader):
            print(f"Reader {i+1}:")
            print(f"  prot-name: {self.reader_info[i].get('prot-name', '')}")
            print(f"  cycle-time: {self.reader_info[i].get('cycle-time', 0)}")
            print(f"  In-Pallette ID: {self.pallette_id[i]}")

class Pallette_Manager:
    """팔레트 상태 관리 및 동기화 매니저"""

    def __init__(self, config):
        self.pallettes = [] # [[EPC, Status], ...] x num_readers
        self.epc_to_id = {} # EPC -> Pallet ID
        self.config = config
        self.refresh_all_pallets()

    def refresh_all_pallets(self):
        """API로부터 모든 팔레트 상태를 가져와 동기화"""
        try:
            res = API("pallets?per_page=100")
            if res and res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    epc = item.get("rfid_epc")
                    if epc:
                        # EPC 공백 제거하여 저장
                        clean_epc = epc.replace(" ", "")
                        self.epc_to_id[clean_epc] = item.get("id")
            
            # config에 정의된 EPC들의 현재 상태를 매핑
            new_pallettes = []
            for i in range(self.config.num_reader):
                reader_pallets = []
                for epc_info in self.config.pallette_id[i]["pallettes"]:
                    epc = epc_info[0].replace(" ", "")
                    status = self.get_latest_status(epc) or epc_info[1]
                    reader_pallets.append([epc, status])
                new_pallettes.append(reader_pallets)
            self.pallettes = new_pallettes
        except Exception as e:
            print(f"Error refreshing pallets: {e}")

    def get_latest_status(self, epc):
        """특정 EPC의 최신 상태를 API에서 조회"""
        pallet_id = self.epc_to_id.get(epc)
        if not pallet_id:
            return None
        res = API(f"pallets/{pallet_id}")
        if res and res.status_code == 200:
            return res.json().get("status")
        return None

    def get_pallettes(self, list_index=None, index=None):
        if list_index is not None and index is not None:
            return self.pallettes[list_index][index]
        elif list_index is not None:
            return self.pallettes[list_index]
        return self.pallettes

    def get_pallettes_idx_for_status(self, list_index, status):
        """특정 리스트에서 해당 상태를 가진 팔레트 인덱스 반환"""
        if list_index < 0 or list_index >= len(self.pallettes):
            return -1
        
        for i, (epc, _) in enumerate(self.pallettes[list_index]):
            current_status = self.get_latest_status(epc)
            self.pallettes[list_index][i][1] = current_status
            if current_status == status:
                return i
        return -1

    def print_pallettes(self):
        for i in range(len(self.pallettes)):
            print(f"Pallette List {i}:")
            for epc, status in self.pallettes[i]:
                print(f"  EPC: {epc}, Status: {status}")

PALLETTE_STATUS_GENERATED = "Generated"
PALLETTE_STATUS_EMPTY = "Empty"
PALLETTE_STATUS_STOCK = "Stock"
PALLETTE_STATUS_CONSUMING = "Consuming"
PALLETTE_STATUS_PRODUCING = "Producing"
PALLETTE_STATUS_FINISHED = "Finished"
PALLETTE_STATUS_DEREGISTERED = "Deregistered"

class Reader:
    def __init__(self, prot_name, id, process_code, in_pallette_id, out_pallette_id, cycle_time=0, pallette_manager=None):
        self.process_status = "WAIT"
        self.process_code = process_code
        self.prot_name = prot_name
        self.id = id
        self.cycle_time = cycle_time
        self.in_pallette_id = in_pallette_id
        self.out_pallette_id = out_pallette_id
        self.pallette_manager = pallette_manager
        self.process = None
        self.output = []
    
    def start_process(self):
        if self.process and self.process.poll() is None:
            return
        try:
            self.process = subprocess.Popen(
                ['docker', 'run', '-i', '--rm', '--name', self.prot_name,
                 '--network', 'host', '-e', f'COM_PORT_BASE_NAME={self.prot_name}',
                 'embedded_virt_reader'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            print(f"Error starting {self.prot_name}: {e}")

    def stop_process(self):
        if self.process:
            try:
                self.process.stdin.write('exit\n')
                self.process.stdin.flush()
                self.process.wait(timeout=2)
            except:
                self.process.kill()

    def read_output(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output.append(f"[{self.prot_name}]: {line.rstrip()}")
        except:
            pass

    def write_input(self, input_str):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(input_str + '\n')
                self.process.stdin.flush()
                print(f"[{self.prot_name} FEEDBACK]: {input_str}")
            except (IOError, BrokenPipeError) as e:
                print(f"Error writing to {self.prot_name}: {e}")
                self.output.append(f"[{self.prot_name} ERROR]: Could not write to process: {e}")
                # Optionally, try to stop/restart the process
                self.stop_process()
                self.start_process()

    def send_rfid(self, type):
        """RFID 스캔 명령 생성 및 전송"""
        # (앞선 도구 호출에서 구현된 내용을 그대로 유지하거나 보강)
        command = ""
        res = ""
        
        if type == 'I':
            target_status = PALLETTE_STATUS_CONSUMING
            fallback_status = PALLETTE_STATUS_STOCK
            target_list_id = self.in_pallette_id
        elif type == 'O':
            if self.process_code == "SHEARING":
                target_status = PALLETTE_STATUS_EMPTY
                fallback_status = PALLETTE_STATUS_GENERATED
            else:
                target_status = PALLETTE_STATUS_PRODUCING
                fallback_status = PALLETTE_STATUS_EMPTY
            target_list_id = self.out_pallette_id
        else:
            return "Unknown"

        if target_list_id == -1: return "No target list"

        idx = self.pallette_manager.get_pallettes_idx_for_status(target_list_id, target_status)
        if idx != -1:
            res = "END"
        else:
            idx = self.pallette_manager.get_pallettes_idx_for_status(target_list_id, fallback_status)
            if idx == -1: return "No candidate"
            res = "START"

        epc = self.pallette_manager.get_pallettes(target_list_id, idx)[0]
        command = f"{type} {epc}"
        self.write_input(command)
        return f"{res} ({epc})"

    def get_status(self):
        if self.process and self.process.poll() is None:
            return "Running"
        return "Stopped"

class ReaderManager:
    def __init__(self, config, pallette_manager=None):
        self.auto_run_active = False
        self.readers = []
        self.auto_run_logs = []
        for i, info in enumerate(config.reader_info):
            # Mapping logic for 5 readers/processes
            # COM00: RECEIVING (PlaceHolder)
            # COM01: SHEARING (IN: RAW(0), OUT: SH-WIP(1))
            # COM02: PRESS (IN: SH-WIP(1), OUT: PR-WIP(2))
            # COM03: ASSEMBLY (IN: PR-WIP(2), OUT: AS-WIP(3))
            # COM04: SHIPPING (IN: AS-WIP(3), OUT: -1)
            
            in_pal_id = -1
            out_pal_id = -1
            
            p_name = info.get('prot-name', '')
            if p_name == "COM01":
                in_pal_id = 0
                out_pal_id = 1
            elif p_name == "COM02":
                in_pal_id = 1
                out_pal_id = 2
            elif p_name == "COM03":
                in_pal_id = 2
                out_pal_id = 3
            elif p_name == "COM04":
                in_pal_id = 3
                out_pal_id = -1
            
            reader = Reader(
                prot_name = p_name,
                id = i,
                process_code = info.get('process-code', ''), # JSON might not have this, we can use process-id
                in_pallette_id = in_pal_id,
                out_pallette_id = out_pal_id,
                cycle_time = info.get('cycle-time', 0),
                pallette_manager = pallette_manager 
            )
            # Auto-detect process_code if missing (based on process-id from new JSON)
            p_id = info.get('process-id')
            if not reader.process_code and p_id is not None:
                # Map based on virt_data.json processes
                p_map = {1: "RECEIVING", 2: "SHEARING", 3: "PRESS", 4: "ASSEMBLY", 5: "SHIPPING"}
                reader.process_code = p_map.get(p_id, "")

            self.readers.append(reader)
    
    def start_all(self):
        for r in self.readers: r.start_process()
    
    def stop_all(self):
        for r in self.readers: r.stop_process()
    
    def start_auto_run(self):
        if self.auto_run_active: return
        self.auto_run_active = True
        self.auto_run_logs.append("🚀 Auto Run Started")
        threading.Thread(target=self._auto_run_loop, daemon=True).start()
    
    def stop_auto_run(self):
        self.auto_run_active = False
        self.auto_run_logs.append("⏸️ Auto Run Stopped")

    def get_auto_run_status(self):
        return "실행 중" if self.auto_run_active else "중지됨"

    def _auto_run_loop(self):
        from datetime import datetime
        while self.auto_run_active:
            for reader in self.readers:
                if not self.auto_run_active: break
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 1. 생산 완료 처리 (PRODUCING -> STOCK)
                idx = reader.pallette_manager.get_pallettes_idx_for_status(reader.out_pallette_id, PALLETTE_STATUS_PRODUCING)
                if idx != -1:
                    res = reader.send_rfid('O')
                    self.auto_run_logs.append(f"[{timestamp}] {reader.prot_name} 생산완료: {res}")
                    sleep(0.5)
                    continue

                # 2. 생산 시작 처리 (EMPTY/GENERATED -> PRODUCING)
                st = PALLETTE_STATUS_EMPTY if reader.process_code != "SHEARING" else PALLETTE_STATUS_GENERATED
                idx = reader.pallette_manager.get_pallettes_idx_for_status(reader.out_pallette_id, st)
                if idx != -1:
                    res = reader.send_rfid('O')
                    self.auto_run_logs.append(f"[{timestamp}] {reader.prot_name} 생산시작: {res}")
                    sleep(0.5)
                    continue

                # 3. 투입/소비 완료 처리 (CONSUMING -> DEREGISTERED)
                idx = reader.pallette_manager.get_pallettes_idx_for_status(reader.in_pallette_id, PALLETTE_STATUS_CONSUMING)
                if idx != -1:
                    res = reader.send_rfid('I')
                    self.auto_run_logs.append(f"[{timestamp}] {reader.prot_name} 소비완료: {res}")
                    sleep(0.5)
                    continue

                # 4. 투입 시작 처리 (STOCK -> CONSUMING)
                idx = reader.pallette_manager.get_pallettes_idx_for_status(reader.in_pallette_id, PALLETTE_STATUS_STOCK)
                if idx != -1:
                    res = reader.send_rfid('I')
                    self.auto_run_logs.append(f"[{timestamp}] {reader.prot_name} 투입시작: {res}")
                    sleep(0.5)
                    continue
            
            sleep(1.5)

if __name__ == "__main__":
    config = ConfigData('../../virt_data.json')
    pm = Pallette_Manager(config)
    rm = ReaderManager(config, pm)
    # rm.start_all() # TUI에서 시작하도록 함
    # print(pallette_manager.get_pallettes())
    # reader_manager.print_all_info()
    # reader.start_process()
    # sleep(2)
    # reader.send_rfid('I', 0)
    # sleep(5)
    # reader.stop_process()

