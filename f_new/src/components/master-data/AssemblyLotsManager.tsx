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
import { Plus, Pencil, Trash2, Search, Layers } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface AssemblyLot {
  id: number;
  lot_no: string;
  part_number: string;
  part_name: string;
  assembly_level: number;
  assembly_date: string;
  quantity: number;
  worker_name: string;
  qc_passed: boolean;
  is_final_product: boolean;
}

export function AssemblyLotsManager() {
  const [assemblyLots, setAssemblyLots] = useState<AssemblyLot[]>([
    {
      id: 1,
      lot_no: 'ASSY-2024-001',
      part_number: '71413-T6000S',
      part_name: '리어 브라켓 ASSY',
      assembly_level: 1,
      assembly_date: '2024-12-01',
      quantity: 50,
      worker_name: '최민수',
      qc_passed: true,
      is_final_product: true
    },
    {
      id: 2,
      lot_no: 'ASSY-2024-002',
      part_number: '71420-T6000',
      part_name: '서브 ASSY',
      assembly_level: 1,
      assembly_date: '2024-12-01',
      quantity: 80,
      worker_name: '정수현',
      qc_passed: true,
      is_final_product: false
    },
    {
      id: 3,
      lot_no: 'ASSY-2024-003',
      part_number: '71413-T6000S',
      part_name: '리어 브라켓 ASSY',
      assembly_level: 1,
      assembly_date: '2024-12-02',
      quantity: 45,
      worker_name: '최민수',
      qc_passed: false,
      is_final_product: true
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedLot, setSelectedLot] = useState<AssemblyLot | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<AssemblyLot>>({});

  const handleCreate = () => {
    if (!formData.lot_no || !formData.part_number || !formData.assembly_date || 
        !formData.quantity || !formData.worker_name) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newLot: AssemblyLot = {
      id: Math.max(...assemblyLots.map(l => l.id), 0) + 1,
      lot_no: formData.lot_no,
      part_number: formData.part_number,
      part_name: formData.part_name || '',
      assembly_level: formData.assembly_level || 1,
      assembly_date: formData.assembly_date,
      quantity: formData.quantity,
      worker_name: formData.worker_name,
      qc_passed: formData.qc_passed ?? true,
      is_final_product: formData.is_final_product ?? false,
    };

    setAssemblyLots([...assemblyLots, newLot]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('조립품 LOT가 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedLot || !formData.lot_no || !formData.part_number || !formData.assembly_date || 
        !formData.quantity || !formData.worker_name) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setAssemblyLots(assemblyLots.map(l => 
      l.id === selectedLot.id 
        ? { ...l, ...formData } as AssemblyLot
        : l
    ));
    setIsEditDialogOpen(false);
    setSelectedLot(null);
    setFormData({});
    toast.success('조립품 LOT 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedLot) return;
    
    setAssemblyLots(assemblyLots.filter(l => l.id !== selectedLot.id));
    setIsDeleteDialogOpen(false);
    setSelectedLot(null);
    toast.success('조립품 LOT가 삭제되었습니다.');
  };

  const openEditDialog = (lot: AssemblyLot) => {
    setSelectedLot(lot);
    setFormData(lot);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (lot: AssemblyLot) => {
    setSelectedLot(lot);
    setIsDeleteDialogOpen(true);
  };

  const filteredLots = assemblyLots.filter(l => 
    l.lot_no.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.part_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.part_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="LOT번호, 품번, 품명 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ qc_passed: true, assembly_level: 1, is_final_product: false });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          조립품 LOT 등록
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
              <TableHead>조립레벨</TableHead>
              <TableHead>조립일자</TableHead>
              <TableHead>수량</TableHead>
              <TableHead>작업자</TableHead>
              <TableHead>완제품</TableHead>
              <TableHead>QC</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLots.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center text-muted-foreground h-32">
                  등록된 조립품 LOT가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredLots.map((lot) => (
                <TableRow key={lot.id} className="border-border">
                  <TableCell className="font-mono flex items-center gap-2">
                    <Layers className="size-4 text-purple-400" />
                    {lot.lot_no}
                  </TableCell>
                  <TableCell className="font-mono text-sm">{lot.part_number}</TableCell>
                  <TableCell>{lot.part_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-purple-500/10 border-purple-500">
                      Level {lot.assembly_level}
                    </Badge>
                  </TableCell>
                  <TableCell>{lot.assembly_date}</TableCell>
                  <TableCell>{lot.quantity}</TableCell>
                  <TableCell>{lot.worker_name}</TableCell>
                  <TableCell>
                    {lot.is_final_product && (
                      <Badge variant="default" className="bg-green-600">완제품</Badge>
                    )}
                  </TableCell>
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
            <DialogTitle>{isCreateDialogOpen ? '조립품 LOT 등록' : '조립품 LOT 수정'}</DialogTitle>
            <DialogDescription>
              조립품 LOT의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="lot_no">LOT 번호 *</Label>
              <Input
                id="lot_no"
                value={formData.lot_no || ''}
                onChange={(e) => setFormData({ ...formData, lot_no: e.target.value })}
                placeholder="예: ASSY-2024-001"
                className="bg-[#151520] border-border"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="part_number">품번 *</Label>
              <Input
                id="part_number"
                value={formData.part_number || ''}
                onChange={(e) => setFormData({ ...formData, part_number: e.target.value })}
                placeholder="예: 71413-T6000S"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="part_name">품명</Label>
              <Input
                id="part_name"
                value={formData.part_name || ''}
                onChange={(e) => setFormData({ ...formData, part_name: e.target.value })}
                placeholder="예: 리어 브라켓 ASSY"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="assembly_level">조립 레벨</Label>
              <Input
                id="assembly_level"
                type="number"
                value={formData.assembly_level || 1}
                onChange={(e) => setFormData({ ...formData, assembly_level: parseInt(e.target.value) })}
                placeholder="예: 1"
                className="bg-[#151520] border-border"
              />
              <p className="text-xs text-muted-foreground">자동 계산되지만 수동 입력 가능</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="assembly_date">조립 완료일 *</Label>
              <Input
                id="assembly_date"
                type="date"
                value={formData.assembly_date || ''}
                onChange={(e) => setFormData({ ...formData, assembly_date: e.target.value })}
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
                placeholder="예: 50"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="worker_name">작업자 *</Label>
              <Input
                id="worker_name"
                value={formData.worker_name || ''}
                onChange={(e) => setFormData({ ...formData, worker_name: e.target.value })}
                placeholder="예: 최민수"
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

            <div className="space-y-2 col-span-2">
              <Label>제품 구분</Label>
              <div className="flex gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_final_product || false}
                    onChange={(e) => setFormData({ ...formData, is_final_product: e.target.checked })}
                    className="size-4"
                  />
                  <span className="text-sm">최종 완제품</span>
                </label>
              </div>
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
            <AlertDialogTitle>조립품 LOT 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 조립품 LOT를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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
