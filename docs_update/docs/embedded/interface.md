# 임베디드 시스템 인터페이스 명세서

## 개요
Raspberry Pi 기반 임베디드 시스템과 RFID 리더기 통신 인터페이스를 정의합니다.

**플랫폼**: Raspberry Pi 4 Model B
**언어**: C/C++
**OS**: Raspberry Pi OS (Debian 기반)

---

## 1. RFID 리더기 통신

### 1.1 지원 리더기
- **모델**: CAEN R4300P (또는 동등 사양)
- **통신 방식**: RS-232 (Serial) / TCP/IP (Ethernet)
- **안테나**: 1~4개 포트

### 1.2 시리얼 통신 (RS-232)

**포트 설정**:
```c
// 시리얼 포트 설정
#define SERIAL_PORT "/dev/ttyUSB0"  // 또는 /dev/ttyAMA0
#define BAUD_RATE 115200
#define DATA_BITS 8
#define STOP_BITS 1
#define PARITY 'N'  // None
```

**초기화 함수**:
```c
int rfid_serial_init(const char *port, int baudrate) {
    int fd = open(port, O_RDWR | O_NOCTTY | O_SYNC);
    if (fd < 0) {
        perror("Error opening serial port");
        return -1;
    }
    
    struct termios tty;
    memset(&tty, 0, sizeof(tty));
    
    if (tcgetattr(fd, &tty) != 0) {
        perror("Error from tcgetattr");
        return -1;
    }
    
    cfsetospeed(&tty, baudrate);
    cfsetispeed(&tty, baudrate);
    
    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;  // 8-bit chars
    tty.c_iflag &= ~IGNBRK;
    tty.c_lflag = 0;
    tty.c_oflag = 0;
    tty.c_cc[VMIN]  = 0;
    tty.c_cc[VTIME] = 5;  // 0.5 seconds read timeout
    
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);
    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~(PARENB | PARODD);
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;
    
    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        perror("Error from tcsetattr");
        return -1;
    }
    
    return fd;
}
```

### 1.3 TCP/IP 통신 (Ethernet)

**연결 설정**:
```c
#define READER_IP "192.168.1.100"
#define READER_PORT 9001
#define LOGICAL_PORT_NAME "READER_01"  // API 서버에 등록된 논리적 이름

int rfid_tcp_connect(const char *ip, int port) {
    int sockfd;
    struct sockaddr_in serv_addr;
    
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation error");
        return -1;
    }
    
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);
    
    if (inet_pton(AF_INET, ip, &serv_addr.sin_addr) <= 0) {
        perror("Invalid address");
        return -1;
    }
    
    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("Connection failed");
        return -1;
    }
    
    return sockfd;
}
```

---

## 2. EPC 데이터 파싱

### 2.1 EPC 포맷
```
E2 80 11 70 00 00 02 03 6B 3D 8C CD
│  │  │  │  └──────┬──────┘  └──┬──┘
│  │  │  │         │            └─ CRC/추가 데이터
│  │  │  │         └─ 시리얼 번호 (고유 ID)
│  │  │  └─ 제조사 코드
│  │  └─ 프로토콜 버전
│  └─ EPC 클래스
└─ 헤더
```

### 2.2 파싱 함수
```c
typedef struct {
    char epc[25];          // EPC 문자열 (24자 + NULL)
    uint8_t header;
    uint8_t class;
    uint8_t protocol;
    uint8_t manufacturer;
    uint64_t serial;
    bool is_valid;
} epc_data_t;

int parse_epc(const uint8_t *raw_data, size_t len, epc_data_t *epc) {
    if (len < 12) {
        return -1;  // 최소 12바이트 필요
    }
    
    // EPC를 16진수 문자열로 변환
    for (size_t i = 0; i < len && i < 12; i++) {
        sprintf(&epc->epc[i * 2], "%02X", raw_data[i]);
    }
    epc->epc[24] = '\0';
    
    // 필드 파싱
    epc->header = raw_data[0];
    epc->class = raw_data[1];
    epc->protocol = raw_data[2];
    epc->manufacturer = raw_data[3];
    
    // 시리얼 번호 (8바이트)
    epc->serial = 0;
    for (int i = 4; i < 12; i++) {
        epc->serial = (epc->serial << 8) | raw_data[i];
    }
    
    epc->is_valid = true;
    return 0;
}
```

