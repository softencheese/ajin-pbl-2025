import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from '../ui/dialog';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';
import { Badge } from '../ui/badge';
import { Plus, Pencil, Trash2, Search } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface Lot {
  id: number;
  lot_no: string;
  part_number: string;
  part_name: string;
  process_code: string;
  process_name: string;
  coil_number: string;
  quantity: number;
  production_date: string;
  worker_name: string;
  qc_passed: boolean;
  assembly_level: number;
}

export function LotsManager() {
  const [lots, setLots] = useState<Lot[]>([
    {
      id: 1,
      lot_no: 'LOT-2024-001',
      part_number: '71412-T6000S',
      part_name: '프론트 브라켓',
      process_code: 'PRESSING',
      process_name: '프레스',
      coil_number: 'C059461B',
      quantity: 100,
      production_date: '2024-12-01',
      worker_name: '김철수',
      qc_passed: true,
      assembly_level: 0
    },
    {
      id: 2,
      lot_no: 'LOT-2024-002',
      part_number: '86520-L1000',
      part_name: '사이드 멤버',
      process_code: 'SHARING',
      process_name: '샤링',
      coil_number: 'C059462A',
      quantity: 150,
      production_date: '2024-12-01',
      worker_name: '이영희',
      qc_passed: true,
      assembly_level: 0
    },
    {
      id: 3,
      lot_no: 'LOT-2024-003',
      part_number: '71412-T6000S',
      part_name: '프론트 브라켓',
      process_code: 'PRESSING',
      process_name: '프레스',
      coil_number: 'C059461B',
      quantity: 95,
      production_date: '2024-12-02',
      worker_name: '박민수',
      qc_passed: false,
      assembly_level: 0
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedLot, setSelectedLot] = useState<Lot | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<Lot>>({});

  const handleCreate = () => {
    if (!formData.lot_no || !formData.part_number || !formData.process_code || 
        !formData.coil_number || !formData.quantity || !formData.production_date || !formData.worker_name) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newLot: Lot = {
      id: Math.max(...lots.map(l => l.id), 0) + 1,
      lot_no: formData.lot_no,
      part_number: formData.part_number,
      part_name: formData.part_name || '',
      process_code: formData.process_code,
      process_name: formData.process_name || '',
      coil_number: formData.coil_number,
      quantity: formData.quantity,
      production_date: formData.production_date,
      worker_name: formData.worker_name,
      qc_passed: formData.qc_passed ?? true,
      assembly_level: 0, // 중간품은 항상 0
    };

    setLots([...lots, newLot]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('중간품 LOT가 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedLot || !formData.lot_no || !formData.part_number || !formData.process_code || 
        !formData.coil_number || !formData.quantity || !formData.production_date || !formData.worker_name) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setLots(lots.map(l => 
      l.id === selectedLot.id 
        ? { ...l, ...formData, assembly_level: 0 } as Lot
        : l
    ));
    setIsEditDialogOpen(false);
    setSelectedLot(null);
    setFormData({});
    toast.success('LOT 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedLot) return;
    
    setLots(lots.filter(l => l.id !== selectedLot.id));
    setIsDeleteDialogOpen(false);
    setSelectedLot(null);
    toast.success('LOT가 삭제되었습니다.');
  };

  const openEditDialog = (lot: Lot) => {
    setSelectedLot(lot);
    setFormData(lot);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (lot: Lot) => {
    setSelectedLot(lot);
    setIsDeleteDialogOpen(true);
  };

  const filteredLots = lots.filter(l => 
    l.lot_no.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.part_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.coil_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="LOT번호, 품번, 코일번호 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ qc_passed: true, assembly_level: 0 });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          중간품 LOT 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>LOT 번호</TableHead>
              <TableHead>품번</TableHead>
              <TableHead>품명</TableHead>
              <TableHead>공정</TableHead>
              <TableHead>코일번호</TableHead>
              <TableHead>수량</TableHead>
              <TableHead>생산일자</TableHead>
              <TableHead>작업자</TableHead>
              <TableHead>QC</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLots.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center text-muted-foreground h-32">
                  등록된 중간품 LOT가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredLots.map((lot) => (
                <TableRow key={lot.id} className="border-border">
                  <TableCell className="font-mono">{lot.lot_no}</TableCell>
                  <TableCell className="font-mono text-sm">{lot.part_number}</TableCell>
                  <TableCell>{lot.part_name}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{lot.process_name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{lot.process_code}</div>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{lot.coil_number}</TableCell>
                  <TableCell>{lot.quantity}</TableCell>
                  <TableCell>{lot.production_date}</TableCell>
                  <TableCell>{lot.worker_name}</TableCell>
                  <TableCell>
                    <Badge variant={lot.qc_passed ? 'default' : 'destructive'}>
                      {lot.qc_passed ? '합격' : '불합격'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(lot)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(lot)}
                      >
                        <Trash2 className="size-4 text-red-400" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isCreateDialogOpen || isEditDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setIsCreateDialogOpen(false);
          setIsEditDialogOpen(false);
          setFormData({});
          setSelectedLot(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-3xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? '중간품 LOT 등록' : '중간품 LOT 수정'}</DialogTitle>
            <DialogDescription>
              중간품 LOT의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="lot_no">LOT 번호 *</Label>
              <Input
                id="lot_no"
                value={formData.lot_no || ''}
                onChange={(e) => setFormData({ ...formData, lot_no: e.target.value })}
                placeholder="예: LOT-2024-001"
                className="bg-[#151520] border-border"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="part_number">품번 *</Label>
              <Input
                id="part_number"
                value={formData.part_number || ''}
                onChange={(e) => setFormData({ ...formData, part_number: e.target.value })}
                placeholder="예: 71412-T6000S"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="part_name">품명</Label>
              <Input
                id="part_name"
                value={formData.part_name || ''}
                onChange={(e) => setFormData({ ...formData, part_name: e.target.value })}
                placeholder="예: 프론트 브라켓"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="process_code">공정 코드 *</Label>
              <Input
                id="process_code"
                value={formData.process_code || ''}
                onChange={(e) => setFormData({ ...formData, process_code: e.target.value })}
                placeholder="예: PRESSING"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="process_name">공정명</Label>
              <Input
                id="process_name"
                value={formData.process_name || ''}
                onChange={(e) => setFormData({ ...formData, process_name: e.target.value })}
                placeholder="예: 프레스"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="coil_number">코일 번호 *</Label>
              <Input
                id="coil_number"
                value={formData.coil_number || ''}
                onChange={(e) => setFormData({ ...formData, coil_number: e.target.value })}
                placeholder="예: C059461B"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="quantity">수량 *</Label>
              <Input
                id="quantity"
                type="number"
                value={formData.quantity || ''}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
                placeholder="예: 100"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="production_date">생산일자 *</Label>
              <Input
                id="production_date"
                type="date"
                value={formData.production_date || ''}
                onChange={(e) => setFormData({ ...formData, production_date: e.target.value })}
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="worker_name">작업자 *</Label>
              <Input
                id="worker_name"
                value={formData.worker_name || ''}
                onChange={(e) => setFormData({ ...formData, worker_name: e.target.value })}
                placeholder="예: 김철수"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="qc_passed">QC 상태</Label>
              <select
                id="qc_passed"
                value={formData.qc_passed ? 'true' : 'false'}
                onChange={(e) => setFormData({ ...formData, qc_passed: e.target.value === 'true' })}
                className="w-full px-3 py-2 bg-[#151520] border border-border rounded-md text-sm"
              >
                <option value="true">합격</option>
                <option value="false">불합격</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedLot(null);
            }}>
              취소
            </Button>
            <Button 
              onClick={isCreateDialogOpen ? handleCreate : handleUpdate}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isCreateDialogOpen ? '등록' : '수정'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent className="bg-[#0f0f14] border-border">
          <AlertDialogHeader>
            <AlertDialogTitle>중간품 LOT 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 LOT를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedLot && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    LOT번호: <span className="font-mono">{selectedLot.lot_no}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    품번: {selectedLot.part_number}
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    수량: {selectedLot.quantity}
                  </div>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
