import sys
import socketio
import requests
import time
import asyncio
from datetime import datetime # Import at top

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "http://localhost:8000"
TEST_EPC = "E2801170000002036B3D8CCD"  # Known EPC from specs
TEST_PORT = "COM3"

# Initialize Socket.IO client
sio = socketio.Client()
event_received = False
scan_event_data = None

@sio.event
def connect():
    print(f"[WS] Connected to {WS_URL}")

@sio.event
def connect_error(data):
    print(f"[WS] Connection failed: {data}")

@sio.event
def disconnect():
    print("[WS] Disconnected")

@sio.event
def scan_event(data):
    global event_received, scan_event_data
    print(f"[WS] Received 'scan_event': {data}")
    scan_event_data = data
    event_received = True

@sio.event
def scan_error(data):
    global event_received, scan_event_data
    print(f"[WS] Received 'scan_error': {data}")
    scan_event_data = data
    event_received = True

def run_test():
    try:
        # 1. Connect to WebSocket
        print(f"Connecting to WebSocket at {WS_URL}...")
        sio.connect(WS_URL, socketio_path='socket.io')
        
        # Wait a bit for connection
        time.sleep(1)
        
        if not sio.connected:
            print("Failed to connect to WebSocket")
            return
            
        # 2. Trigger Scan via API
        print(f"Triggering scan for EPC={TEST_EPC} on Port={TEST_PORT}...")
        payload = {
            "epc": TEST_EPC,
            "port_name": TEST_PORT,
            "scan_time": datetime.utcnow().isoformat(),
            "reader_info": {"model": "VirtualReader", "antenna": 1}
        }
        
        # We need datetime for payload
        # from datetime import datetime (Removed)
        payload["scan_time"] = datetime.utcnow().isoformat()
        
        try:
            response = requests.post(f"{API_URL}/api/v1/rfid/scan", json=payload)
            print(f"[API] Response Status: {response.status_code}")
            print(f"[API] Response Body: {response.json()}")
        except Exception as e:
            print(f"[API] Request failed: {e}")
            
        # 3. Wait for Event
        print("Waiting for WebSocket event...")
        timeout = 5
        start_time = time.time()
        
        while not event_received and (time.time() - start_time) < timeout:
            time.sleep(0.5)
            
        if event_received:
            print("\n✅ TEST PASSED: WebSocket event received!")
            print(f"Event Data: {scan_event_data}")
        else:
            print("\n❌ TEST FAILED: No WebSocket event received within timeout.")

    except Exception as e:
        print(f"Test failed with exception: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    run_test()