### 2.3 중복 제거 (500ms 윈도우)
```c
#define DUPLICATE_WINDOW_MS 500
#define MAX_RECENT_TAGS 100

typedef struct {
    char epc[25];
    uint64_t timestamp_ms;
} recent_tag_t;

recent_tag_t recent_tags[MAX_RECENT_TAGS];
int recent_tag_count = 0;

uint64_t get_timestamp_ms() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000ULL + ts.tv_nsec / 1000000ULL;
}

bool is_duplicate(const char *epc) {
    uint64_t now = get_timestamp_ms();
    
    // 만료된 태그 제거
    for (int i = 0; i < recent_tag_count; ) {
        if (now - recent_tags[i].timestamp_ms > DUPLICATE_WINDOW_MS) {
            // 배열에서 제거 (마지막 요소와 교체)
            recent_tags[i] = recent_tags[--recent_tag_count];
        } else {
            i++;
        }
    }
    
    // 중복 체크
    for (int i = 0; i < recent_tag_count; i++) {
        if (strcmp(recent_tags[i].epc, epc) == 0) {
            return true;  // 중복
        }
    }
    
    // 새 태그 추가
    if (recent_tag_count < MAX_RECENT_TAGS) {
        strncpy(recent_tags[recent_tag_count].epc, epc, 24);
        recent_tags[recent_tag_count].timestamp_ms = now;
        recent_tag_count++;
    }
    
    return false;  // 새 태그
}
```

---

## 3. GPIO 제어 (부저, LED)

### 3.1 WiringPi 설정
```c
#include <wiringPi.h>

#define BUZZER_PIN 17       // GPIO 17 (물리 핀 11)
#define LED_GREEN_PIN 22    // GPIO 22 (물리 핀 15)
#define LED_YELLOW_PIN 27   // GPIO 27 (물리 핀 13)
#define LED_RED_PIN 23      // GPIO 23 (물리 핀 16)

int gpio_init() {
    if (wiringPiSetupGpio() == -1) {
        fprintf(stderr, "WiringPi setup failed\n");
        return -1;
    }
    
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(LED_GREEN_PIN, OUTPUT);
    pinMode(LED_YELLOW_PIN, OUTPUT);
    pinMode(LED_RED_PIN, OUTPUT);
    
    // 초기 상태: 모두 OFF
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_YELLOW_PIN, LOW);
    digitalWrite(LED_RED_PIN, LOW);
    
    return 0;
}
```

### 3.2 부저 제어
```c
void buzzer_beep(int duration_ms, int count, int interval_ms) {
    for (int i = 0; i < count; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(duration_ms);
        digitalWrite(BUZZER_PIN, LOW);
        
        if (i < count - 1) {
            delay(interval_ms);
        }
    }
}

// 패턴별 함수
void buzzer_success() {
    buzzer_beep(100, 1, 0);  // 1회 짧게
}

void buzzer_warning() {
    buzzer_beep(100, 3, 100);  // 3회 짧게
}

void buzzer_error() {
    buzzer_beep(300, 3, 300);  // 3회 길게
}
```

### 3.3 LED 제어
```c
typedef enum {
    LED_COLOR_NONE,
    LED_COLOR_GREEN,
    LED_COLOR_YELLOW,
    LED_COLOR_RED
} led_color_t;

void led_off_all() {
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_YELLOW_PIN, LOW);
    digitalWrite(LED_RED_PIN, LOW);
}

void led_on(led_color_t color, int duration_ms) {
    led_off_all();
    
    int pin = 0;
    switch (color) {
        case LED_COLOR_GREEN:
            pin = LED_GREEN_PIN;
            break;
        case LED_COLOR_YELLOW:
            pin = LED_YELLOW_PIN;
            break;
        case LED_COLOR_RED:
            pin = LED_RED_PIN;
            break;
        default:
            return;
    }
    
    digitalWrite(pin, HIGH);
    
    if (duration_ms > 0) {
        delay(duration_ms);
        digitalWrite(pin, LOW);
    }
}
```

### 3.4 피드백 패턴 실행
```c
typedef enum {
    PATTERN_SUCCESS,
    PATTERN_WARNING,
    PATTERN_ERROR,
    PATTERN_DEFECT
} feedback_pattern_t;

void execute_feedback(feedback_pattern_t pattern) {
    switch (pattern) {
        case PATTERN_SUCCESS:
            buzzer_beep(100, 1, 0);
            led_on(LED_COLOR_GREEN, 1000);
            break;
            
        case PATTERN_WARNING:
            buzzer_beep(100, 3, 100);
            led_on(LED_COLOR_YELLOW, 2000);
            break;
            
        case PATTERN_ERROR:
            buzzer_beep(300, 3, 300);
            led_on(LED_COLOR_RED, 3000);
            break;
            
        case PATTERN_DEFECT:
            buzzer_beep(200, 2, 200);
            led_on(LED_COLOR_RED, 2000);
            break;
    }
}
```

---

## 4. API 서버 통신

### 4.1 HTTP 클라이언트 (libcurl)

**초기화**:
```c
#include <curl/curl.h>

CURL *curl;
CURLcode res;

int api_client_init(const char *base_url) {
    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return -1;
    }
    
    return 0;
}

void api_client_cleanup() {
    if (curl) {
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
}
```

