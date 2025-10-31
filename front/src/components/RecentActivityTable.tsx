import { Card } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';

const recentActivity = [
  {
    rfidTag: 'RFID-A1234',
    moldId: 'MOLD-2024-001',
    carModel: 'Model X 세단',
    partNumber: 'PT-88945',
    lotNumber: 'LOT-2024-1027-A',
    timestamp: '2025-10-27 14:32',
    status: '합격'
  },
  {
    rfidTag: 'RFID-B5678',
    moldId: 'MOLD-2024-087',
    carModel: 'Model Y SUV',
    partNumber: 'PT-88967',
    lotNumber: 'LOT-2024-1027-B',
    timestamp: '2025-10-27 14:28',
    status: '합격'
  },
  {
    rfidTag: 'RFID-C9012',
    moldId: 'MOLD-2024-042',
    carModel: 'Model Z 쿠페',
    partNumber: 'PT-88923',
    lotNumber: 'LOT-2024-1027-C',
    timestamp: '2025-10-27 14:15',
    status: '불량'
  },
  {
    rfidTag: 'RFID-D3456',
    moldId: 'MOLD-2024-128',
    carModel: 'Model X 세단',
    partNumber: 'PT-88945',
    lotNumber: 'LOT-2024-1027-D',
    timestamp: '2025-10-27 14:09',
    status: '합격'
  },
  {
    rfidTag: 'RFID-E7890',
    moldId: 'MOLD-2024-065',
    carModel: 'Model Y SUV',
    partNumber: 'PT-88956',
    lotNumber: 'LOT-2024-1027-E',
    timestamp: '2025-10-27 13:58',
    status: '합격'
  },
];

export function RecentActivityTable() {
  return (
    <Card className="bg-[#151520] border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3>최근 금형 사용 내역</h3>
        <Badge variant="outline" className="text-blue-400 border-blue-400">실시간</Badge>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>RFID 태그</TableHead>
              <TableHead>금형 ID</TableHead>
              <TableHead>차종</TableHead>
              <TableHead>부품 번호</TableHead>
              <TableHead>LOT 번호</TableHead>
              <TableHead>시간</TableHead>
              <TableHead>상태</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentActivity.map((activity, idx) => (
              <TableRow key={idx} className="border-border hover:bg-accent/50">
                <TableCell className="font-mono text-sm text-blue-400">{activity.rfidTag}</TableCell>
                <TableCell className="font-mono text-sm">{activity.moldId}</TableCell>
                <TableCell>{activity.carModel}</TableCell>
                <TableCell className="font-mono text-sm">{activity.partNumber}</TableCell>
                <TableCell className="font-mono text-sm">{activity.lotNumber}</TableCell>
                <TableCell className="text-muted-foreground text-sm">{activity.timestamp}</TableCell>
                <TableCell>
                  <Badge 
                    variant={activity.status === '합격' ? 'default' : 'destructive'}
                    className={activity.status === '합격' ? 'bg-green-600 hover:bg-green-700' : ''}
                  >
                    {activity.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
