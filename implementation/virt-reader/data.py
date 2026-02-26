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

def API(endpoint="/", is_print=True):
    url = "http://localhost:8000/api/v1/" + endpoint
    
    try:
        res = requests.get(url)
        if is_print: print(f"Requesting URL: {url}")
        res.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        if is_print: print(f"Request failed: {e}")
        return None

    return res


class ConfigData:
    num_reader = 0
    reader_info = []
    pallette = []
    item_info = []
    processes = []
    
    def __init__(self, file_path):
        try:
            with open(file_path, 'r') as file:
                config = json.load(file)
        except Exception as e:
            raise RuntimeError(f"Error loading {file_path}\n - {e}")

        readers_config = config.get('reader', {})
        self.reader_info = readers_config.get('reader-info', [])
        self.num_reader = len(self.reader_info)
        self.pallette = config.get('pallette-data', [])
        self.items = { item["process_id"]: item for item in config.get('item', []) if "process_id" in item }
        self.processes = { item["id"]: item for item in config.get('processes', []) }
class Pallette_Manager:
    """팔레트 상태 관리 및 동기화 매니저"""
    class Pallette:
        def __init__(self, item_id, epc, status):
            self.item_id = item_id
            self.epc = epc
            self.status = status

        def print_pallette(self):
            print(f"Item ID: {self.item_id}, EPC: {self.epc}, Status: {self.status}")

    def __init__(self, config):
        pallettes = [
            self.Pallette(item["item_id"], epc.replace(" ", ""), status)
            for item in config.pallette
            for epc, status in item["pallettes"]
        ]
        self.pallettes = {}

        for p in pallettes:
            if p.item_id not in self.pallettes:
                self.pallettes[p.item_id] = []
            self.pallettes[p.item_id].append(p)

        self.refresh_all_pallets()

    def refresh_all_pallets(self):
        for item_id, pallettes in self.pallettes.items():
            for pallette in pallettes:
                try:
                    res = API(f"physical-pallets/epc/{pallette.epc}", is_print=False)
                    if res is None:
                        print(f"API call for EPC {pallette.epc} returned no response. (로컬 status 유지: {pallette.status})")
                        continue  # 로컬 status 그대로 유지
                    
                    if res.status_code != 200:
                        print(f"API call for EPC {pallette.epc} failed ({res.status_code}). (로컬 status 유지: {pallette.status})")
                        continue  # 로컬 status 그대로 유지
                        
                    api_status = res.json().get("status")
                    if api_status:
                        pallette.status = api_status  # API 성공 시에만 업데이트
                except Exception as e:
                    print(f"Error refreshing pallets for EPC {pallette.epc}: {e}. (로컬 status 유지: {pallette.status})")
                    # 예외 시에도 로컬 status 그대로 유지

    def get_latest_status(self, epc):
        """특정 EPC의 최신 상태를 API에서 조회.
        우선 `physical-pallets/epc/{epc}`로 상태를 조회하고 불가능하면
        기존의 `epc_to_id` 매핑을 사용해 `pallets/{id}`를 조회합니다.
        """
        # 1) try physical-pallet lookup (returns status directly)
        try:
            res = API(f"physical-pallets/epc/{epc}")
            if res and res.status_code == 200:
                status = res.json().get("status")
                if status is not None:
                    return status
        except Exception:
            # ignore and fall back
            pass

    def find_pallette_with_status(self, item_ids, target_statuses):
        """주어진 item_id(들)와 target_statuses 중 하나에 해당하는
        첫 번째 팔레트의 (epc, status)를 반환. 없으면 None.
        item_ids는 int 또는 list[int] 모두 허용.
        1) API로 최신 상태 조회 시도 (가상 팔레트 API 사용)
        2) API 조회 실패 시 로컬 캐시 status로 폴백
        """
        if not isinstance(item_ids, list):
            item_ids = [item_ids]
        log_lines = [f"[find_pallette] item_ids={item_ids}, target={target_statuses}, pallettes keys={list(self.pallettes.keys())}"]

        # API로 전체 가상 팔레트 목록을 한 번만 조회하여 EPC->status 매핑 구성
        api_status_map = {}
        try:
            res = API("pallets?per_page=100", is_print=False)
            if res is not None and res.status_code == 200:
                for p in res.json().get("items", []):
                    epc = p.get("rfid_epc")
                    status = p.get("status")
                    if epc and status:
                        api_status_map[epc] = status
        except Exception as e:
            log_lines.append(f"  pallets API 조회 실패: {e}")

        result = None
        for item_id in item_ids:
            pallettes = self.pallettes.get(item_id, [])
            if not pallettes:
                log_lines.append(f"  item_id={item_id} -> 로컬 팔레트 없음")
                continue
            for pallette in pallettes:
                current_status = pallette.status  # 로컬 캐시 기본값
                api_note = "(local)"
                if pallette.epc in api_status_map:
                    current_status = api_status_map[pallette.epc]
                    pallette.status = current_status  # 캐시 갱신
                    api_note = "(api)"
                log_lines.append(f"  epc={pallette.epc}, status={current_status} {api_note}")
                if current_status in target_statuses:
                    result = (pallette.epc, current_status)
                    break
            if result:
                break
        log_lines.append(f"  => result={result}")
        with open("log.txt", "a") as f:
            f.write("\n".join(log_lines) + "\n")
        return result

    def print_pallettes(self):
        for item_id, pallettes in self.pallettes.items():
            for pallette in pallettes:
                pallette.print_pallette()

