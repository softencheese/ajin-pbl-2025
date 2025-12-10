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

interface RawMaterial {
  id: number;
  coil_number: string;
  material_name: string;
  supplier: string;
  receipt_date: string;
  qc_passed: boolean;
  thickness?: number;
  width?: number;
  weight?: number;
  notes?: string;
}

export function RawMaterialsManager() {
  const [materials, setMaterials] = useState<RawMaterial[]>([
    {
      id: 1,
      coil_number: 'C059461B',
      material_name: 'SPHC 냉연강판',
      supplier: '포스코',
      receipt_date: '2024-11-15',
      qc_passed: true,
      thickness: 1.2,
      width: 1200,
      weight: 2500
    },
    {
      id: 2,
      coil_number: 'C059462A',
      material_name: 'SPCC 열연강판',
      supplier: '현대제철',
      receipt_date: '2024-11-20',
      qc_passed: true,
      thickness: 1.5,
      width: 1000,
      weight: 3200
    },
    {
      id: 3,
      coil_number: 'C059463C',
      material_name: 'SPHC 냉연강판',
      supplier: '포스코',
      receipt_date: '2024-11-22',
      qc_passed: false,
      thickness: 1.2,
      width: 1200,
      weight: 2450
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState<RawMaterial | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<RawMaterial>>({});

  const handleCreate = () => {
    if (!formData.coil_number || !formData.material_name || !formData.supplier || !formData.receipt_date) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newMaterial: RawMaterial = {
      id: Math.max(...materials.map(m => m.id), 0) + 1,
      coil_number: formData.coil_number,
      material_name: formData.material_name,
      supplier: formData.supplier,
      receipt_date: formData.receipt_date,
      qc_passed: formData.qc_passed ?? true,
      thickness: formData.thickness,
      width: formData.width,
      weight: formData.weight,
      notes: formData.notes,
    };

    setMaterials([...materials, newMaterial]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('원자재가 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedMaterial || !formData.coil_number || !formData.material_name || !formData.supplier || !formData.receipt_date) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setMaterials(materials.map(m => 
      m.id === selectedMaterial.id 
        ? { ...m, ...formData } as RawMaterial
        : m
    ));
    setIsEditDialogOpen(false);
    setSelectedMaterial(null);
    setFormData({});
    toast.success('원자재 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedMaterial) return;
    
    setMaterials(materials.filter(m => m.id !== selectedMaterial.id));
    setIsDeleteDialogOpen(false);
    setSelectedMaterial(null);
    toast.success('원자재가 삭제되었습니다.');
  };

  const openEditDialog = (material: RawMaterial) => {
    setSelectedMaterial(material);
    setFormData(material);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (material: RawMaterial) => {
    setSelectedMaterial(material);
    setIsDeleteDialogOpen(true);
  };

  const filteredMaterials = materials.filter(m => 
    m.coil_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.material_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.supplier.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="코일번호, 자재명, 공급업체 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ qc_passed: true });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          원자재 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>코일 번호</TableHead>
              <TableHead>자재명</TableHead>
              <TableHead>공급업체</TableHead>
              <TableHead>입고일자</TableHead>
              <TableHead>두께(mm)</TableHead>
              <TableHead>폭(mm)</TableHead>
              <TableHead>중량(kg)</TableHead>
              <TableHead>QC 상태</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredMaterials.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center text-muted-foreground h-32">
                  등록된 원자재가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredMaterials.map((material) => (
                <TableRow key={material.id} className="border-border">
                  <TableCell className="font-mono">{material.coil_number}</TableCell>
                  <TableCell>{material.material_name}</TableCell>
                  <TableCell>{material.supplier}</TableCell>
                  <TableCell>{material.receipt_date}</TableCell>
                  <TableCell>{material.thickness ?? '-'}</TableCell>
                  <TableCell>{material.width ?? '-'}</TableCell>
                  <TableCell>{material.weight ?? '-'}</TableCell>
                  <TableCell>
                    <Badge variant={material.qc_passed ? 'default' : 'destructive'}>
                      {material.qc_passed ? '합격' : '불합격'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(material)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(material)}
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
          setSelectedMaterial(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? '원자재 등록' : '원자재 수정'}</DialogTitle>
            <DialogDescription>
              원자재 코일의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
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
              <Label htmlFor="material_name">자재명 *</Label>
              <Input
                id="material_name"
                value={formData.material_name || ''}
                onChange={(e) => setFormData({ ...formData, material_name: e.target.value })}
                placeholder="예: SPHC 냉연강판"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="supplier">공급업체 *</Label>
              <Input
                id="supplier"
                value={formData.supplier || ''}
                onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                placeholder="예: 포스코"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="receipt_date">입고일자 *</Label>
              <Input
                id="receipt_date"
                type="date"
                value={formData.receipt_date || ''}
                onChange={(e) => setFormData({ ...formData, receipt_date: e.target.value })}
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="thickness">두께 (mm)</Label>
              <Input
                id="thickness"
                type="number"
                step="0.1"
                value={formData.thickness || ''}
                onChange={(e) => setFormData({ ...formData, thickness: parseFloat(e.target.value) })}
                placeholder="예: 1.2"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="width">폭 (mm)</Label>
              <Input
                id="width"
                type="number"
                value={formData.width || ''}
                onChange={(e) => setFormData({ ...formData, width: parseInt(e.target.value) })}
                placeholder="예: 1200"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="weight">중량 (kg)</Label>
              <Input
                id="weight"
                type="number"
                value={formData.weight || ''}
                onChange={(e) => setFormData({ ...formData, weight: parseInt(e.target.value) })}
                placeholder="예: 2500"
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
              <Label htmlFor="notes">비고</Label>
              <Input
                id="notes"
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="추가 메모 사항"
                className="bg-[#151520] border-border"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedMaterial(null);
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
            <AlertDialogTitle>원자재 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 원자재를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedMaterial && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    코일번호: <span className="font-mono">{selectedMaterial.coil_number}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    자재명: {selectedMaterial.material_name}
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
