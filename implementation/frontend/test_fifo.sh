#!/bin/bash

# FIFO 테스트 스크립트
# 사용법: ./test_fifo.sh [테스트_타입]
# 테스트 타입:
#   1 - 정상 순서 스캔 (첫 번째 팔레트부터 순서대로)
#   2 - FIFO 위반 스캔 (5번째 팔레트를 먼저 스캔)
#   3 - 혼합 테스트 (정상 + 위반)

API_URL="http://localhost:8000/api/v1"
READER_PORT="COM3"

# 현재 FIFO 큐 조회
get_fifo_queue() {
    echo "📊 현재 FIFO 대기열 (상위 10개):"
    curl -s "${API_URL}/pallets/fifo-queue" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'총 {data[\"total\"]}개의 Stock 팔레트')
print(f'\n상태별:')
print(f'  대기 중: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"WAITING\")}')
print(f'  정상 스캔: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"OK\")}')
print(f'  순서 위반: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"VIOLATION\")}')
print(f'\n첫 10개 팔레트:')
for item in data['items'][:10]:
    status_icon = '⏳' if item['scan_status'] == 'WAITING' else ('✅' if item['scan_status'] == 'OK' else '❌')
    print(f'  {status_icon} #{item[\"queue_position\"]}: {item[\"pallet_no\"]} ({item[\"item_name\"]})')
"
    echo ""
}

# RFID 스캔 시뮬레이션
scan_pallet() {
    local epc=$1
    local pallet_no=$2

    echo "🔍 스캔 중: $pallet_no (EPC: $epc)"

    response=$(curl -s -X POST "${API_URL}/rfid/scan" \
        -H "Content-Type: application/json" \
        -d "{
            \"epc\": \"$epc\",
            \"port_name\": \"$READER_PORT\",
            \"scan_time\": \"$(date -u +"%Y-%m-%dT%H:%M:%S")\"
        }")

    success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")

    if [ "$success" = "True" ]; then
        echo "✅ 스캔 성공!"
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('warning'):
    print(f\"⚠️  경고: {data['warning']['message']}\")
    if 'oldest_stock' in data['warning']:
        oldest = data['warning']['oldest_stock']
        print(f\"   더 오래된 팔레트: {oldest.get('pallet_no', 'N/A')}\")
else:
    print('✅ FIFO 순서 정상')
"
    else
        echo "❌ 스캔 실패"
        echo "$response" | python3 -m json.tool
    fi
    echo ""
}

# 테스트 1: 정상 순서 스캔
test_normal_order() {
    echo "=========================================="
    echo "테스트 1: 정상 순서 스캔"
    echo "=========================================="

    get_fifo_queue

    # 첫 3개 팔레트를 순서대로 스캔
    echo "📋 첫 3개 팔레트를 순서대로 스캔합니다..."
    echo ""

    scan_pallet "TEMP-PLT-2512220100001-001" "PLT-2512220100001-001"
    sleep 1

    scan_pallet "TEMP-PLT-2512220100001-002" "PLT-2512220100001-002"
    sleep 1

    scan_pallet "TEMP-PLT-2512220100002-001" "PLT-2512220100002-001"

    echo "✅ 정상 순서 스캔 완료"
    echo ""
    get_fifo_queue
}

# 테스트 2: FIFO 위반 스캔
test_fifo_violation() {
    echo "=========================================="
    echo "테스트 2: FIFO 위반 스캔"
    echo "=========================================="

    get_fifo_queue

    # 5번째 팔레트를 먼저 스캔 (1-4번 건너뛰기)
    echo "⚠️  순서를 어기고 5번째 팔레트를 먼저 스캔합니다..."
    echo ""

    scan_pallet "TEMP-PLT-2512220200001-001" "PLT-2512220200001-001"

    echo "❌ FIFO 위반 완료"
    echo ""
    get_fifo_queue
}

# 테스트 3: 혼합 테스트
test_mixed() {
    echo "=========================================="
    echo "테스트 3: 혼합 테스트 (정상 + 위반)"
    echo "=========================================="

    get_fifo_queue

    echo "1️⃣ 첫 번째 팔레트 스캔 (정상)"
    scan_pallet "TEMP-PLT-2512220100001-001" "PLT-2512220100001-001"
    sleep 1

    echo "2️⃣ 두 번째 건너뛰고 네 번째 스캔 (위반)"
    scan_pallet "TEMP-PLT-2512220100002-002" "PLT-2512220100002-002"
    sleep 1

    echo "3️⃣ 두 번째 팔레트 스캔 (정상)"
    scan_pallet "TEMP-PLT-2512220100001-002" "PLT-2512220100001-002"

    echo "🔄 혼합 테스트 완료"
    echo ""
    get_fifo_queue
}

# 메인
case "${1:-0}" in
    1)
        test_normal_order
        ;;
    2)
        test_fifo_violation
        ;;
    3)
        test_mixed
        ;;
    *)
        echo "FIFO 테스트 스크립트"
        echo ""
        echo "사용법: $0 [테스트_번호]"
        echo ""
        echo "테스트 목록:"
        echo "  1 - 정상 순서 스캔 (첫 3개 팔레트를 순서대로)"
        echo "  2 - FIFO 위반 스캔 (5번째 팔레트를 먼저 스캔)"
        echo "  3 - 혼합 테스트 (정상 + 위반 섞어서)"
        echo "  0 - 현재 FIFO 큐만 조회 (스캔 없음)"
        echo ""
        get_fifo_queue
        ;;
esac
