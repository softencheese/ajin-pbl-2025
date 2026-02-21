

# 사전 데이터 삽입

``` md
1. 공정 프로세스 데이터 삽입

2. 아이템 데이터 삽입

3. 리더기 위치 정보 데이터 삽입
   
4. 실물 팔레트 정보 삽입
```

위의 과정을 통해 리더기가 작동시 일어날 동작에 필요한 데이터 준비완료

위의 정보를 통해 리더기가 태깅시 어느 공정, 찍힌 태그의 유효성, lot와의 연결 등 프로세스를 진행할 수 있음


# LOT 등록

API를 통해서 `LOT` 를 등록 `LOT`등록시 아래 과정을 거침

LOT 등록시 필요한 팔레트를 자동 생성
- 팔레트:실물 팔레트 N:1 연결(tag_status상태 팔레트는 항상 실물 팔레트와는 1:1 관계)


``` md
1. item, prosess ID들을 통해 공정, 아이템이 존재하는 값인지 확인 또한 공정을 통해 생산하는 item인지 확인
   
2. lot 번호 자동 생성
   
3. 데이터베이스 적재 데이터 생성
	3.1 item type == RAW
		status = STOCK
		quantity = data->quantity
		initial_quantity = data->quantity
	3.2 ITEM_TYPE != RAW
		status = WAIT
		quantity = 0
		initial_quantity = data->quantity
		
4. 투입 LOT 정보가 있으면 lot_genealogy에 기록
   
5. lot에 필요한 팔레트를 자동 생성
   팔레트생성 개수는 pallet_capacity에 의해 결정
   num_pallets = (lot.initial_quantity + pallet_capacity - 1) // pallet_capacity
   팔레트의 quantity는 lot의 pallet_capacity또는 남은 개수
```

# PROCESSES 진행

### 원자재 생성
- 원자재의 경우 LOT 생성시 STOCK(가득참)으로 생성됨

### 중간재 생성
- 리더기를 통해 RFID태그 리딩 (API /api/v1/rfid/scan)
- 서버에서 리더기 정보를 통해 processes를 확인
- RFID 태그를 통해 실물 팔레트 정보 확인
- processes에서 생산하는 item과 실물 팔레트의 item이 같은지 확인
- 팔레트가 stock 상태로 변환되면 생산완료

### 완제품 생성
- 위의 과정과 동일
- 단, 팔레트가 Finished 상태시 생산완료


### 진행 과정

입고를 제외한 첫 공정의 경우 IN 과정이 생략이됨
``` md
- out 리더기에 리딩된 실물 팔레트(RFID)가 팔레트와 바인딩 되어 있지 않다면 바인딩
	- 바인딩 전 팔레트의 tag_status는 AVAILABLE 여야함
	- 바인딩 후에는 tag_status를 IN_USE 로 변경

- 리딩시 실물 팔레트(RFID)와 바인딩된 팔레트의 status에 따라 진행
	1. status == Empty
		- Producing으로 변경
	2. status == Producing
		- Stock으로 변경
	3. else
		- 옯바르지 않은 리딩
```

마지막 공정(출하)의 경우 OUT 과정이 생략이됨
```
- IN 리더기에 리딩된 실물 팔레트가 아래 조건을 성립해야함
	- 최종생산물
	- Stock 상태
	인 팔레트와 바인딩되어 있을것

	1. status == Finished
		- Deregistered으로 변경
		- 팔레트의 tag_status를 OUT_OF_USE로 변경
```

나머지 공정
```
- IN 리더기에 리딩된 실물 팔레트가 아래 조건을 성립해야함
	- 공정에 맞는 input lot에 속해 있는 팔레트
	- Stock 상태
	인 팔레트와 바인딩되어 있을것
- out 리더기에 리딩된 실물 팔레트(RFID)가 팔레트와 바인딩 되어 있지 않다면 바인딩
	- 바인딩 전 팔레트의 tag_status는 AVAILABLE 여야함
	- 바인딩 후에는 tag_status를 IN_USE 로 변경

- IN 리더기에 리딩시
	1. status == Stock
		- Consuming으로 변경
	2. status == Consuming
		- Deregistered으로 변경
		- 팔레트의 tag_stauts를 OUT_OF_USE로 변경

- OUT 리더기에 리딩시
	1. status == Empty
		- Producing으로 변경
	2. status == Producing
		- Stock으로 변경
	2.1 생산 마지막 공정의 경우
		status == Producing
		- Finished으로 변경		
	3. else
		- 옯바르지 않은 리딩
```


# LOT

LOT의 quantity와 status는 하위 팔레트의 상태에 따라 변경

예) quantity의 산정 과정
```
LOT 하위 팔레트 3개

1. pallet01 { quantity: 10, status: Empty }
2. pallet02 { quantity: 10, status: stock }
3. pallet03 { quantity: 10, status: `Finished or Deregistered` }
   
이렇게 4개의 팔레트가 있다고 가정해보자
이때 개수로 인정의 되는것은 stock과 Finished, Deregistered 뿐이다 나머지 status는 개수에 포함되지 않는다.

현재 quantity는 20개
```

### LOT의 status 변환 과정

| 상태       | 설명         | 변환조건                                    |
| -------- | ---------- | --------------------------------------- |
| WAIT     | 대기상태       | 기본값                                     |
| PROCESS  | 공정 진행중     | 하위 팔레트중 하나라도 Consuming, Producing 상태시   |
| STOCK    | 재고 (사용 가능) | 하위 팔레트중 하나라도 STOCK 상태시 변경               |
| CONSUMED | 소비 완료      | 하위 팔레트가 모두 Deregistered 상태시 변경          |
| SHIPPED  | 출하 완료      | 하위 팔레트가 완제품 팔레트이고 모두 Deregistered상태시 변경 |
| HOLD     | 보류         | -                                       |
| DEFECT   | 불량         | -                                       |
