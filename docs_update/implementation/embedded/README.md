# Embedded System (C/C++ for Raspberry Pi)

## 개요
Raspberry Pi에서 실행되는 RFID 리더기 인터페이스 및 API 클라이언트

## 필요 라이브러리
```bash
sudo apt-get install -y libcurl4-openssl-dev libjson-c-dev wiringpi
```

## 빌드 방법
```bash
mkdir build
cd build
cmake ..
make
```

## 실행
```bash
./rfid_client
```

## 주요 기능
1. RFID 리더기 시리얼/TCP 통신
2. EPC 파싱 및 유효성 검증
3. API 서버로 스캔 데이터 전송
4. GPIO 제어 (부저, LED 피드백)
5. 로컬 큐잉 (네트워크 장애 대응)

## 참고 문서
- `/docs/embedded/interface.md`
- `/docs/embedded/embedded-system-spec.md`
