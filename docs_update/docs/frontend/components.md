ㅇ# 프론트엔드 컴포넌트 가이드

## 개요
React + TypeScript 기반 프론트엔드 애플리케이션의 주요 컴포넌트와 구조를 설명합니다.

**기술 스택**: Next.js (React 18 + Vite + TypeScript)

---

## 1. 프로젝트 구조

```
frontend/src/
├── main.tsx                # 앱 엔트리포인트
├── App.tsx                 # 루트 컴포넌트
├── api/                    # API 클라이언트
│   ├── client.ts           # Axios 인스턴스
│   ├── rfid.ts             # RFID 관련 API
│   ├── pallets.ts          # 팔레트 API
│   ├── lots.ts             # LOT API
│   └── trace.ts            # 추적성 API
├── components/             # 재사용 컴포넌트
│   ├── Layout/
│   │   ├── MainLayout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── PalletCard/
│   │   └── PalletCard.tsx
│   ├── ProcessFlow/
│   │   └── ProcessFlow.tsx
│   └── TraceTree/
│       └── TraceTree.tsx
├── pages/                  # 페이지 컴포넌트
│   ├── Dashboard/
│   │   └── DashboardPage.tsx
│   ├── ProcessMapping/
│   │   └── ProcessMappingPage.tsx
│   ├── MasterData/
│   │   ├── MaterialsPage.tsx
│   │   ├── PartsPage.tsx
│   │   └── PalletsPage.tsx
│   ├── Monitoring/
│   │   └── MonitoringPage.tsx
│   ├── Traceability/
│   │   └── TraceabilityPage.tsx
│   └── Inventory/
│       └── InventoryPage.tsx
├── hooks/                  # 커스텀 훅
│   ├── useWebSocket.ts
│   ├── usePallets.ts
│   └── useTrace.ts
├── store/                  # Zustand 스토어
│   ├── authStore.ts
│   └── realtimeStore.ts
├── types/                  # TypeScript 타입
│   ├── pallet.ts
│   ├── lot.ts
│   └── trace.ts
└── utils/
    ├── constants.ts
    └── helpers.ts
```

---

## 2. API 클라이언트

### 2.1 Axios 인스턴스
```typescript
// api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (인증 토큰)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 2.2 팔레트 API
```typescript
// api/pallets.ts
import { apiClient } from './client';
import type { Pallet, PalletCreateRequest } from '../types/pallet';

export const palletApi = {
  // 목록 조회
  async getAll(params?: { status?: string; process_id?: number; search?: string }) {
    const { data } = await apiClient.get<Pallet[]>('/pallets', { params });
    return data;
  },

  // 상세 조회
  async getById(id: number) {
    const { data } = await apiClient.get<Pallet>(`/pallets/${id}`);
    return data;
  },

  // 생성
  async create(payload: PalletCreateRequest) {
    const { data } = await apiClient.post<Pallet>('/pallets', payload);
    return data;
  },

  // LOT 연결
  async linkLot(id: number, lotId: number) {
    const { data } = await apiClient.put(`/pallets/${id}/link-lot`, { lot_id: lotId });
    return data;
  },

  // 상태 변경 (관리자)
  async updateStatus(id: number, status: string, reason?: string) {
    const { data } = await apiClient.put(`/pallets/${id}/status`, { status, reason });
    return data;
  },
};
```

---

## 3. 타입 정의

### 3.1 팔레트 타입
```typescript
// types/pallet.ts
export type PalletStatus =
  | 'Generated'
  | 'Empty'
  | 'Stock'
  | 'Consuming'
  | 'Producing'
  | 'Finished'
  | 'Deregistered'
  | 'Hold'
  | 'Defect';

export interface Pallet {
  id: number;
  pallet_no: string;
  rfid_epc: string;
  status: PalletStatus;
  lot_id?: number;
  assembly_lot_id?: number;
  current_process_id?: number;
  lot?: {
    lot_no: string;
    part: {
      part_number: string;
      part_name: string;
    };
  };
  registered_at: string;
  updated_at: string;
}

