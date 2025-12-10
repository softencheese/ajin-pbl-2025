import { Card } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScanLine, Package } from 'lucide-react';
import { useState } from 'react';

const mockPalletData = {
  palletId: 'PLT-2024-001',
  location: 'A구역-3열-2단',
  status: '사용 가능',
  lastUpdate: '2025-10-27 14:30',
  contents: [
    { coilId: 'COIL-2024-A1234', material: 'SPCC 1.0T', weight: 1250, inboundDate: '2025-10-20 09:15', fifoPosition: 1 },
    { coilId: 'COIL-2024-A1235', material: 'SPCC 1.0T', weight: 1180, inboundDate: '2025-10-20 09:20', fifoPosition: 2 },
    { coilId: 'COIL-2024-A1236', material: 'SPCC 1.0T', weight: 1300, inboundDate: '2025-10-20 09:25', fifoPosition: 3 },
  ]
};

export function PalletScanner() {
  const [palletId, setPalletId] = useState('');
  const [showResults, setShowResults] = useState(false);

  const handleScan = () => {
    setShowResults(true);
  };

  return (
    <Card className="bg-[#151520] border-border p-6">
      <div className="flex items-center gap-2 mb-6">
        <ScanLine className="size-5 text-blue-400" />
        <h3>파레트 RFID 스캔</h3>
      </div>

      <div className="space-y-6">
        <div>
          <p className="text-sm text-muted-foreground mb-4">
            파레트의 RFID를 스캔하여 현재 적재된 코일 정보를 확인합니다
          </p>
          <div className="flex gap-2">
            <Input
              placeholder="파레트 ID 입력 또는 스캔 (예: PLT-2024-001)"
              value={palletId}
              onChange={(e) => setPalletId(e.target.value)}
              className="bg-[#0a0a0f] border-border"
            />
            <Button onClick={handleScan} className="gap-2 bg-blue-600 hover:bg-blue-700">
              <ScanLine className="size-4" />
              스캔
            </Button>
          </div>
        </div>

        {showResults && (
          <div className="space-y-4">
            {/* Pallet Info */}
            <div className="p-4 bg-[#0a0a0f] rounded-lg border border-blue-500/50">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Package className="size-4 text-blue-400" />
                    <h4>파레트 정보</h4>
                  </div>
                  <div className="font-mono text-blue-400">{mockPalletData.palletId}</div>
                </div>
                <Badge className="bg-green-600">{mockPalletData.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">위치:</span>
                  <span className="ml-2">{mockPalletData.location}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">마지막 업데이트:</span>
                  <span className="ml-2">{mockPalletData.lastUpdate}</span>
                </div>
              </div>
            </div>

            {/* Contents */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4>적재 코일 목록</h4>
                <Badge variant="outline">{mockPalletData.contents.length}개 코일</Badge>
              </div>
              <div className="space-y-2">
                {mockPalletData.contents.map((item, idx) => (
                  <div key={idx} className="p-4 bg-[#0a0a0f] rounded-lg border border-border">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-sm text-green-400">{item.coilId}</span>
                          <Badge variant="outline" className="text-xs">
                            FIFO #{item.fifoPosition}
                          </Badge>
                        </div>
                        <div className="text-sm">{item.material}</div>
                      </div>
                      <div className="text-right text-sm">
                        <div>{item.weight.toLocaleString()} kg</div>
                        <div className="text-muted-foreground text-xs mt-1">
                          입고: {item.inboundDate}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/50 rounded-lg">
              <div className="flex items-start gap-3">
                <ScanLine className="size-5 text-blue-400 mt-0.5" />
                <div className="text-sm">
                  <div className="text-blue-400 mb-1">FIFO 순서 확인</div>
                  <div className="text-muted-foreground">
                    모든 코일이 올바른 FIFO 순서로 적재되어 있습니다. 
                    가장 오래된 코일부터 우선 사용해주세요.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
