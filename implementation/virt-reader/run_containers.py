#!/usr/bin/env python3

import subprocess
import sys
import threading
import queue
from datetime import datetime

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Header, Footer, Static, Input, Log
    from textual.binding import Binding
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'textual'], check=True)
    sys.exit(0)


class ContainerPanel(Static):
    def __init__(self, container_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container_name = container_name
        self.process = None
        self.output_queue = queue.Queue()
        self.border_title = f"📦 {container_name}"
        
    def compose(self) -> ComposeResult:
        yield Log(id=f"log-{self.container_name}", auto_scroll=True, max_lines=100)
        yield Input(placeholder=f"Type command for {self.container_name}...", 
                   id=f"input-{self.container_name}")
    
    def on_mount(self) -> None:
        self.start_container()
    
    def start_container(self):
        log = self.query_one(f"#log-{self.container_name}", Log)
        log.write_line(f"[bold green]Starting {self.container_name}...[/]")
        
        try:
            self.process = subprocess.Popen(
                ['docker', 'run', '-i', '--rm', '--name', self.container_name,
                 '--network', 'host', '-e', f'COM_PORT_BASE_NAME={self.container_name}',
                 'embedded_virt_reader'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            threading.Thread(target=self._read_output, daemon=True).start()
            self.set_interval(0.1, self._update_output)
        except Exception as e:
            log.write_line(f"[bold red]Error: {e}[/]")
    
    def _read_output(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_queue.put(line.rstrip())
        except:
            pass
    
    def _update_output(self):
        log = self.query_one(f"#log-{self.container_name}", Log)
        try:
            while True:
                line = self.output_queue.get_nowait()
                log.write_line(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/] {line}")
        except queue.Empty:
            pass
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == f"input-{self.container_name}":
            if event.value and self.process and self.process.poll() is None:
                try:
                    self.process.stdin.write(event.value + '\n')
                    self.process.stdin.flush()
                    self.query_one(f"#log-{self.container_name}", Log).write_line(
                        f"[bold cyan]> {event.value}[/]")
                except:
                    pass
            event.input.value = ""
    
    def stop_container(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()


class ContainerManagerApp(App):
    CSS = """
    Screen { layout: vertical; }
    Vertical { height: 1fr; }
    ContainerPanel { height: 1fr; border: solid green; margin: 1; padding: 1; }
    Log { height: 1fr; border: solid blue; background: $surface; scrollbar-size: 1 0; }
    Input { dock: bottom; margin-top: 1; }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "restart", "Restart All"),
    ]
    
    def __init__(self, containers):
        super().__init__()
        self.containers = containers
        self.panels = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            for container_name in self.containers:
                panel = ContainerPanel(container_name)
                self.panels.append(panel)
                yield panel
        yield Footer()
    
    def action_restart(self):
        for panel in self.panels:
            panel.stop_container()
            panel.start_container()
    
    def on_unmount(self):
        for panel in self.panels:
            panel.stop_container()


def main():
    try:
        result = subprocess.run(['docker', 'images', '--format', '{{.Repository}}'],
                              capture_output=True, text=True, check=True)
        if 'embedded_virt_reader' not in result.stdout:
            if input("Docker image not found. Build now? (y/n): ").lower() == 'y':
                subprocess.run(['docker', 'build', '-t', 'embedded_virt_reader', '.'], check=True)
            else:
                sys.exit(1)
    except:
        sys.exit(1)
    
    ContainerManagerApp(['COM00', 'COM01', 'COM02']).run()


if __name__ == "__main__":
    main()
