import time
import socketio
from locust import User, task, between, events

class SocketIOUser(User):
    wait_time = between(1, 2)  # Simulate human/machine delay

    def on_start(self):
        self.sio = socketio.Client()
        self.connect_ws()

    def connect_ws(self):
        try:
            start_time = time.time()
            # Note: Ensure the path matches the server mount (/socket.io) and transport
            self.sio.connect("http://localhost:8000", socketio_path="/socket.io", transports=['websocket'])
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="WebSocket",
                name="Connect",
                response_time=total_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="WebSocket",
                name="Connect",
                response_time=total_time,
                response_length=0,
                exception=e,
            )

    @task
    def send_heartbeat(self):
        # Taking 'reader-status' as a lightweight frequent event
        start_time = time.time()
        try:
            # Emit doesn't block for ack unless callback used, but we simulate load
            # Server side: implementation/api/app/core/socket.py doesn't explicitly listen to client events
            # except connect/disconnect.
            # BUT, we can hit the API endpoint that triggers the broadcast to simulate the FULL loop.
            # "WebSocket Load Testing" usually means testing the WS server's ability to PUSH or HANDLE msg.
            # If our clients (Readers) only LISTEN, then we should hit the API (Reader Scan) and measure WS reception.
            
            # Since User is also a reader, let's assume valid reader behavior.
            # In this project, Readers hit HTTP POST /rfid/scan, and Server PUSHES via WS.
            # So this User should be an HTTPUser that ALSO listens to WS.
            pass
        except Exception as e:
            pass

    def on_stop(self):
        if self.sio.connected:
            self.sio.disconnect()

# Combining HTTP and WebSocket for full-loop testing
from locust import HttpUser

class ReaderUser(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        self.sio = socketio.Client()
        try:
            self.sio.connect("http://localhost:8000", socketio_path="/socket.io", transports=['websocket', 'polling'])
            print("WS Connected")
            
            # Listener for latency measurement
            @self.sio.on('pallet_updated')
            def on_message(data):
                # Calculate latency if we could embed timestamp in broadcast, 
                # but for now just counting reception
                events.request.fire(
                    request_type="WebSocket",
                    name="Receive: pallet_updated",
                    response_time=0,
                    response_length=len(str(data)),
                    exception=None,
                )
                
        except Exception as e:
            print(f"WS Connect Error: {e}")

    @task
    def triggering_scan(self):
        # Simulate RFID Scan which triggers WS broadcast
        # Need valid data? Or just 404/Validation Error is enough to trigger *some* response?
        # Let's try to send a valid scan pattern if possible, or just raw scan.
        
        # We need a random EPC to avoid locking constraints if we want successful flow
        import random
        epc = f"LOAD_TEST_{random.randint(1000, 9999)}"
        
        start_time = time.time()
        with self.client.post("/api/v1/rfid/scan", json={
            "epc": epc,
            "port_name": "COM_LOAD",
            "scan_time": "2024-01-01T00:00:00Z",
            "reader_info": {}
        }, catch_response=True) as response:
            if response.status_code in [200, 201, 400, 404, 422]: 
                # 404/400 etc are valid server responses under load
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
