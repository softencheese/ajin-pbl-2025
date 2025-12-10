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

interface Part {
  id: number;
  part_number: string;
  part_name: string;
  vehicle_model: string;
  is_assembly: boolean;
  is_final_product: boolean;
  standard_cycle_time?: number;
  unit_price?: number;
  specification?: string;
}

export function PartsManager() {
  const [parts, setParts] = useState<Part[]>([
    {
      id: 1,
      part_number: '71412-T6000S',
      part_name: '프론트 브라켓',
      vehicle_model: '쏘나타 DN8',
      is_assembly: false,
      is_final_product: false,
      standard_cycle_time: 45,
      unit_price: 1200
    },
    {
      id: 2,
      part_number: '71413-T6000S',
      part_name: '리어 브라켓 ASSY',
      vehicle_model: '쏘나타 DN8',
      is_assembly: true,
      is_final_product: true,
      standard_cycle_time: 120,
      unit_price: 3500
    },
    {
      id: 3,
      part_number: '86520-L1000',
      part_name: '사이드 멤버',
      vehicle_model: '그랜저 IG',
      is_assembly: false,
      is_final_product: false,
      standard_cycle_time: 60,
      unit_price: 1800
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedPart, setSelectedPart] = useState<Part | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<Part>>({});

  const handleCreate = () => {
    if (!formData.part_number || !formData.part_name || !formData.vehicle_model) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newPart: Part = {
      id: Math.max(...parts.map(p => p.id), 0) + 1,
      part_number: formData.part_number,
      part_name: formData.part_name,
      vehicle_model: formData.vehicle_model,
      is_assembly: formData.is_assembly ?? false,
      is_final_product: formData.is_final_product ?? false,
      standard_cycle_time: formData.standard_cycle_time,
      unit_price: formData.unit_price,
      specification: formData.specification,
    };

    setParts([...parts, newPart]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('품번이 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedPart || !formData.part_number || !formData.part_name || !formData.vehicle_model) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setParts(parts.map(p => 
      p.id === selectedPart.id 
        ? { ...p, ...formData } as Part
        : p
    ));
    setIsEditDialogOpen(false);
    setSelectedPart(null);
    setFormData({});
    toast.success('품번 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedPart) return;
    
    setParts(parts.filter(p => p.id !== selectedPart.id));
    setIsDeleteDialogOpen(false);
    setSelectedPart(null);
    toast.success('품번이 삭제되었습니다.');
  };

  const openEditDialog = (part: Part) => {
    setSelectedPart(part);
    setFormData(part);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (part: Part) => {
    setSelectedPart(part);
    setIsDeleteDialogOpen(true);
  };

  const filteredParts = parts.filter(p => 
    p.part_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.vehicle_model.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="품번, 품명, 차종 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ is_assembly: false, is_final_product: false });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          품번 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>품번</TableHead>
              <TableHead>품명</TableHead>
              <TableHead>차종</TableHead>
              <TableHead>조립품</TableHead>
              <TableHead>최종완제품</TableHead>
              <TableHead>표준C/T(초)</TableHead>
              <TableHead>단가(원)</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredParts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground h-32">
                  등록된 품번이 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredParts.map((part) => (
                <TableRow key={part.id} className="border-border">
                  <TableCell className="font-mono">{part.part_number}</TableCell>
                  <TableCell>{part.part_name}</TableCell>
                  <TableCell>{part.vehicle_model}</TableCell>
                  <TableCell>
                    <Badge variant={part.is_assembly ? 'default' : 'secondary'}>
                      {part.is_assembly ? '조립품' : '중간품'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {part.is_final_product && (
                      <Badge variant="default" className="bg-green-600">완제품</Badge>
                    )}
                  </TableCell>
                  <TableCell>{part.standard_cycle_time ?? '-'}</TableCell>
                  <TableCell>{part.unit_price ? part.unit_price.toLocaleString() : '-'}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(part)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(part)}
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
          setSelectedPart(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? '품번 등록' : '품번 수정'}</DialogTitle>
            <DialogDescription>
              품번의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
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
              <Label htmlFor="part_name">품명 *</Label>
              <Input
                id="part_name"
                value={formData.part_name || ''}
                onChange={(e) => setFormData({ ...formData, part_name: e.target.value })}
                placeholder="예: 프론트 브라켓"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="vehicle_model">차종 *</Label>
              <Input
                id="vehicle_model"
                value={formData.vehicle_model || ''}
                onChange={(e) => setFormData({ ...formData, vehicle_model: e.target.value })}
                placeholder="예: 쏘나타 DN8"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="standard_cycle_time">표준 사이클 타임 (초)</Label>
              <Input
                id="standard_cycle_time"
                type="number"
                value={formData.standard_cycle_time || ''}
                onChange={(e) => setFormData({ ...formData, standard_cycle_time: parseInt(e.target.value) })}
                placeholder="예: 45"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit_price">단가 (원)</Label>
              <Input
                id="unit_price"
                type="number"
                value={formData.unit_price || ''}
                onChange={(e) => setFormData({ ...formData, unit_price: parseInt(e.target.value) })}
                placeholder="예: 1200"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label>제품 구분</Label>
              <div className="flex gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_assembly || false}
                    onChange={(e) => setFormData({ ...formData, is_assembly: e.target.checked })}
                    className="size-4"
                  />
                  <span className="text-sm">조립품</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_final_product || false}
                    onChange={(e) => setFormData({ ...formData, is_final_product: e.target.checked })}
                    className="size-4"
                  />
                  <span className="text-sm">최종완제품</span>
                </label>
              </div>
            </div>

            <div className="space-y-2 col-span-2">
              <Label htmlFor="specification">규격 및 사양</Label>
              <Input
                id="specification"
                value={formData.specification || ''}
                onChange={(e) => setFormData({ ...formData, specification: e.target.value })}
                placeholder="규격, 재질 등 추가 정보"
                className="bg-[#151520] border-border"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedPart(null);
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
            <AlertDialogTitle>품번 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 품번을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedPart && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    품번: <span className="font-mono">{selectedPart.part_number}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    품명: {selectedPart.part_name}
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