### 4.2 스캔 이벤트 전송

**JSON 생성 (json-c)**:
```c
#include <json-c/json.h>

char *create_scan_json(const char *epc, const char *port_name, uint64_t timestamp_ms) {
    json_object *jobj = json_object_new_object();
    
    json_object_object_add(jobj, "epc", json_object_new_string(epc));
    json_object_object_add(jobj, "port_name", json_object_new_string(port_name));
    
    // ISO 8601 타임스탬프 생성
    char timestamp[32];
    time_t t = timestamp_ms / 1000;
    int ms = timestamp_ms % 1000;
    struct tm *tm_info = gmtime(&t);
    strftime(timestamp, 26, "%Y-%m-%dT%H:%M:%S", tm_info);
    sprintf(timestamp + strlen(timestamp), ".%03dZ", ms);
    
    json_object_object_add(jobj, "scan_time", json_object_new_string(timestamp));
    
    // JSON 문자열 복사 (호출자가 free 해야 함)
    const char *json_str = json_object_to_json_string(jobj);
    char *result = strdup(json_str);
    
    json_object_put(jobj);  // 메모리 해제
    return result;
}
```

**HTTP POST 요청**:
```c
typedef struct {
    char *data;
    size_t size;
} response_buffer_t;

size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    response_buffer_t *mem = (response_buffer_t *)userp;
    
    char *ptr = realloc(mem->data, mem->size + realsize + 1);
    if (!ptr) {
        fprintf(stderr, "Out of memory\n");
        return 0;
    }
    
    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = 0;
    
    return realsize;
}

int api_send_scan(const char *epc, const char *port_name) {
    uint64_t timestamp = get_timestamp_ms();
    char *json_data = create_scan_json(epc, port_name, timestamp);
    
    response_buffer_t response = {0};
    
    curl_easy_setopt(curl, CURLOPT_URL, "http://192.168.1.100:8000/api/v1/rfid/scan");
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 3L);  // 3초 타임아웃
    
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    
    res = curl_easy_perform(curl);
    
    int result = 0;
    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        result = -1;
    } else {
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
        
        if (http_code == 200) {
            // 성공 - 응답 파싱하여 피드백 실행
            parse_and_execute_feedback(response.data);
            result = 0;
        } else {
            fprintf(stderr, "HTTP error: %ld\n", http_code);
            result = -1;
        }
    }
    
    curl_slist_free_all(headers);
    free(json_data);
    free(response.data);
    
    return result;
}
```

### 4.3 응답 파싱 및 피드백
```c
void parse_and_execute_feedback(const char *json_response) {
    json_object *jobj = json_tokener_parse(json_response);
    if (!jobj) {
        fprintf(stderr, "Failed to parse JSON response\n");
        return;
    }
    
    json_object *feedback_obj;
    if (json_object_object_get_ex(jobj, "feedback", &feedback_obj)) {
        json_object *pattern_obj, *count_obj, *led_obj;
        
        if (json_object_object_get_ex(feedback_obj, "pattern", &pattern_obj)) {
            const char *pattern = json_object_get_string(pattern_obj);
            
            feedback_pattern_t fb_pattern;
            if (strcmp(pattern, "SUCCESS") == 0) {
                fb_pattern = PATTERN_SUCCESS;
            } else if (strcmp(pattern, "WARNING") == 0) {
                fb_pattern = PATTERN_WARNING;
            } else if (strcmp(pattern, "ERROR") == 0) {
                fb_pattern = PATTERN_ERROR;
            } else {
                fb_pattern = PATTERN_SUCCESS;  // 기본값
            }
            
            execute_feedback(fb_pattern);
        }
    }
    
    json_object_put(jobj);
}
```

---

## 5. 로컬 큐잉 (장애 복구)

### 5.1 큐 구조
```c
#define QUEUE_MAX_SIZE 1000

typedef struct {
    char epc[25];
    char port_name[50];
    uint64_t timestamp_ms;
} queued_event_t;

typedef struct {
    queued_event_t events[QUEUE_MAX_SIZE];
    int head;
    int tail;
    int count;
    pthread_mutex_t mutex;
} event_queue_t;

event_queue_t event_queue = {0};

int queue_init() {
    event_queue.head = 0;
    event_queue.tail = 0;
    event_queue.count = 0;
    pthread_mutex_init(&event_queue.mutex, NULL);
    return 0;
}

int queue_enqueue(const char *epc, const char *port_name, uint64_t timestamp) {
    pthread_mutex_lock(&event_queue.mutex);
    
    if (event_queue.count >= QUEUE_MAX_SIZE) {
        // 큐 가득 참 - 가장 오래된 것 제거 (FIFO)
        event_queue.head = (event_queue.head + 1) % QUEUE_MAX_SIZE;
        event_queue.count--;
    }
    
    queued_event_t *event = &event_queue.events[event_queue.tail];
    strncpy(event->epc, epc, 24);
    strncpy(event->port_name, port_name, 49);
    event->timestamp_ms = timestamp;
    
    event_queue.tail = (event_queue.tail + 1) % QUEUE_MAX_SIZE;
    event_queue.count++;
    
    pthread_mutex_unlock(&event_queue.mutex);
    return 0;
}

int queue_dequeue(queued_event_t *event) {
    pthread_mutex_lock(&event_queue.mutex);
    
    if (event_queue.count == 0) {
        pthread_mutex_unlock(&event_queue.mutex);
        return -1;  // 큐 비어있음
    }
    
    *event = event_queue.events[event_queue.head];
    event_queue.head = (event_queue.head + 1) % QUEUE_MAX_SIZE;
    event_queue.count--;
    
    pthread_mutex_unlock(&event_queue.mutex);
    return 0;
}
```