export interface PalletCreateRequest {
  pallet_no: string;
  rfid_epc: string;
}
```

### 3.2 LOT 타입
```typescript
// types/lot.ts
export interface Lot {
  id: number;
  lot_no: string;
  part_id: number;
  process_id: number;
  material_id: number;
  quantity: number;
  production_date: string;
  worker_name: string;
  qc_passed: boolean;
  part: {
    part_number: string;
    part_name: string;
  };
  process: {
    process_name: string;
  };
  material: {
    item_code: string;
  };
}
```

---

## 4. 커스텀 훅

### 4.1 WebSocket 훅
```typescript
// hooks/useWebSocket.ts
import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useWebSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(WS_URL, {
      transports: ['websocket'],
    });

    socketInstance.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  const on = useCallback(
    (event: string, callback: (data: any) => void) => {
      if (socket) {
        socket.on(event, callback);
      }
    },
    [socket]
  );

  const off = useCallback(
    (event: string, callback: (data: any) => void) => {
      if (socket) {
        socket.off(event, callback);
      }
    },
    [socket]
  );

  return { socket, isConnected, on, off };
}
```

### 4.2 팔레트 훅 (React Query)
```typescript
// hooks/usePallets.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { palletApi } from '../api/pallets';
import type { PalletCreateRequest } from '../types/pallet';

export function usePallets(params?: Parameters<typeof palletApi.getAll>[0]) {
  return useQuery({
    queryKey: ['pallets', params],
    queryFn: () => palletApi.getAll(params),
  });
}

export function usePallet(id: number) {
  return useQuery({
    queryKey: ['pallet', id],
    queryFn: () => palletApi.getById(id),
    enabled: !!id,
  });
}

export function useCreatePallet() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: PalletCreateRequest) => palletApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pallets'] });
    },
  });
}
```

---

## 5. 주요 컴포넌트

### 5.1 레이아웃
```typescript
// components/Layout/MainLayout.tsx
import React from 'react';
import { Layout, Menu } from 'antd'; //다른 라이브러리로 수정예정
import { Link, Outlet } from 'react-router-dom';
import {
  DashboardOutlined,
  SettingOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  SearchOutlined,
  InboxOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

export function MainLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ color: 'white', fontSize: '20px' }}>
        🏭 AJIN RFID 물류 추적 시스템
      </Header>
      
      <Layout>
        <Sider width={200} theme="light">
          <Menu mode="inline" defaultSelectedKeys={['dashboard']}>
            <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
              <Link to="/">대시보드</Link>
            </Menu.Item>
            <Menu.Item key="process-mapping" icon={<SettingOutlined />}>
              <Link to="/process-mapping">공정 배치</Link>
            </Menu.Item>
            <Menu.SubMenu key="master" icon={<DatabaseOutlined />} title="마스터 데이터">
              <Menu.Item key="materials">
                <Link to="/materials">원자재</Link>
              </Menu.Item>
              <Menu.Item key="parts">
                <Link to="/parts">품번</Link>
              </Menu.Item>
              <Menu.Item key="pallets">
                <Link to="/pallets">팔레트</Link>
              </Menu.Item>
            </Menu.SubMenu>
            <Menu.Item key="monitoring" icon={<MonitorOutlined />}>
              <Link to="/monitoring">모니터링</Link>
            </Menu.Item>
            <Menu.Item key="traceability" icon={<SearchOutlined />}>
              <Link to="/traceability">추적성 조회</Link>
            </Menu.Item>
            <Menu.Item key="inventory" icon={<InboxOutlined />}>
              <Link to="/inventory">재고 현황</Link>
            </Menu.Item>
          </Menu>
        </Sider>
        
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: 'white', padding: '24px', minHeight: 280 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}
```

### 5.2 팔레트 카드
```typescript
// components/PalletCard/PalletCard.tsx
import React from 'react';
import { Card, Tag, Descriptions } from 'antd'; //다른 라이브러리로 수정예정
import type { Pallet } from '../../types/pallet';

interface PalletCardProps {
  pallet: Pallet;
  onClick?: () => void;
}