PALLETTE_STATUS_GENERATED = "Generated"
PALLETTE_STATUS_EMPTY = "Empty"
PALLETTE_STATUS_STOCK = "Stock"
PALLETTE_STATUS_CONSUMING = "Consuming"
PALLETTE_STATUS_PRODUCING = "Producing"
PALLETTE_STATUS_FINISHED = "Finished"
PALLETTE_STATUS_DEREGISTERED = "Deregistered"

class Reader:
    def __init__(self, prot_name, process_code, process_id, in_item_id, out_item_id, cycle_time=0, pallette_manager=None, capabilities=None):
        self.process_status = "WAIT"
        self.prot_name = prot_name
        self.process_code = process_code
        self.process_id = process_id
        self.in_item_id = in_item_id
        self.out_item_id = out_item_id
        self.cycle_time = cycle_time
        self.pallette_manager = pallette_manager
        self.capabilities = capabilities if capabilities is not None else []
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
                if self.process.stdin:
                    self.process.stdin.write('exit\n')
                    self.process.stdin.flush()
                self.process.wait(timeout=2)
            except:
                self.process.kill()

    def read_output(self):
        try:
            if self.process and self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.output.append(f"[{self.prot_name}]: {line.rstrip()}")
        except:
            pass

    def write_input(self, input_str):
        if self.process and self.process.poll() is None:
            try:
                if self.process.stdin:
                    self.process.stdin.write(input_str + '\n')
                    self.process.stdin.flush()
                print(f"[{self.prot_name} FEEDBACK]: {input_str}")
                return True
            except (IOError, BrokenPipeError) as e:
                print(f"Error writing to {self.prot_name}: {e}")
                self.output.append(f"[{self.prot_name} ERROR]: Could not write to process: {e}")
                self.stop_process()
                return False
        return False

    def send_rfid(self, type):
        """RFID 스캔 명령 생성 및 전송.

        AI_README.md 진행 과정 기준:

        [O - OUT 리더기]
          1. status == Empty     -> Producing 으로 변경 (생산 시작)
          2. status == Producing -> Stock 으로 변경    (생산 완료)
             * 마지막 공정(in_item_id == -1)이면 Finished 로 변경

        [I - IN 리더기]
          1. status == Stock     -> Consuming 으로 변경     (투입 시작)
          2. status == Consuming -> Deregistered 으로 변경  (투입/소비 완료)
        """
        if type == 'O':
            # OUT 리더기가 설정에 있는지 확인
            if "OUT" not in self.capabilities:
                return "No OUT scanner"

            # OUT 리더기: out_item_id 팔레트를 대상으로 함
            target_id = self.out_item_id
            if target_id == -1:
                # For Defect/Hold (COM05, COM06 OUT), pick any pallet with status Defect or Hold
                # Or just pick any pallet that can be rolled back? 
                # Actually, for these scanners, we just want to pick a pallet that is CURRENTLY in that state.
                target_statuses = {PALLETTE_STATUS_PRODUCING, PALLETTE_STATUS_STOCK, "Hold", "Defect"}
                for item_id in self.pallette_manager.pallettes.keys():
                    result = self.pallette_manager.find_pallette_with_status(item_id, target_statuses)
                    if result:
                        epc, _ = result
                        self.write_input(f"O {epc}")
                        return f"TEST_TRIGGER_O ({epc})"
                return "No out target"

            if self.get_status() != "Running":
                return "Reader NOT Running"

            # 우선순위 1: Producing 상태 → 생산 완료 처리
            result = self.pallette_manager.find_pallette_with_status(
                target_id, {PALLETTE_STATUS_PRODUCING}
            )
            if result:
                epc, _ = result
                self.write_input(f"O {epc}")
                self.process_status = "WAIT" # End of production
                with open("log.txt", "a") as f:
                    f.write(f"[send_rfid O] END: Producing->Stock/Finished epc={epc}\n")
                return f"OUT END (Producing->Stock/Finished) ({epc})"

            # 우선순위 2: Empty 또는 Generated 상태 → 생산 시작 처리
            # 생산 시작 전, 해당 공정에 대기 중이거나 진행 중인 LOT가 있는지 확인
            # (계속해서 빈 팔레트를 스캔하여 에러가 발생하는 것을 방지)
            try:
                # WAIT 상태인 LOT 확인
                res_wait = API(f"lots?process_id={self.process_id}&status=WAIT", is_print=False)
                wait_count = res_wait.json().get("total", 0) if res_wait and res_wait.status_code == 200 else 0
                
                # PROCESS 상태인 LOT 확인
                res_proc = API(f"lots?process_id={self.process_id}&status=PROCESS", is_print=False)
                proc_count = res_proc.json().get("total", 0) if res_proc and res_proc.status_code == 200 else 0
                
                if wait_count == 0 and proc_count == 0:
                    with open("log.txt", "a") as f:
                        f.write(f"[send_rfid O] Skip: No pending/processing LOTs for process {self.process_id}\n")
                    return "NO_PENDING_LOTS"
            except Exception as e:
                with open("log.txt", "a") as f:
                    f.write(f"[send_rfid O] LOT check failed: {e}\n")
                # 에러 시에는 일단 진행 (기존 로직 유지)

            # 중간 공정은 Consuming 상태의 투입 팔레트가 있을 때만 생산 시작 가능
            if self.process_code not in ["RECEIVING", "SHEARING"]:
                input_check = self.pallette_manager.find_pallette_with_status(
                    self.in_item_id, {PALLETTE_STATUS_CONSUMING}
                )
                if not input_check:
                    return "WAITING_INPUT"

            result = self.pallette_manager.find_pallette_with_status(
                target_id, {PALLETTE_STATUS_EMPTY, PALLETTE_STATUS_GENERATED, PALLETTE_STATUS_DEREGISTERED}
            )
            if result:
                epc, status = result
                self.write_input(f"O {epc}")
                self.process_status = "PRODUCING" # Start of production
                with open("log.txt", "a") as f:
                    f.write(f"[send_rfid O] START: {status}->Producing epc={epc}\n")
                return f"OUT START ({status}->Producing) ({epc})"

            with open("log.txt", "a") as f:
                f.write(f"[send_rfid O] No candidate: all pallets in non-actionable status\n")
            return "No candidate (O)"


        elif type == 'I':
            # IN 리더기가 설정에 있는지 확인
            if "IN" not in self.capabilities:
                return "No IN scanner"

            # IN 리더기: in_item_id(들) 팔레트를 대상으로 함
            target_ids = self.in_item_id
            if target_ids == -1 or target_ids == [] or target_ids is None:
                # For Defect/Hold/Scrap (COM05, COM06, COM07 IN), pick any Producing or Stock pallet
                target_statuses = {PALLETTE_STATUS_PRODUCING, PALLETTE_STATUS_STOCK}
                for item_id in self.pallette_manager.pallettes.keys():
                    result = self.pallette_manager.find_pallette_with_status(item_id, target_statuses)
                    if result:
                        epc, _ = result
                        self.write_input(f"I {epc}")
                        return f"TEST_TRIGGER_I ({epc})"
                return "No in target"

            if self.get_status() != "Running":
                return "Reader NOT Running"

            # 우선순위 1: Consuming 상태 → 소비 완료 처리
            result = self.pallette_manager.find_pallette_with_status(
                target_ids, {PALLETTE_STATUS_CONSUMING}
            )
            if result:
                epc, _ = result
                self.write_input(f"I {epc}")
                self.process_status = "WAIT" # End of consumption
                return f"IN END (Consuming->Deregistered) ({epc})"

            # 우선순위 2: Stock 상태 → 투입 시작 처리
            result = self.pallette_manager.find_pallette_with_status(
                target_ids, {PALLETTE_STATUS_STOCK}
            )
            if result:
                epc, _ = result
                self.write_input(f"I {epc}")
                self.process_status = "CONSUMING" # Start of consumption
                return f"IN START (Stock->Consuming) ({epc})"

            return "No candidate (I)"

        else:
            return "Unknown type"

    def get_status(self):
        if self.process and self.process.poll() is None:
            return "Running"
        return "Stopped"

    def get_process_status(self):
        """UI 등에서 사용하기 위해 리더의 공정 상태를 반환합니다."""
        return self.process_status