### 5.2 큐 플러시 (재전송)
```c
void queue_flush() {
    queued_event_t event;
    
    while (queue_dequeue(&event) == 0) {
        // 원래 타임스탬프로 전송
        char *json_data = create_scan_json(event.epc, event.port_name, event.timestamp_ms);
        
        // API 전송 시도
        if (api_send_scan(event.epc, event.port_name) != 0) {
            // 실패 - 다시 큐에 넣기
            queue_enqueue(event.epc, event.port_name, event.timestamp_ms);
            free(json_data);
            break;  // 재시도는 다음 주기에
        }
        
        free(json_data);
        usleep(100000);  // 100ms 대기 (API 서버 부하 방지)
    }
}
```

---

## 6. 메인 루프

```c
int main(int argc, char *argv[]) {
    // 초기화
    if (gpio_init() != 0) return 1;
    if (queue_init() != 0) return 1;
    if (api_client_init("http://192.168.1.100:8000") != 0) return 1;
    
    int reader_fd = rfid_serial_init(SERIAL_PORT, BAUD_RATE);
    if (reader_fd < 0) return 1;
    
    printf("RFID system started\n");
    
    time_t last_flush = time(NULL);
    time_t last_heartbeat = time(NULL);
    
    // 메인 루프
    while (1) {
        // RFID 스캔 폴링
        uint8_t raw_data[12];
        ssize_t n = read(reader_fd, raw_data, sizeof(raw_data));
        
        if (n > 0) {
            epc_data_t epc;
            if (parse_epc(raw_data, n, &epc) == 0) {
                // 중복 체크
                if (!is_duplicate(epc.epc)) {
                    printf("Tag scanned: %s\n", epc.epc);
                    
                    // API 전송 시도
                    if (api_send_scan(epc.epc, LOGICAL_PORT_NAME) != 0) {
                        // 실패 - 큐에 저장
                        queue_enqueue(epc.epc, LOGICAL_PORT_NAME, get_timestamp_ms());
                    }
                }
            }
        }
        
        // 큐 플러시 (5초마다)
        time_t now = time(NULL);
        if (now - last_flush >= 5) {
            queue_flush();
            last_flush = now;
        }
        
        // Heartbeat (30초마다)
        if (now - last_heartbeat >= 30) {
            // send_heartbeat();
            last_heartbeat = now;
        }
        
        usleep(100000);  // 100ms 대기
    }
    
    // 정리
    close(reader_fd);
    api_client_cleanup();
    
    return 0;
}
```

---

## 7. 컴파일 및 배포

### 7.1 CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.10)
project(rfid_embedded C)

set(CMAKE_C_STANDARD 99)

# 의존성 라이브러리
find_package(CURL REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(JSON_C REQUIRED json-c)

# 소스 파일
add_executable(rfid_embedded
    src/main.c
    src/rfid_reader.c
    src/api_client.c
    src/feedback.c
    src/queue.c
)

# 링크 라이브러리
target_link_libraries(rfid_embedded
    ${CURL_LIBRARIES}
    ${JSON_C_LIBRARIES}
    wiringPi
    pthread
)

target_include_directories(rfid_embedded PRIVATE
    ${CURL_INCLUDE_DIRS}
    ${JSON_C_INCLUDE_DIRS}
    include
)
```

### 7.2 빌드
```bash
mkdir build
cd build
cmake ..
make
```

### 7.3 Systemd 서비스
```ini
[Unit]
Description=AJIN RFID Embedded System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/ajin-rfid
ExecStart=/opt/ajin-rfid/build/rfid_embedded
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 참고 문서
- 임베디드 시스템 상세 명세: `embedded-system-spec.md`
- API 엔드포인트: `../api/endpoints.md`
- 시스템 명세: `../.specify/specs/rfid-logistics-tracking-system.md`