const statusColors: Record<string, string> = {
  Stock: 'green',
  Consuming: 'orange',
  Producing: 'blue',
  Finished: 'purple',
  Hold: 'gold',
  Defect: 'red',
};

export function PalletCard({ pallet, onClick }: PalletCardProps) {
  return (
    <Card
      hoverable
      onClick={onClick}
      title={pallet.pallet_no}
      extra={<Tag color={statusColors[pallet.status]}>{pallet.status}</Tag>}
    >
      <Descriptions column={1} size="small">
        <Descriptions.Item label="RFID EPC">{pallet.rfid_epc}</Descriptions.Item>
        {pallet.lot && (
          <>
            <Descriptions.Item label="LOT">{pallet.lot.lot_no}</Descriptions.Item>
            <Descriptions.Item label="품번">{pallet.lot.part.part_number}</Descriptions.Item>
            <Descriptions.Item label="품명">{pallet.lot.part.part_name}</Descriptions.Item>
          </>
        )}
      </Descriptions>
    </Card>
  );
}
```

### 5.3 실시간 모니터링
```typescript
// pages/Monitoring/MonitoringPage.tsx
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Tabs, Badge } from 'antd'; //다른 라이브러리로 수정예정
import { useWebSocket } from '../../hooks/useWebSocket';
import { usePallets } from '../../hooks/usePallets';
import type { Pallet } from '../../types/pallet';

