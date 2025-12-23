# NFC Reader Scanner

NFC 리더 및 바코드 스캐너를 지원하는 C 기반 애플리케이션입니다. JSON 형식으로 데이터를 처리하고 REST API를 통해 서버와 통신합니다.

## 주요 기능

- **NFC 읽기**: NFC 태그 데이터 읽기 및 처리
- **바코드 스캔**: 바코드 인식 및 처리 (비활성화)
- **REST API 통신**: JSON 형식으로 데이터 전송
- **멀티 포트 지원**: 여러 NFC 리더 동시 관리

## 필수 의존성

빌드 및 실행에 필요한 라이브러리:

- **gcc**: C 컴파일러
- **libcurl4-openssl-dev**: HTTP 통신 라이브러리
- **libjson-c**: JSON 처리 라이브러리 (내부 포함)

### Ubuntu/Debian에서 설치

```bash
sudo apt-get update
sudo apt-get install -y libcurl4-openssl-dev build-essential
```

## 빌드

```bash
make
```

빌드 결과로 `nfc_reader` 실행 파일이 생성됩니다.

## 실행

```bash
./nfc_reader
```

## 프로젝트 구조

```
.
├── src/              # 소스 파일
│   ├── main.c       # 메인 진입점
│   ├── rfid.c       # NFC/RFID 처리
│   ├── barcode.c    # 바코드 처리
│   ├── API.c        # REST API 통신
│   ├── utils.c      # 유틸리티 함수
│   └── init.c       # 초기화 함수
├── inc/              # 헤더 파일
│   ├── main.h       # 메인 헤더
│   ├── nfc/         # NFC 관련 헤더
│   └── json/        # JSON 라이브러리 헤더
├── lib/              # 라이브러리
└── Makefile         # 빌드 설정
```

## 클린업

```bash
make clean
```

`nfc_reader` 실행 파일을 삭제합니다.

## 라이선스

프로젝트에 포함된 json-c 라이브러리는 MIT 라이선스를 따릅니다.
