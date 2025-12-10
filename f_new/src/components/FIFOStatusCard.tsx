import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

const fifoData = [
  {
    palletId: 'PLT-2024-001',
    coilId: 'COIL-2024-A1234',
    material: 'SPCC 1.0T',
    inboundDate: '2025-10-20 09:15',
    position: 1,
    isViolation: false,
    daysInStock: 7
  },
  {
    palletId: 'PLT-2024-003',
    coilId: 'COIL-2024-C9012',
    material: 'SPHC 0.8T',
    inboundDate: '2025-10-18 14:30',
    position: 3,
    isViolation: true,
    daysInStock: 9
  },
  {
    palletId: 'PLT-2024-002',
    coilId: 'COIL-2024-B5678',
    material: 'SPCC 1.2T',
    inboundDate: '2025-10-19 11:20',
    position: 2,
    isViolation: false,
    daysInStock: 8
  },
  {
    palletId: 'PLT-2024-005',
    coilId: 'COIL-2024-E7890',
    material: 'SPHC 1.0T',
    inboundDate: '2025-10-15 08:45',
    position: 5,
    isViolation: true,
    daysInStock: 12
  },
];

export function FIFOStatusCard() {
  const violations = fifoData.filter(item => item.isViolation).length;
  
  return (
    <Card className="bg-[#151520] border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3>FIFO 순서 관리</h3>
        {violations > 0 ? (
          <Badge variant="destructive" className="gap-1">
            <AlertTriangle className="size-3" />
            {violations}건 위반
          </Badge>
        ) : (
          <Badge className="bg-green-600 hover:bg-green-700 gap-1">
            <CheckCircle2 className="size-3" />
            정상
          </Badge>
        )}
      </div>

      <div className="space-y-3">
        {fifoData.map((item, idx) => (
          <div 
            key={idx}
            className={`p-4 rounded-lg border ${
              item.isViolation 
                ? 'border-red-500/50 bg-red-500/10' 
                : 'border-border bg-[#0a0a0f]'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-blue-400">{item.palletId}</span>
                  {item.isViolation && (
                    <AlertTriangle className="size-4 text-red-400" />
                  )}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  코일: <span className="font-mono text-green-400">{item.coilId}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm">{item.material}</div>
                <div className="text-xs text-muted-foreground mt-1">{item.daysInStock}일 재고</div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">입고: {item.inboundDate}</span>
              {item.isViolation && (
                <Badge variant="destructive" className="text-xs">
                  순서 위반 (예상: {item.position}번째)
                </Badge>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
