import subprocess
import sys
import threading
import time

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical, Container,Horizontal
    from textual.widgets import Header, Footer, Static, Input, Log, Label, Button, Markdown
    from textual.binding import Binding
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'textual'], check=True)
    sys.exit(0)



class ReaderButton(Button):
    def __init__(self, reader):
        super().__init__(f"{reader.prot_name}", classes="list-btn reader-button", id=f"btn-{reader.prot_name}")
        self.reader = reader

    def on_button_pressed(self) -> None:
        if self.reader.get_status() != "Running":
            self.reader.start_process()
        panel = self.app.query_one("#reader-panel", ReaderPanel)
        panel.reader = self.reader
        

class ReaderList(Static):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def compose(self) -> ComposeResult:
        yield Markdown("# Readers", id="reader-list-label")
        for reader in self.manager.readers:
            yield ReaderButton(reader)
        yield Button("Start All Readers", classes="list-btn", id="btn-start-all")
        yield Button("Stop All Readers", classes="list-btn", id="btn-stop-all")
        yield Label("", id="auto-run-status-label")
        yield Button("Start Auto Run", classes="list-btn auto-run-btn", id="btn-start-auto")
        yield Button("Stop Auto Run", classes="list-btn auto-run-btn", id="btn-stop-auto")
    
    def on_mount(self) -> None:
        self.set_interval(0.5, self._update_auto_status)
    
    def _update_auto_status(self):
        label = self.query_one("#auto-run-status-label", Label)
        status = self.manager.get_auto_run_status()
        if status == "실행 중":
            label.update(f"Auto Run: [green]{status}[/]")
        else:
            label.update(f"Auto Run: [red]{status}[/]")
    
    def on_button_pressed(self, message: Button.Pressed) -> None:
        if message.button.id == "btn-start-all":
            self.manager.start_all()
        elif message.button.id == "btn-stop-all":
            self.manager.stop_all()
        elif message.button.id == "btn-start-auto":
            self.manager.start_auto_run()
        elif message.button.id == "btn-stop-auto":
            self.manager.stop_auto_run()

class ReaderPanel(Static):
    def __init__(self):
        super().__init__(id="reader-panel")
        self.reader = None

    def compose(self) -> ComposeResult:
        yield Label("Reader Information", id="reader-panel-label")
        yield Log(id="reader-log")
        with Horizontal(id ="reader-panel-buttons"):
            yield Button("Start Reader", classes="reader-panel-btn", id="btn-start-reader")
            yield Button("Stop Reader", classes="reader-panel-btn", id="btn-stop-reader")
        with Horizontal():
            yield Button("REG", classes="reader-panel-pallette-btn", id="btn-reg-pallette")
            yield Button("IN", classes="reader-panel-pallette-btn", id="btn-in-pallette")
            yield Button("OUT", classes="reader-panel-pallette-btn", id="btn-out-pallette")
            yield Button("New Tag", classes="reader-panel-pallette-btn", id="btn-new-tag")
        yield Input(placeholder="RFID Tag Input", id="input-rfid-tag")

    def on_mount(self) -> None:
        threading.Thread(target=self._update_reader, daemon=True).start()

    def _update_reader(self):
        tracking_reader = None
        tracking_log_idx = 0

        label = self.query_one("#reader-panel-label", Label)
        log = self.query_one("#reader-log", Log)
        while True:
            if self.reader != tracking_reader:
                log.clear()
                tracking_reader = self.reader
                tracking_log_idx = 0
                if self.reader:
                    label.update(f"Reader: [bold green]{self.reader.prot_name}[/] ({self.reader.process_code})")
                continue
            
            if self.reader:
                # 1200줄 넘으면 오래된 것 삭제
                if len(self.reader.output) > 1200:
                    self.reader.output = self.reader.output[-1000:]
                    tracking_log_idx = max(0, tracking_log_idx - (len(self.reader.output) - 1000))

                while tracking_log_idx < len(self.reader.output):
                    log.write_line(self.reader.output[tracking_log_idx])
                    tracking_log_idx += 1
            
            time.sleep(0.1)

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if self.reader == None:
            return
        if message.input.id == "input-rfid-tag":
            rfid_tag = message.value
            if rfid_tag != "":
                # 직접 입력은 포트 접두사(I/O/R)가 포함되어야 함
                self.reader.write_input(rfid_tag)
            message.input.value = ""
    
    def on_button_pressed(self, message: Button.Pressed) -> None:
        if self.reader == None:
            return
        if message.button.id == "btn-start-reader":
            self.reader.start_process()
        elif message.button.id == "btn-stop-reader":
            self.reader.stop_process()
        elif message.button.id == "btn-reg-pallette":
            self.reader.send_rfid('R')
        elif message.button.id == "btn-in_pallette": # main.py logic based
            self.reader.send_rfid('I')
        elif message.button.id == "btn-out_pallette":
            self.reader.send_rfid('O')
        elif message.button.id == "btn-in-pallette":
            self.reader.send_rfid('I')
        elif message.button.id == "btn-out-pallette":
            self.reader.send_rfid('O')
        elif message.button.id == "btn-new-tag":
            # 자동 바인딩 테스트용 새 태그 생성 및 OUT 스캔
            import random
            new_epc = f"E28011602000{random.randint(0x6000, 0x6FFF):04X}"
            self.reader.write_input(f"O {new_epc}")
            self.reader.output.append(f"[@TUI]: Scanned NEW tag {new_epc} (Auto-binding Test)")
        
