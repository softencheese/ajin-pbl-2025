import requests

try:
    res = requests.post("http://localhost:8000/api/v1/rfid/reader-status", json={"reader_id": "COM02", "status": "Running"})
    print(res.status_code, res.text)
except Exception as e:
    print(e)
