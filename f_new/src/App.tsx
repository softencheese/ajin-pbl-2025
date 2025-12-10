import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { ProductionMonitorTable } from './components/ProductionMonitorTable';
import { TraceabilitySearch } from './components/TraceabilitySearch';
import { PalletScanner } from './components/PalletScanner';
import { FIFOStatusCard } from './components/FIFOStatusCard';
import { MasterDataManagement } from './components/MasterDataManagement';
import { Toaster } from './components/ui/sonner';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');

  return (
    <div className="dark h-screen w-screen flex overflow-hidden bg-[#0f0f14]">
      {/* Sidebar */}
      <Sidebar activeView={activeView} onNavigate={setActiveView} />
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'dashboard' && <Dashboard />}
        
        {activeView === 'production-monitor' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>생산 공정 모니터링</h2>
              <p className="text-muted-foreground mt-1">각 공정 단계별 RFID 리더기로 수집된 실시간 부품 데이터</p>
            </div>
            <ProductionMonitorTable />
          </div>
        )}
        
        {activeView === 'process-status' && (
          <div className="p-8">
            <h2>공정별 현황</h2>
            <p className="text-muted-foreground mt-2">쉐어링, 프레싱, 조립 등 각 공정의 상세 현황</p>
            <div className="mt-8 bg-[#151520] border border-border rounded-lg p-12 text-center text-muted-foreground">
              공정별 상세 현황 - 개발 예정
            </div>
          </div>
        )}
        
        {activeView === 'inventory-status' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>재고 현황</h2>
              <p className="text-muted-foreground mt-1">원자재 코일 및 중간 부품 재고 관리</p>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-[#151520] border border-border rounded-lg p-12 text-center text-muted-foreground">
                코일 재고 목록 - 개발 예정
              </div>
              <div className="bg-[#151520] border border-border rounded-lg p-12 text-center text-muted-foreground">
                부품 재고 목록 - 개발 예정
              </div>
            </div>
          </div>
        )}
        
        {activeView === 'fifo-management' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>FIFO 관리</h2>
              <p className="text-muted-foreground mt-1">선입선출 원칙 관리 및 순서 위반 모니터링</p>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FIFOStatusCard />
              <div className="bg-[#151520] border border-border rounded-lg p-6">
                <h3 className="mb-4">FIFO 위반 알림</h3>
                <div className="space-y-3">
                  <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm">PLT-2024-003</span>
                      <span className="text-xs text-muted-foreground">2025-10-27 14:15</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      FIFO 순서 위반: 더 오래된 코일이 먼저 사용되어야 합니다
                    </div>
                  </div>
                  <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm">PLT-2024-005</span>
                      <span className="text-xs text-muted-foreground">2025-10-27 13:45</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      재고 기간 초과: 12일 이상 보관 중
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeView === 'pallet-verification' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>파레트 검증</h2>
              <p className="text-muted-foreground mt-1">RFID 스캔으로 파레트 내용물 확인</p>
            </div>
            <div className="max-w-4xl">
              <PalletScanner />
            </div>
          </div>
        )}
        
        {activeView === 'traceability-search' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>양방향 추적 검색</h2>
              <p className="text-muted-foreground mt-1">부품에서 코일로, 또는 코일에서 부품으로 완전한 추적성 제공</p>
            </div>
            <div className="max-w-5xl">
              <TraceabilitySearch />
            </div>
          </div>
        )}
        
        {activeView === 'backward-trace' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>역방향 추적 (부품 → 코일)</h2>
              <p className="text-muted-foreground mt-1">최종 제품에서 원자재 코일까지 역추적</p>
            </div>
            <div className="max-w-5xl">
              <TraceabilitySearch />
            </div>
          </div>
        )}
        
        {activeView === 'forward-trace' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>정방향 추적 (코일 → 부품)</h2>
              <p className="text-muted-foreground mt-1">원자재 코일에서 생산된 모든 부품 조회</p>
            </div>
            <div className="max-w-5xl">
              <TraceabilitySearch />
            </div>
          </div>
        )}
        
        {activeView === 'master-data' && (
          <MasterDataManagement />
        )}
        
        {activeView === 'user-management' && (
          <div className="p-8">
            <h2>사용자 관리</h2>
            <p className="text-muted-foreground mt-2">시스템 접근 권한 및 사용자 계정 관리</p>
            <div className="mt-8 bg-[#151520] border border-border rounded-lg p-12 text-center text-muted-foreground">
              사용자 관리 인터페이스 - 개발 예정
            </div>
          </div>
        )}
      </div>
      
      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}