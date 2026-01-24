#!/bin/bash

# FIFO 테스트 스크립트 v2 (자동 EPC 조회)
# 사용법: ./test_fifo_v2.sh [테스트_타입]

API_URL="http://localhost:8000/api/v1"
READER_PORT="COM3"

# 현재 FIFO 큐 조회 및 EPC 정보 저장
get_fifo_queue_with_epc() {
    echo "📊 현재 FIFO 대기열 조회 중..."
    curl -s "${API_URL}/pallets/fifo-queue" > /tmp/fifo_queue.json

    python3 -c "
import json
with open('/tmp/fifo_queue.json') as f:
    data = json.load(f)

print(f'총 {data[\"total\"]}개의 Stock 팔레트\n')
print('상태별:')
print(f'  대기 중: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"WAITING\")}')
print(f'  정상 스캔: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"OK\")}')
print(f'  순서 위반: {sum(1 for item in data[\"items\"] if item[\"scan_status\"] == \"VIOLATION\")}')
print(f'\n첫 10개 팔레트:')
for item in data['items'][:10]:
    status_icon = '⏳' if item['scan_status'] == 'WAITING' else ('✅' if item['scan_status'] == 'OK' else '❌')
    print(f'  {status_icon} #{item[\"queue_position\"]}: {item[\"pallet_no\"]} (EPC: {item[\"rfid_epc\"]}) - {item.get(\"item_name\", \"N/A\")}')
"
    echo ""
}

# RFID 스캔 시뮬레이션
scan_pallet_by_position() {
    local position=$1

    # FIFO 큐에서 해당 순서의 팔레트 정보 가져오기
    pallet_info=$(python3 -c "
import json
with open('/tmp/fifo_queue.json') as f:
    data = json.load(f)
    items = data['items']
    for item in items:
        if item['queue_position'] == $position:
            print(f\"{item['rfid_epc']}|||{item['pallet_no']}\")
            break
")

    if [ -z "$pallet_info" ]; then
        echo "❌ 순서 #$position의 팔레트를 찾을 수 없습니다."
        return
    fi

    local epc=$(echo "$pallet_info" | cut -d'|' -f1)
    local pallet_no=$(echo "$pallet_info" | cut -d'|' -f4)

    echo "🔍 스캔 중: #$position - $pallet_no (EPC: $epc)"

    response=$(curl -s -X POST "${API_URL}/rfid/scan" \
        -H "Content-Type: application/json" \
        -d "{
            \"epc\": \"$epc\",
            \"port_name\": \"$READER_PORT\",
            \"scan_time\": \"$(date -u +"%Y-%m-%dT%H:%M:%S")\"
        }")

    success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

    if [ "$success" = "True" ]; then
        echo "✅ 스캔 성공!"
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('warning'):
        print(f\"⚠️  경고: {data['warning']['message']}\")
        if 'oldest_stock' in data['warning']:
            oldest = data['warning']['oldest_stock']
            print(f\"   더 오래된 팔레트: {oldest.get('pallet_no', 'N/A')}\")
    else:
        print('✅ FIFO 순서 정상')
except:
    pass
" 2>/dev/null
    else
        echo "❌ 스캔 실패"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -20
    fi
    echo ""
}

# 테스트 1: 정상 순서 스캔
test_normal_order() {
    echo "=========================================="
    echo "테스트 1: 정상 순서 스캔"
    echo "=========================================="

    get_fifo_queue_with_epc

    echo "📋 첫 3개 팔레트를 순서대로 스캔합니다..."
    echo ""

    scan_pallet_by_position 1
    sleep 1

    scan_pallet_by_position 2
    sleep 1

    scan_pallet_by_position 3

    echo "✅ 정상 순서 스캔 완료"
    echo ""
    get_fifo_queue_with_epc
}

# 테스트 2: FIFO 위반 스캔
test_fifo_violation() {
    echo "=========================================="
    echo "테스트 2: FIFO 위반 스캔"
    echo "=========================================="

    get_fifo_queue_with_epc

    echo "⚠️  순서를 어기고 5번째 팔레트를 먼저 스캔합니다..."
    echo ""

    scan_pallet_by_position 5

    echo "❌ FIFO 위반 완료"
    echo ""
    get_fifo_queue_with_epc
}

# 테스트 3: 혼합 테스트
test_mixed() {
    echo "=========================================="
    echo "테스트 3: 혼합 테스트 (정상 + 위반)"
    echo "=========================================="

    get_fifo_queue_with_epc

    echo "1️⃣ 첫 번째 팔레트 스캔 (정상)"
    scan_pallet_by_position 1
    sleep 1

    echo "2️⃣ 두 번째 건너뛰고 네 번째 스캔 (위반)"
    scan_pallet_by_position 4
    sleep 1

    echo "3️⃣ 두 번째 팔레트 스캔 (정상)"
    scan_pallet_by_position 2

    echo "🔄 혼합 테스트 완료"
    echo ""
    get_fifo_queue_with_epc
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
        echo "FIFO 테스트 스크립트 v2"
        echo ""
        echo "사용법: $0 [테스트_번호]"
        echo ""
        echo "테스트 목록:"
        echo "  1 - 정상 순서 스캔 (첫 3개 팔레트를 순서대로)"
        echo "  2 - FIFO 위반 스캔 (5번째 팔레트를 먼저 스캔)"
        echo "  3 - 혼합 테스트 (정상 + 위반 섞어서)"
        echo "  0 - 현재 FIFO 큐만 조회 (스캔 없음)"
        echo ""
        get_fifo_queue_with_epc
        ;;
esac
