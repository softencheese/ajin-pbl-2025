# 임베디드 시스템 상세 명세서

> **목적**: RFID 리더기와 API 서버 간 인터페이스 구현 명세
> **대상**: Speckit Plan - 임베디드 시스템 개발

---

## 1. 시스템 역할

### 1.1 개요
- 고정형 RFID 리더기와 API 서버 간 중계 역할
- 태그 스캔 이벤트를 실시간으로 API 서버에 전달
- API 서버로부터 피드백 명령을 수신하여 리더기 제어
- 네트워크 장애 시 로컬 큐잉으로 데이터 손실 방지

### 1.2 지원 리더기
- CAEN R4300P (또는 동등 사양)
- 통신 방식: RS-232, TCP/IP
- 안테나: 1~4개 지원

---

## 2. 핵심 기능 명세

### 2.1 RFID 태그 스캔 처리

#### 2.1.1 스캔 이벤트 수신
**입력**:
- RFID 리더기로부터 EPC 코드 수신
- 안테나 번호 (1~4)
- RSSI (신호 강도)

**처리**:
1. EPC 코드 파싱 및 포맷 검증
2. 리더기 포트 정보 확인 (COM3, READER_01 등)
3. UTC 타임스탬프 생성
4. 중복 제거 (500ms 윈도우 내 동일 EPC 무시)

**출력 (API 서버로 전송)**:
```json
POST /api/v1/rfid/scan
{
  "epc": "E2801170000002036B3D8CCD",
  "port_name": "COM3",
  "scan_time": "2025-11-17T09:23:45.123Z",
  "reader_info": {
    "model": "CAEN R4300P",
    "antenna": 1,
    "rssi": -45
  }
}
```

#### 2.1.2 중복 제거 로직
- 같은 EPC가 500ms 이내 재스캔되면 무시
- 상태: 최근 500ms 내 스캔된 EPC 목록 메모리 보관
- 500ms 경과 후 자동 제거

---

### 2.2 피드백 제어

#### 2.2.1 API 서버 응답 수신
**입력 (API 응답)**:
```json
{
  "success": true,
  "feedback": {
    "action": "BUZZER",
    "pattern": "SUCCESS",
    "count": 1,
    "led_color": "GREEN"
  }
}
```

#### 2.2.2 피드백 패턴 실행
| 패턴 | 부저 | LED | 용도 |
|------|------|-----|------|
| SUCCESS | 1회 짧게 (100ms) | 녹색 1초 | 정상 투입/완료 |
| WARNING | 3회 (100ms 간격) | 노란색 2초 | FIFO 위반 경고 |
| ERROR | 3회 길게 (300ms 간격) | 빨간색 3초 | 오투입 차단 |
| DEFECT | 2회 (200ms 간격) | 빨간색 2초 | 불량 처리 |

**구현 예시 (의사 코드)**:
```python
def execute_feedback(feedback):
    pattern = feedback['pattern']
    count = feedback['count']
    led_color = feedback['led_color']
    
    if pattern == 'SUCCESS':
        buzzer.beep(duration=100, count=1)
        led.turn_on(color=led_color, duration=1000)
    elif pattern == 'WARNING':
        buzzer.beep(duration=100, count=3, interval=100)
        led.turn_on(color=led_color, duration=2000)
    elif pattern == 'ERROR':
        buzzer.beep(duration=300, count=3, interval=300)
        led.turn_on(color=led_color, duration=3000)
    elif pattern == 'DEFECT':
        buzzer.beep(duration=200, count=2, interval=200)
        led.turn_on(color=led_color, duration=2000)
```

---

### 2.3 리더기 상태 모니터링

#### 2.3.1 Heartbeat 전송
- 주기: 30초마다
- API 엔드포인트: `POST /api/v1/rfid/reader-status`

**전송 데이터**:
```json
{
  "port_name": "COM3",
  "status": "CONNECTED",
  "last_scan_time": "2025-11-17T09:23:45.123Z",
  "uptime_seconds": 3600,
  "total_scans": 1234,
  "error_count": 0
}
```

#### 2.3.2 연결 상태 관리
**상태 정의**:
- `CONNECTED`: 정상 연결
- `DISCONNECTED`: 연결 끊김
- `ERROR`: 하드웨어 오류

**연결 끊김 감지**:
- 리더기와 통신 실패 시 즉시 감지
- 재연결 시도 (5초 간격, 최대 10회)
- 10회 실패 시 `ERROR` 상태로 전환

---

### 2.4 장애 복구

#### 2.4.1 로컬 큐잉
**목적**: API 서버 연결 실패 시 스캔 이벤트 손실 방지

**구현**:
- 메모리 큐: 최대 1000개 이벤트 저장
- 저장 형식: JSON 문자열
- 큐 오버플로우 시: 가장 오래된 이벤트 제거 (FIFO)

**큐 구조**:
```python
scan_queue = []  # 최대 1000개

def enqueue_scan(scan_event):
    if len(scan_queue) >= 1000:
        scan_queue.pop(0)  # 가장 오래된 것 제거
    scan_queue.append(scan_event)
```

#### 2.4.2 재전송 로직
**연결 복구 시**:
1. 큐에 저장된 이벤트를 순차적으로 전송
2. 각 이벤트 전송 후 100ms 대기 (API 서버 부하 방지)
3. 전송 성공 시 큐에서 제거
4. 전송 실패 시 큐에 유지 (다음 재시도)

