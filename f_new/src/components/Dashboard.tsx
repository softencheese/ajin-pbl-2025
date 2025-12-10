import { KPICard } from './KPICard';
import { DefectRateChart } from './DefectRateChart';
import { InventoryChart } from './InventoryChart';
import { ProductionMonitorTable } from './ProductionMonitorTable';
import { FIFOStatusCard } from './FIFOStatusCard';
import { Package, Radio, AlertTriangle, Box } from 'lucide-react';

export function Dashboard() {
  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h2>통합 대시보드</h2>
        <p className="text-muted-foreground mt-1">RFID 기반 코일 및 부품 추적성 실시간 모니터링</p>
      </div>

      {/* KPI Summary Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KPICard
          title="등록 코일 수"
          value={885}
          icon={Box}
          change={23}
          unit="개"
        />
        <KPICard
          title="활성 부품 수"
          value={1247}
          icon={Package}
          change={-12}
          unit="개"
        />
        <KPICard
          title="RFID 읽기 성공률"
          value={99.2}
          icon={Radio}
          change={0.5}
          unit="%"
        />
        <KPICard
          title="FIFO 위반 건수"
          value={2}
          icon={AlertTriangle}
          change={-3}
          unit="건"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DefectRateChart />
        </div>
        <FIFOStatusCard />
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <InventoryChart />
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-[#151520] border border-border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">금일 입고</div>
              <div className="text-2xl">34</div>
              <div className="text-sm text-muted-foreground mt-1">코일</div>
            </div>
            <div className="p-4 bg-[#151520] border border-border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">금일 출고</div>
              <div className="text-2xl">28</div>
              <div className="text-sm text-muted-foreground mt-1">코일</div>
            </div>
          </div>
          <div className="p-4 bg-[#151520] border border-border rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">평균 재고 일수</div>
            <div className="text-2xl">8.5</div>
            <div className="text-sm text-muted-foreground mt-1">일</div>
          </div>
        </div>
      </div>

      {/* Production Monitor Table */}
      <ProductionMonitorTable />
    </div>
  );
}
