import { Card } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Search, ArrowRight, ArrowLeft } from 'lucide-react';
import { useState } from 'react';

// Mock data for traceability
const mockBackwardTrace = {
  partId: 'PART-2024-10001',
  partName: '프론트 도어 패널',
  carModel: 'K5 세단',
  history: [
    { level: '최종 제품', id: 'PART-2024-10001', name: '프론트 도어 패널', process: '조립 완료', timestamp: '2025-10-27 14:32' },
    { level: '중간 부품', id: 'PART-2024-09856', name: '도어 외판', process: '프레싱', timestamp: '2025-10-27 12:15' },
    { level: '중간 부품', id: 'PART-2024-09123', name: '블랭크 재단', process: '쉐어링', timestamp: '2025-10-27 09:30' },
    { level: '원자재', id: 'COIL-2024-A1234', name: 'SPCC 1.0T 코일', process: '입고', timestamp: '2025-10-20 09:15' },
  ]
};

const mockForwardTrace = {
  coilId: 'COIL-2024-A1234',
  material: 'SPCC 1.0T',
  supplier: '포스코',
  products: [
    { partId: 'PART-2024-10001', partName: '프론트 도어 패널', carModel: 'K5 세단', quantity: 450, status: '완료' },
    { partId: 'PART-2024-10087', partName: '리어 도어 패널', carModel: 'K5 세단', quantity: 420, status: '작업중' },
    { partId: 'PART-2024-10156', partName: '사이드 패널', carModel: '쏘나타 세단', quantity: 380, status: '완료' },
  ]
};

export function TraceabilitySearch() {
  const [searchType, setSearchType] = useState<'backward' | 'forward'>('backward');
  const [searchQuery, setSearchQuery] = useState('');
  const [showResults, setShowResults] = useState(false);

  const handleSearch = () => {
    setShowResults(true);
  };

  return (
    <Card className="bg-[#151520] border-border p-6">
      <h3 className="mb-6">양방향 추적성 검색</h3>

      <Tabs defaultValue="backward" className="w-full" onValueChange={(v) => setSearchType(v as 'backward' | 'forward')}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="backward" className="gap-2">
            <ArrowLeft className="size-4" />
            역방향 추적 (부품 → 코일)
          </TabsTrigger>
          <TabsTrigger value="forward" className="gap-2">
            <ArrowRight className="size-4" />
            정방향 추적 (코일 → 부품)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="backward" className="space-y-6">
          <div className="flex gap-2">
            <Input
              placeholder="부품 ID를 입력하세요 (예: PART-2024-10001)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#0a0a0f] border-border"
            />
            <Button onClick={handleSearch} className="gap-2 bg-blue-600 hover:bg-blue-700">
              <Search className="size-4" />
              검색
            </Button>
          </div>

          {showResults && searchType === 'backward' && (
            <div className="space-y-4">
              <div className="p-4 bg-[#0a0a0f] rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h4>검색 결과</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      {mockBackwardTrace.partName} ({mockBackwardTrace.carModel})
                    </p>
                  </div>
                  <Badge className="bg-blue-600">{mockBackwardTrace.history.length}단계</Badge>
                </div>
              </div>

              <div className="space-y-3">
                {mockBackwardTrace.history.map((step, idx) => (
                  <div key={idx} className="relative">
                    <div className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`size-8 rounded-full flex items-center justify-center ${
                          step.level === '원자재' ? 'bg-green-600' :
                          step.level === '최종 제품' ? 'bg-blue-600' : 'bg-yellow-600'
                        }`}>
                          {idx + 1}
                        </div>
                        {idx < mockBackwardTrace.history.length - 1 && (
                          <div className="w-0.5 h-16 bg-border mt-2" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <div className="p-4 bg-[#0a0a0f] rounded-lg border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <Badge variant="outline" className="mb-2">{step.level}</Badge>
                              <div className="font-mono text-sm text-blue-400">{step.id}</div>
                              <div className="mt-1">{step.name}</div>
                            </div>
                            <div className="text-right text-sm text-muted-foreground">
                              {step.timestamp}
                            </div>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            공정: {step.process}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="forward" className="space-y-6">
          <div className="flex gap-2">
            <Input
              placeholder="코일 ID를 입력하세요 (예: COIL-2024-A1234)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#0a0a0f] border-border"
            />
            <Button onClick={handleSearch} className="gap-2 bg-blue-600 hover:bg-blue-700">
              <Search className="size-4" />
              검색
            </Button>
          </div>

          {showResults && searchType === 'forward' && (
            <div className="space-y-4">
              <div className="p-4 bg-[#0a0a0f] rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h4>원자재 정보</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      {mockForwardTrace.material} - {mockForwardTrace.supplier}
                    </p>
                  </div>
                  <Badge className="bg-green-600">{mockForwardTrace.products.length}개 제품</Badge>
                </div>
              </div>

              <div>
                <h4 className="mb-3">생산된 부품 목록</h4>
                <div className="space-y-2">
                  {mockForwardTrace.products.map((product, idx) => (
                    <div key={idx} className="p-4 bg-[#0a0a0f] rounded-lg border border-border">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-sm text-blue-400">{product.partId}</span>
                            <Badge className={product.status === '완료' ? 'bg-green-600' : 'bg-blue-600'}>
                              {product.status}
                            </Badge>
                          </div>
                          <div>{product.partName}</div>
                          <div className="text-sm text-muted-foreground mt-1">{product.carModel}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm">수량: {product.quantity.toLocaleString()}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </Card>
  );
}
