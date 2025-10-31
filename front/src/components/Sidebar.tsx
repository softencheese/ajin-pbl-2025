import { 
  LayoutDashboard, 
  Radio, 
  Search, 
  Package, 
  History, 
  AlertTriangle,
  Settings,
  Users,
  ScanLine,
  ArrowLeftRight,
  PackageSearch
} from 'lucide-react';
import { cn } from './ui/utils';

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
}

const navigationGroups = [
  {
    title: '실시간 모니터링',
    items: [
      { id: 'dashboard', label: '통합 대시보드', icon: LayoutDashboard },
    ]
  },
  {
    title: '재고 및 FIFO 관리',
    items: [
      { id: 'inventory-status', label: '재고 현황', icon: Package },
      { id: 'fifo-management', label: 'FIFO 관리', icon: AlertTriangle },
      { id: 'pallet-verification', label: '파레트 검증', icon: ScanLine },
    ]
  },
  {
    title: '추적성 검색',
    items: [
      { id: 'traceability-search', label: '양방향 추적 검색', icon: ArrowLeftRight },
      // { id: 'backward-trace', label: '역방향 추적 (부품→코일)', icon: History },
      // { id: 'forward-trace', label: '정방향 추적 (코일→부품)', icon: Search },
    ]
  },
  {
    title: '시스템 관리',
    items: [
      { id: 'master-data', label: '마스터 데이터 관리', icon: Settings },
      { id: 'user-management', label: '사용자 관리', icon: Users },
    ]
  }
];

export function Sidebar({ activeView, onNavigate }: SidebarProps) {
  return (
    <div className="w-72 bg-[#0a0a0f] border-r border-border h-full flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b border-border">
        <h1 className="text-blue-400">RFID 추적 시스템</h1>
        <p className="text-muted-foreground text-sm mt-1">코일 & 부품 추적성 관리</p>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {navigationGroups.map((group, idx) => (
          <div key={idx}>
            <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-3 px-3">
              {group.title}
            </h3>
            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left",
                      isActive 
                        ? "bg-blue-600 text-white" 
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <Icon className="size-4 shrink-0" />
                    <span className="text-sm">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          <div>시스템 상태: <span className="text-green-400">정상</span></div>
          <div className="mt-1">마지막 동기화: 2분 전</div>
        </div>
      </div>
    </div>
  );
}
