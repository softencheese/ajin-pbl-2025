import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { ProductionMonitorTable } from './components/ProductionMonitorTable';
import { TraceabilitySearch } from './components/TraceabilitySearch';
import { PalletScanner } from './components/PalletScanner';
import { FIFOStatusCard } from './components/FIFOStatusCard';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');

  return (
    <div className="dark h-screen w-screen flex overflow-hidden bg-[#0f0f14]">
      {/* Sidebar */}
      <Sidebar activeView={activeView} onNavigate={setActiveView} />
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'dashboard' && <Dashboard />}
        
        {activeView === 'traceability-search' && (
          <div className="p-8 space-y-6">
            <div>
              <h2>12312양방향 추적 검색</h2>
              <p className="text-muted-foreground mt-1">부품에서 코일로, 또는 코일에서 부품으로 완전한 추적성 제공</p>
            </div>
            <div className="max-w-5xl">
              <TraceabilitySearch />
            </div>
          </div>
        )}
     
        {activeView === 'master-data' && (
          <div className="p-8">
            <h2>마스터 데이터 관리</h2>
            <p className="text-muted-foreground mt-2">코일, 부품, 파레트, 공정 마스터 데이터 관리</p>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-[#151520] border border-border rounded-lg p-6 text-center">
                <h4 className="mb-2">코일 마스터</h4>
                <div className="text-3xl text-blue-400 mb-2">885</div>
                <p className="text-sm text-muted-foreground">등록된 코일</p>
              </div>
              <div className="bg-[#151520] border border-border rounded-lg p-6 text-center">
                <h4 className="mb-2">부품 마스터</h4>
                <div className="text-3xl text-green-400 mb-2">1247</div>
                <p className="text-sm text-muted-foreground">등록된 부품</p>
              </div>
              <div className="bg-[#151520] border border-border rounded-lg p-6 text-center">
                <h4 className="mb-2">파레트 마스터</h4>
                <div className="text-3xl text-yellow-400 mb-2">156</div>
                <p className="text-sm text-muted-foreground">활성 파레트</p>
              </div>
              <div className="bg-[#151520] border border-border rounded-lg p-6 text-center">
                <h4 className="mb-2">공정 마스터</h4>
                <div className="text-3xl text-purple-400 mb-2">12</div>
                <p className="text-sm text-muted-foreground">등록된 공정</p>
              </div>
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