**의사 코드**:
```python
def flush_queue():
    while len(scan_queue) > 0:
        event = scan_queue[0]
        try:
            response = api_client.post('/api/v1/rfid/scan', event)
            if response.status_code == 200:
                scan_queue.pop(0)  # 성공 시 제거
                time.sleep(0.1)  # 100ms 대기
        except Exception as e:
            logger.error(f"Failed to send queued event: {e}")
            break  # 실패 시 중단, 다음 재시도 때 계속
```

#### 2.4.3 타임스탬프 유지
- 큐에 저장된 이벤트는 원래 스캔 타임스탬프 유지
- API 서버에서 이력 기록 시 원래 시간으로 기록

---

## 3. API 서버 통신

### 3.1 엔드포인트

#### 3.1.1 스캔 이벤트 전송
- **URL**: `POST /api/v1/rfid/scan`
- **Content-Type**: `application/json`
- **타임아웃**: 3초
- **재시도**: 없음 (실패 시 큐잉)

#### 3.1.2 리더기 상태 전송
- **URL**: `POST /api/v1/rfid/reader-status`
- **주기**: 30초
- **타임아웃**: 3초
- **재시도**: 1회 (실패 시 다음 주기 대기)

### 3.2 에러 처리

#### HTTP 상태 코드별 처리
- `200 OK`: 정상 처리, 피드백 실행
- `400 Bad Request`: 로그 기록, 피드백 없음
- `500 Internal Server Error`: 로컬 큐에 저장, 재전송 대기
- `503 Service Unavailable`: 로컬 큐에 저장, 재전송 대기
- 네트워크 타임아웃: 로컬 큐에 저장, 재연결 시도

---

## 4. 리더기 제어

### 4.1 초기화
1. 리더기 전원 ON
2. 시리얼/네트워크 연결 확립
3. 리더기 설정 로드 (안테나 파워, 주파수 등)
4. 스캔 모드 시작 (연속 스캔)

### 4.2 스캔 모드
- **연속 스캔 모드**: 태그가 감지되면 즉시 이벤트 발생
- **안테나 순환**: 1번 → 2번 → 3번 → 4번 (사용 안테나만)
- **스캔 주기**: 100ms (안테나당)

### 4.3 전원 관리
- 리더기 연결 끊김 시 자동 재연결 시도
- 재연결 실패 시 시스템 재시작 (선택 사항)

---

## 5. 설정 관리

### 5.1 설정 파일 (config.json)
```json
{
  "api_server": {
    "base_url": "http://192.168.1.100:8080",
    "timeout": 3,
    "heartbeat_interval": 30
  },
  "rfid_reader": {
    "port_name": "COM3",
    "baud_rate": 115200,
    "model": "CAEN R4300P",
    "antennas": [1, 2]
  },
  "queue": {
    "max_size": 1000
  },
  "feedback": {
    "buzzer_enabled": true,
    "led_enabled": true
  }
}
```

### 5.2 환경 변수
- `API_SERVER_URL`: API 서버 주소 (config.json 오버라이드)
- `RFID_PORT`: 리더기 포트 (config.json 오버라이드)

---

## 6. 성능 요구사항

### 6.1 응답 시간
- 태그 스캔 인식: 100ms 이내
- API 서버 전송: 3초 타임아웃
- 피드백 실행: 100ms 이내

### 6.2 처리량
- 초당 스캔 처리: 10개 이상
- 큐 처리 속도: 초당 10개 (재전송 시)

### 6.3 메모리
- 최대 메모리 사용량: 100MB
- 큐 크기: 1000개 이벤트 (약 1MB)

---

## 7. 로깅

### 7.1 로그 레벨
- `DEBUG`: 모든 스캔 이벤트, 큐 상태
- `INFO`: 연결 상태 변화, API 응답
- `WARNING`: 재시도, 큐 오버플로우
- `ERROR`: API 통신 실패, 리더기 연결 끊김

### 7.2 로그 파일
- 경로: `logs/embedded-system.log`
- 로테이션: 일별, 최대 7일 보관
- 포맷: `[timestamp] [level] [message]`

**예시**:
```
[2025-11-17 09:23:45.123] [INFO] RFID tag scanned: E2801170000002036B3D8CCD
[2025-11-17 09:23:45.456] [INFO] API response: 200 OK, feedback: SUCCESS
[2025-11-17 09:23:45.789] [ERROR] API server connection failed, queuing event
```

---

## 8. 테스트

### 8.1 단위 테스트
- EPC 코드 파싱 및 검증
- 중복 제거 로직
- 피드백 패턴 실행
- 큐잉 및 재전송 로직

### 8.2 통합 테스트
- 리더기 연결 및 스캔
- API 서버 통신 (정상, 실패)
- 네트워크 장애 시나리오
- 피드백 실행 확인

### 8.3 성능 테스트
- 초당 10개 스캔 처리
- 큐 1000개 채우기 및 플러시
- 장시간 운영 (24시간) 안정성

---

## 9. 배포

### 9.1 배포 환경
- OS: Linux (Raspberry Pi) 또는 Windows
- Python 3.8 이상 (또는 동등 언어)
- 리더기 드라이버 설치

### 9.2 배포 절차
1. 설정 파일 작성 (`config.json`)
2. 리더기 연결 및 테스트
3. API 서버 연결 확인
4. 서비스 시작 (systemd 또는 Windows Service)
5. 로그 모니터링

### 9.3 서비스 관리 (systemd 예시)
```ini
[Unit]
Description=RFID Embedded System
After=network.target

[Service]
Type=simple
User=rfid
WorkingDirectory=/opt/rfid-system
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 10. 관련 문서
- **시스템 명세**: `docs/rfid-logistics-tracking-system.md`
- **API 서버 명세**: `docs/api-server-spec.md`
- **헌법**: `docs/constitution.md`