class Pallette_Status(Static):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def compose(self) -> ComposeResult:
        yield Markdown("# Pallette Status", id="pallette-status-label")
        for reader in self.manager.readers:
            yield Label(f"{reader.prot_name} In: ", id=f"pallette-in-{reader.prot_name}")
            yield Label(f"{reader.prot_name} Out: ", id=f"pallette-out-{reader.prot_name}")
            yield Label("")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._update_pallette_status)

    def _update_pallette_status(self):
        for reader in self.manager.readers:
            try:
                # Find the corresponding labels in the UI
                in_label = self.query(f"#pallette-in-{reader.prot_name}")
                out_label = self.query(f"#pallette-out-{reader.prot_name}")

                if not in_label or not out_label:
                    continue
                
                in_label = in_label.first()
                out_label = out_label.first()

                in_pals = reader.pallette_manager.get_pallettes(reader.in_pallette_id) \
                          if reader.in_pallette_id != -1 and reader.in_pallette_id < len(reader.pallette_manager.pallettes) else []
                out_pals = reader.pallette_manager.get_pallettes(reader.out_pallette_id) \
                          if reader.out_pallette_id != -1 and reader.out_pallette_id < len(reader.pallette_manager.pallettes) else []

                in_str = " ".join([f"[{p[1]}]" for p in in_pals])
                out_str = " ".join([f"[{p[1]}]" for p in out_pals])

                in_label.update(f"{reader.prot_name} In:  {in_str}")
                out_label.update(f"{reader.prot_name} Out: {out_str}")
            except Exception:
                pass

class StatusBar(Static):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.tracking_log_idx = 0

    def compose(self) -> ComposeResult:
        yield Markdown("# Status: All readers operational", id="status-label")
        for reader in self.manager.readers:
            yield Label(f"{reader.prot_name}: {reader.get_status()}", id=f"status-{reader.prot_name}")
            yield Label("")
        yield Markdown("## Auto Run Log", id="auto-run-log-title")
        yield Log(id="auto-run-log", auto_scroll=True)
        yield Pallette_Status(self.manager)
    
    def on_mount(self) -> None:
        self.set_interval(0.5, self._update_readers_status)
        self.set_interval(0.3, self._update_auto_run_log)

    def _update_readers_status(self):
        for reader in self.manager.readers:
            status_label = self.query_one(f"#status-{reader.prot_name}", Label)
            status = reader.get_status()
            process_status = reader.get_process_status()
            if (status == "Running"):
                status_label.update(f"{reader.prot_name}: [green]{status}  ({process_status})[/]")
            else:
                status_label.update(f"{reader.prot_name}: [red]{status}")
    
    def _update_auto_run_log(self):
        log_widget = self.query_one("#auto-run-log", Log)
        logs = self.manager.auto_run_logs
        
        if self.tracking_log_idx > len(logs):
            log_widget.clear()
            self.tracking_log_idx = 0
        
        while self.tracking_log_idx < len(logs):
            log_widget.write_line(logs[self.tracking_log_idx])
            self.tracking_log_idx += 1



class TextualApp(App):
    CSS = """
    .list-btn {
        margin: 1;
        text-align: center;
        width: 90%;
    }
    ReaderList {
        margin: 1;
        padding: 1;
        border: solid white;
        height: 100%;
        width: 20%;
    }
    .reader-list-label {
        margin: 1;
        text-align: center;
    }
    ReaderPanel {
        margin: 1;
        border: solid white;
        padding: 1;
        height: 100%;
        width: 39%;
    }

    #reader-log {
        height: 70%;
        width: 100%;
        border: solid #aaaaaa;
        margin-bottom: 1;
    }

    #reader-panel-buttons {
        height: 4;
    }
    .reader-panel-btn {
        margin: 1;
        width: 49%;
    }
    .reader-panel-pallette-btn {
        margin: 1;
        width: 32.5%;
    }
    .auto-run-btn {
        background: $boost;
        border: solid $success;
    }
    #auto-run-status-label {
        margin: 1;
        text-align: center;
    }
    #auto-run-log-title {
        margin-top: 1;
    }
    #auto-run-log {
        height: 15;
        width: 100%;
        border: solid #888888;
        margin-bottom: 1;
    }
    StatusBar {
        margin: 1;
        padding: 1;
        border: solid white;
        height: 100%;
        width: 39%;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ReaderList(self.manager)
            yield ReaderPanel()
            yield StatusBar(self.manager)

        yield Footer()

from main import ConfigData, ReaderManager, Pallette_Manager

if __name__ == "__main__":
    config = ConfigData('../../virt_data.json')
    pallette_manager = Pallette_Manager(config)
    manager = ReaderManager(config, pallette_manager)
    app = TextualApp(manager)
    app.run()