export function MonitoringPage() {
  const { socket, isConnected, on, off } = useWebSocket();
  const { data: pallets = [], refetch } = usePallets();
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  useEffect(() => {
    const handlePalletUpdate = (pallet: Pallet) => {
      refetch();
    };

    const handleScanEvent = (event: any) => {
      setRecentEvents((prev) => [event, ...prev].slice(0, 20));
    };

    on('pallet_updated', handlePalletUpdate);
    on('scan_event', handleScanEvent);

    return () => {
      off('pallet_updated', handlePalletUpdate);
      off('scan_event', handleScanEvent);
    };
  }, [on, off, refetch]);

  const columns = [
    {
      title: '팔레트',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
    },
    {
      title: 'LOT',
      dataIndex: ['lot', 'lot_no'],
      key: 'lot_no',
    },
    {
      title: '품번',
      dataIndex: ['lot', 'part', 'part_number'],
      key: 'part_number',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = {
          Stock: 'green',
          Consuming: 'orange',
          Producing: 'blue',
          Finished: 'purple',
        }[status] || 'default';
        return <Tag color={color}>{status}</Tag>;
      },
    },
  ];

  return (
    <div>
      <h1>실시간 모니터링</h1>
      
      <Card
        title="연결 상태"
        extra={
          <Badge
            status={isConnected ? 'success' : 'error'}
            text={isConnected ? '연결됨' : '연결 끊김'}
          />
        }
        style={{ marginBottom: 24 }}
      >
        <Tabs
          items={[
            {
              key: 'pallets',
              label: `팔레트 현황 (${pallets.length})`,
              children: <Table dataSource={pallets} columns={columns} rowKey="id" />,
            },
            {
              key: 'events',
              label: `최근 이벤트 (${recentEvents.length})`,
              children: (
                <div>
                  {recentEvents.map((event, i) => (
                    <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <Tag>{event.scan_time}</Tag> {event.pallet_no} - {event.status}
                    </div>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
```

---

## 6. 라우팅

```typescript
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from './components/Layout/MainLayout';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { ProcessMappingPage } from './pages/ProcessMapping/ProcessMappingPage';
import { MonitoringPage } from './pages/Monitoring/MonitoringPage';
import { TraceabilityPage } from './pages/Traceability/TraceabilityPage';
import { InventoryPage } from './pages/Inventory/InventoryPage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="process-mapping" element={<ProcessMappingPage />} />
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route path="traceability" element={<TraceabilityPage />} />
            <Route path="inventory" element={<InventoryPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

---

## 7. 상태 관리 (Zustand)

```typescript
// store/authStore.ts
import { create } from 'zustand';

interface AuthState {
  token: string | null;
  user: { username: string; role: string } | null;
  login: (token: string, user: any) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('access_token'),
  user: null,
  
  login: (token, user) => {
    localStorage.setItem('access_token', token);
    set({ token, user });
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({ token: null, user: null });
  },
}));
```

---

## 8. 환경 변수

```bash
# .env.local
VITE_API_URL=http://localhost:8000
```

---

## 9. 마스터 데이터 관리 페이지

웹 애플리케이션에서 제공하는 마스터 데이터 관리 기능입니다.

### 9.1 원자재 관리 페이지 (`MaterialsPage.tsx`)

**기능**:
- 원자재 목록 조회 (테이블 형식)
- 코일 번호, 재질명, 공급업체, 입고일자, QC 상태 표시
- 신규 원자재 등록 (모달)
- 원자재 정보 수정
- 검색 및 필터링 (QC 합격/불합격)

**주요 필드**:
- `item_code`: 코일 번호 (필수, 중복 불가)
- `material_name`: 재질명 (예: SPHC 1.6T)
- `supplier`: 공급업체
- `receipt_date`: 입고일자
- `qc_passed`: QC 합격 여부 (체크박스)

**비즈니스 규칙**:
- QC 불합격 원자재는 생산 투입 불가
- 코일 번호는 추적성을 위해 삭제 불가 (사용 이력 있는 경우)

---

### 9.2 품번 관리 페이지 (`PartsPage.tsx`)

**기능**:
- 품번 목록 조회
- 품번, 품명, 규격, 차종, 유형(중간품/조립품/완제품) 표시
- 신규 품번 등록
- 품번 정보 수정
- 필터링: 중간품/조립품, 완제품 여부

**주요 필드**:
- `part_number`: 품번 (필수, 중복 불가, 예: 71412-T6000S)
- `part_name`: 품명 (예: PNL-FR DR INR, LH)
- `part_spec`: 규격 (예: LH, 1.6T)
- `vehicle_model`: 적용 차종 (예: JX1, NE)
- `is_assembly`: 조립품 여부 (체크박스)
- `is_final_product`: 완제품 여부 (체크박스)

**비즈니스 규칙**:
- 중간품: `is_assembly = false`
- 하위 조립품: `is_assembly = true, is_final_product = false`
- 최종 완제품: `is_assembly = true, is_final_product = true`

---

### 9.3 공정 관리 페이지 (`ProcessesPage.tsx`)

**기능**:
- 공정 목록 조회 (순서대로 표시)
- 공정 코드, 공정명, 생산 라인 표시
- 신규 공정 추가
- 공정 순서 변경 (드래그 앤 드롭 또는 버튼)
- 공정 정보 수정

**주요 필드**:
- `process_code`: 공정 코드 (필수, 중복 불가, 예: SHEARING, PRESS)
- `process_name`: 공정명 (예: 샤링, 프레스, 조립, 출하)
- `process_order`: 공정 순서 (1, 2, 3, 4...)
- `production_line`: 생산 라인 (예: 400T, 1500T, 조립 라인 1)

**비즈니스 규칙**:
- 공정 순서는 중복 불가 (자동 재정렬)
- 기본 공정: 샤링(1) → 프레스(2) → 조립(3) → 출하(4)

---

### 9.4 리더기 위치 관리 페이지 (`ReaderLocationsPage.tsx`)

**기능**:
- 리더기 위치 목록 조회 (공정별 그룹화)
- 포트, 공정, 위치 타입, 설명, 활성 상태 표시
- 신규 리더기 등록 (공정과 위치 매핑)
- 리더기 정보 수정
- 리더기 활성화/비활성화

**주요 필드**:
- `port_name`: 포트 식별자 (필수, 중복 불가, 예: COM3, 192.168.1.100:9001)
- `process_id`: 연결된 공정 (드롭다운 선택)
- `location_type`: 위치 타입 (드롭다운: IN, OUT, HOLD, DEFECT, FINISH, RETURN)
- `description`: 설명 (예: 프레스 1500T 투입구 리더기)
- `is_active`: 활성 상태 (토글 스위치)

**비즈니스 규칙**:
- 포트 이름은 중복 불가 (1개 리더기 = 1개 포트)
- 각 공정별로 IN/OUT 리더기 최소 1개씩 필요
- 비활성 리더기는 스캔 이벤트 무시

---

### 9.5 LOT 관리 페이지 (`LotsPage.tsx`)

**기능**:
- LOT 목록 조회 (중간품 LOT + 조립품 LOT 통합 또는 탭 분리)
- LOT 번호, 품번, 공정, 생산일자, 수량, 작업자, QC 상태 표시
- 신규 LOT 생성 (중간품/조립품 선택)
- LOT 정보 수정
- 원자재 연결 (중간품 LOT만)
- 조립품 구성 요소 관리 (조립품 LOT만)

**중간품 LOT 필드**:
- `lot_no`: LOT 번호 (필수, 중복 불가)
- `part_id`: 품번 (드롭다운)
- `process_id`: 공정 (드롭다운)
- `material_id`: 원자재 (드롭다운, 코일 번호로 검색)
- `quantity`: 수량
- `production_date`: 생산일자
- `worker_name`: 작업자
- `qc_passed`: QC 합격 여부

**조립품 LOT 필드**:
- `lot_no`: 조립품 LOT 번호 (필수)
- `part_id`: 조립품 품번 (is_assembly = true만 선택 가능)
- `assembly_date`: 조립 완료일
- `quantity`: 조립 수량
- `worker_name`: 작업자
- `components`: 구성 요소 목록 (서브 테이블)
  - 중간품 LOT 또는 하위 조립품 LOT 선택
  - 단위당 필요 수량 입력

**비즈니스 규칙**:
- 중간품 LOT는 반드시 원자재 연결 필요 (추적성)
- 조립품 LOT는 최소 1개 이상의 구성 요소 필요
- QC 불합격 LOT는 다음 공정 투입 불가

---

### 9.6 팔레트 관리 페이지 (`PalletsPage.tsx`)

**기능**:
- 팔레트 목록 조회 (상태별, 태그 상태별 필터링)
- 팔레트 번호, RFID EPC, 상태, 태그 상태, 연결된 LOT, 현재 공정 표시
- 신규 팔레트 생성 (팔레트 번호 + RFID 태그 매칭)
- 팔레트-LOT 연결/해제
- 팔레트 상태 강제 변경 (관리자 권한)
- 팔레트 이력 조회 (모달)
- **RFID 태그 상태 변경** (정상, 손상 등)

**주요 필드**:
- `pallet_no`: 팔레트 번호 (필수, 중복 불가)
- `rfid_epc`: RFID EPC 코드 (필수, 중복 불가)
- `status`: 팔레트 상태 (9가지)
- `tag_status`: RFID 태그 상태 (AVAILABLE, IN_USE, DAMAGED)
- `lot_id` 또는 `assembly_lot_id`: 연결된 LOT

**상태 관리**:
- **팔레트 상태**: Generated, Empty, Stock, Consuming, Producing, Finished, Deregistered, Hold, Defect
- **태그 상태**: AVAILABLE(정상), IN_USE(사용중), DAMAGED(손상)
- 일반적으로 RFID 스캔으로 자동 전이되나, 관리자는 수동 변경 가능

---

## 10. 페이지 간 연동

### 10.1 데이터 흐름
```
원자재 등록 
  → LOT 생성 시 원자재 선택 
    → 팔레트-LOT 연결 
      → RFID 스캔으로 추적
```

### 10.2 탐색 경로
- 원자재 상세 → 해당 원자재로 생성된 LOT 목록 (정방향 추적)
- LOT 상세 → 사용된 원자재 정보 (역방향 추적)
- 팔레트 상세 → 연결된 LOT → 원자재/구성요소
- 리더기 위치 → 해당 공정의 LOT/팔레트 현황

---

## 참고 문서
- 웹 애플리케이션 상세 명세: `web-app-spec.md`
- API 엔드포인트: `../api/endpoints.md`
- 시스템 명세: `../docs/rfid-logistics-tracking-system.md`
