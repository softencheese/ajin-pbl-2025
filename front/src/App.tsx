import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { ProductionMonitorTable } from './components/ProductionMonitorTable';
import { TraceabilitySearch } from './components/TraceabilitySearch';

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
    </div>
  );
}