class ReaderManager:
    def __init__(self, config, pallette_manager=None):
        self.auto_run_active = False
        self.readers = []
        self.auto_run_logs = []
        for info in config.reader_info:
            p_id = info.get('process-id')
            if p_id is not None:
                process_code = config.processes[p_id]['process_code']
                item_node = config.items.get(p_id)
                if item_node:
                    out_item_id = item_node.get('id', -1)
                    in_item_id = [x['id'] for x in item_node.get('child', [])]
                else:
                    out_item_id = -1
                    in_item_id = -1
            else:
                p_name = info.get('prot-name', '').upper()
                if "COM05" in p_name:
                    process_code = "DEFECT"
                elif "COM06" in p_name:
                    process_code = "HOLD"
                elif "COM07" in p_name:
                    process_code = "SCRAP"
                else:
                    process_code = "SYSTEM"
                
                out_item_id = -1
                in_item_id = -1

            reader = Reader(
                prot_name = info.get('prot-name', ''),
                process_code = process_code,
                process_id = p_id,
                out_item_id = out_item_id,
                in_item_id = in_item_id,
                cycle_time = info.get('cycle-time', 0),
                pallette_manager = pallette_manager,
                capabilities = [x['prefix-name'] for x in info.get('inner', [])]
            )
            self.readers.append(reader)

    def print_reader_info(self):
        for r in self.readers:
            print(f"Reader: {r.prot_name}, Process: {r.process_code} {r.out_item_id} {r.in_item_id}")
    
    def start_all(self):
        for r in self.readers: r.start_process()

    def stop_all(self):
        for r in self.readers: r.stop_process()

    def _add_auto_run_log(self, message):
        """메모리 리스트와 파일 모두에 로그 기록"""
        self.auto_run_logs.append(message)
        try:
            with open("auto_run.log", "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            # 파일 기록 실패 시 내역 출력 (stderr 등)
            print(f"Failed to write to auto_run.log: {e}", file=sys.stderr)

    def start_auto_run(self):
        if self.auto_run_active: return
        self.auto_run_active = True
        self._add_auto_run_log("🚀 Auto Run Started")
        threading.Thread(target=self._auto_run_loop, daemon=True).start()
    
    def stop_auto_run(self):
        self.auto_run_active = False
        self._add_auto_run_log("⏸️ Auto Run Stopped")

    def get_auto_run_status(self):
        return "실행 중" if self.auto_run_active else "중지됨"

    def _auto_run_loop(self):
        from datetime import datetime
        last_refresh = datetime.min
        REFRESH_INTERVAL_SECONDS = 5
        
        while self.auto_run_active:
            # 1. Refresh all pallets periodically from API
            try:
                if (datetime.now() - last_refresh).total_seconds() > REFRESH_INTERVAL_SECONDS:
                    if self.readers and self.readers[0].pallette_manager:
                        self.readers[0].pallette_manager.refresh_all_pallets()
                    last_refresh = datetime.now()
            except Exception as e:
                self._add_auto_run_log(f"⚠️ Refresh Error: {e}")

            # 2. Iterate through readers and perform automated actions
            for reader in self.readers:
                if not self.auto_run_active:
                    break

                # DEFECT/HOLD/SCRAP/SHIPPING 리더기는 자동 실행에서 제외 (수동 전용)
                if reader.process_code in ["DEFECT", "HOLD", "SCRAP", "SHIPPING"]:
                    continue
                
                # Ensure reader is running during auto run
                if reader.get_status() != "Running":
                    reader.start_process()
                    sleep(0.2)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 1. IN (소비/투입) 먼저 시도하여 생산재료를 Consuming 상태로 만듦
                res_i = reader.send_rfid('I')
                if all(x not in res_i for x in ["No candidate", "No in target", "Running", "No IN scanner"]):
                    self._add_auto_run_log(f"[{timestamp}] {reader.prot_name} IN: {res_i}")
                    sleep(0.2)

                # 2. OUT (생산) 시도 (이제 바로 위에서 시작한 투입재료를 인식 가능)
                res_o = reader.send_rfid('O')
                if all(x not in res_o for x in ["No candidate", "No out target", "Running", "WAITING_INPUT", "NO_PENDING_LOTS", "No OUT scanner"]):
                    self._add_auto_run_log(f"[{timestamp}] {reader.prot_name} OUT: {res_o}")
                    sleep(0.2)
            
            # 사이클 간 대기 시간 단축 (0.5초 정도로 더 민감하게 반응)
            sleep(0.5)

if __name__ == "__main__":
    config = ConfigData('./virt_data.json')
    pm = Pallette_Manager(config)
    rm = ReaderManager(config, pm)
    rm.print_reader_info()
    # rm.start_all() # TUI에서 시작하도록 함
    # print(pallette_manager.get_pallettes())
    # reader_manager.print_all_info()
    # reader.start_process()
    # sleep(2)
    # reader.send_rfid('I', 0)
    # sleep(5)
    # reader.stop_process()

