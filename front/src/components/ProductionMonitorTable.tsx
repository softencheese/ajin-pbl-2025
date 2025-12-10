import { Card } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Search } from 'lucide-react';

const productionData = [
  {
    partId: 'PART-2024-10001',
    partName: '프론트 도어 패널',
    carModel: 'K5 세단',
    processName: '프레싱',
    processCode: 'PRESS-01',
    status: '작업중',
    line: 'A 라인',
    quantity: 450,
    coilId: 'COIL-2024-A1234',
    timestamp: '2025-10-27 14:32'
  },
  {
    partId: 'PART-2024-10002',
    partName: '리어 펜더',
    carModel: '쏘렌토 SUV',
    processName: '조립',
    processCode: 'ASSEM-02',
    status: '완료',
    line: 'B 라인',
    quantity: 320,
    coilId: 'COIL-2024-B5678',
    timestamp: '2025-10-27 14:28'
  },
  {
    partId: 'PART-2024-10003',
    partName: '루프 패널',
    carModel: '쏘나타 세단',
    processName: '쉐어링',
    processCode: 'SHAR-01',
    status: '대기',
    line: 'C 라인',
    quantity: 280,
    coilId: 'COIL-2024-C9012',
    timestamp: '2025-10-27 14:15'
  },
  {
    partId: 'PART-2024-10004',
    partName: '후드 어셈블리',
    carModel: 'GV80 SUV',
    processName: '프레싱',
    processCode: 'PRESS-02',
    status: '불량',
    line: 'A 라인',
    quantity: 150,
    coilId: 'COIL-2024-D3456',
    timestamp: '2025-10-27 14:09'
  },
  {
    partId: 'PART-2024-10005',
    partName: '사이드 패널',
    carModel: '투싼 SUV',
    processName: '조립',
    processCode: 'ASSEM-01',
    status: '작업중',
    line: 'B 라인',
    quantity: 380,
    coilId: 'COIL-2024-E7890',
    timestamp: '2025-10-27 13:58'
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case '작업중':
      return 'bg-blue-600 hover:bg-blue-700';
    case '완료':
      return 'bg-green-600 hover:bg-green-700';
    case '대기':
      return 'bg-yellow-600 hover:bg-yellow-700';
    case '불량':
      return 'bg-red-600 hover:bg-red-700';
    default:
      return '';
  }
};

export function ProductionMonitorTable() {
  return (
    <Card className="bg-[#151520] border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3>생산 공정 실시간 모니터링</h3>
          <p className="text-muted-foreground text-sm mt-1">RFID 리더기로 수집된 부품 식별 데이터</p>
        </div>
        <Badge variant="outline" className="text-blue-400 border-blue-400">실시간</Badge>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input 
            placeholder="부품 ID, 부품명, 차종 검색..." 
            className="pl-10 bg-[#0a0a0f] border-border"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>부품 ID</TableHead>
              <TableHead>부품명</TableHead>
              <TableHead>차종</TableHead>
              <TableHead>공정명 (코드)</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>생산 라인</TableHead>
              <TableHead>수량</TableHead>
              <TableHead>투입 코일 ID</TableHead>
              <TableHead>시간</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {productionData.map((item, idx) => (
              <TableRow key={idx} className="border-border hover:bg-accent/50">
                <TableCell className="font-mono text-sm text-blue-400">{item.partId}</TableCell>
                <TableCell>{item.partName}</TableCell>
                <TableCell>{item.carModel}</TableCell>
                <TableCell>
                  <div>{item.processName}</div>
                  <div className="text-xs text-muted-foreground font-mono">{item.processCode}</div>
                </TableCell>
                <TableCell>
                  <Badge className={getStatusColor(item.status)}>
                    {item.status}
                  </Badge>
                </TableCell>
                <TableCell>{item.line}</TableCell>
                <TableCell>{item.quantity.toLocaleString()}</TableCell>
                <TableCell className="font-mono text-sm text-green-400">{item.coilId}</TableCell>
                <TableCell className="text-muted-foreground text-sm">{item.timestamp}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
