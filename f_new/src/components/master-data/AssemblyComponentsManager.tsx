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
import { Plus, Pencil, Trash2, Search, GitBranch } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface AssemblyComponent {
  id: number;
  assembly_lot_no: string;
  assembly_part_name: string;
  component_type: 'LOT' | 'ASSEMBLY' | 'PALLET';
  component_lot_no?: string;
  component_assembly_no?: string;
  component_pallet_id?: string;
  component_part_name: string;
  required_quantity_per_unit: number;
  total_consumed_quantity: number;
  added_date: string;
}

export function AssemblyComponentsManager() {
  const [components, setComponents] = useState<AssemblyComponent[]>([
    {
      id: 1,
      assembly_lot_no: 'ASSY-2024-001',
      assembly_part_name: '리어 브라켓 ASSY',
      component_type: 'LOT',
      component_lot_no: 'LOT-2024-001',
      component_part_name: '프론트 브라켓',
      required_quantity_per_unit: 2,
      total_consumed_quantity: 100,
      added_date: '2024-12-01'
    },
    {
      id: 2,
      assembly_lot_no: 'ASSY-2024-001',
      assembly_part_name: '리어 브라켓 ASSY',
      component_type: 'LOT',
      component_lot_no: 'LOT-2024-002',
      component_part_name: '사이드 멤버',
      required_quantity_per_unit: 1,
      total_consumed_quantity: 50,
      added_date: '2024-12-01'
    },
    {
      id: 3,
      assembly_lot_no: 'ASSY-2024-002',
      assembly_part_name: '서브 ASSY',
      component_type: 'PALLET',
      component_pallet_id: 'PLT-2024-001',
      component_part_name: '볼트 세트',
      required_quantity_per_unit: 4,
      total_consumed_quantity: 320,
      added_date: '2024-12-01'
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<AssemblyComponent | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<AssemblyComponent>>({});

  const handleCreate = () => {
    if (!formData.assembly_lot_no || !formData.component_type || 
        !formData.component_part_name || !formData.required_quantity_per_unit || 
        !formData.total_consumed_quantity || !formData.added_date) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    // Validate component reference based on type
    if (formData.component_type === 'LOT' && !formData.component_lot_no) {
      toast.error('중간품 LOT 번호를 입력해주세요.');
      return;
    }
    if (formData.component_type === 'ASSEMBLY' && !formData.component_assembly_no) {
      toast.error('조립품 번호를 입력해주세요.');
      return;
    }
    if (formData.component_type === 'PALLET' && !formData.component_pallet_id) {
      toast.error('팔레트 ID를 입력해주세요.');
      return;
    }

    const newComponent: AssemblyComponent = {
      id: Math.max(...components.map(c => c.id), 0) + 1,
      assembly_lot_no: formData.assembly_lot_no,
      assembly_part_name: formData.assembly_part_name || '',
      component_type: formData.component_type,
      component_lot_no: formData.component_lot_no,
      component_assembly_no: formData.component_assembly_no,
      component_pallet_id: formData.component_pallet_id,
      component_part_name: formData.component_part_name,
      required_quantity_per_unit: formData.required_quantity_per_unit,
      total_consumed_quantity: formData.total_consumed_quantity,
      added_date: formData.added_date,
    };

    setComponents([...components, newComponent]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('조립품 구성요소가 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedComponent || !formData.assembly_lot_no || !formData.component_type || 
        !formData.component_part_name || !formData.required_quantity_per_unit || 
        !formData.total_consumed_quantity || !formData.added_date) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setComponents(components.map(c => 
      c.id === selectedComponent.id 
        ? { ...c, ...formData } as AssemblyComponent
        : c
    ));
    setIsEditDialogOpen(false);
    setSelectedComponent(null);
    setFormData({});
    toast.success('구성요소 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedComponent) return;
    
    setComponents(components.filter(c => c.id !== selectedComponent.id));
    setIsDeleteDialogOpen(false);
    setSelectedComponent(null);
    toast.success('구성요소가 삭제되었습니다.');
  };

  const openEditDialog = (component: AssemblyComponent) => {
    setSelectedComponent(component);
    setFormData(component);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (component: AssemblyComponent) => {
    setSelectedComponent(component);
    setIsDeleteDialogOpen(true);
  };

  const filteredComponents = components.filter(c => 
    c.assembly_lot_no.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.assembly_part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.component_part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.component_lot_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.component_assembly_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.component_pallet_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getComponentTypeBadge = (type: string) => {
    const variants: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' }> = {
      LOT: { label: '중간품 LOT', variant: 'default' },
      ASSEMBLY: { label: '조립품', variant: 'secondary' },
      PALLET: { label: '팔레트', variant: 'outline' },
    };
    const config = variants[type] || { label: type, variant: 'secondary' };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="조립품, 구성품 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ component_type: 'LOT' });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          구성요소 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>조립품 LOT</TableHead>
              <TableHead>조립품명</TableHead>
              <TableHead>구성 유형</TableHead>
              <TableHead>구성품 번호</TableHead>
              <TableHead>구성품명</TableHead>
              <TableHead>단위당 필요수량</TableHead>
              <TableHead>총 소비수량</TableHead>
              <TableHead>등록일</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredComponents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center text-muted-foreground h-32">
                  등록된 조립품 구성요소가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredComponents.map((component) => (
                <TableRow key={component.id} className="border-border">
                  <TableCell className="font-mono">
                    <div className="flex items-center gap-2">
                      <GitBranch className="size-4 text-blue-400" />
                      {component.assembly_lot_no}
                    </div>
                  </TableCell>
                  <TableCell>{component.assembly_part_name}</TableCell>
                  <TableCell>{getComponentTypeBadge(component.component_type)}</TableCell>
                  <TableCell className="font-mono text-sm">
                    {component.component_lot_no || 
                     component.component_assembly_no || 
                     component.component_pallet_id || '-'}
                  </TableCell>
                  <TableCell>{component.component_part_name}</TableCell>
                  <TableCell>{component.required_quantity_per_unit}</TableCell>
                  <TableCell>{component.total_consumed_quantity}</TableCell>
                  <TableCell>{component.added_date}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(component)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(component)}
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
          setSelectedComponent(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-3xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? '조립품 구성요소 등록' : '조립품 구성요소 수정'}</DialogTitle>
            <DialogDescription>
              조립품에 투입된 구성품의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="assembly_lot_no">조립품 LOT 번호 *</Label>
              <Input
                id="assembly_lot_no"
                value={formData.assembly_lot_no || ''}
                onChange={(e) => setFormData({ ...formData, assembly_lot_no: e.target.value })}
                placeholder="예: ASSY-2024-001"
                className="bg-[#151520] border-border"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="assembly_part_name">조립품명</Label>
              <Input
                id="assembly_part_name"
                value={formData.assembly_part_name || ''}
                onChange={(e) => setFormData({ ...formData, assembly_part_name: e.target.value })}
                placeholder="예: 리어 브라켓 ASSY"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="component_type">구성 유형 *</Label>
              <select
                id="component_type"
                value={formData.component_type || 'LOT'}
                onChange={(e) => {
                  setFormData({ 
                    ...formData, 
                    component_type: e.target.value as any,
                    component_lot_no: undefined,
                    component_assembly_no: undefined,
                    component_pallet_id: undefined
                  });
                }}
                className="w-full px-3 py-2 bg-[#151520] border border-border rounded-md text-sm"
              >
                <option value="LOT">중간품 LOT</option>
                <option value="ASSEMBLY">조립품</option>
                <option value="PALLET">팔레트</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="component_ref">
                {formData.component_type === 'LOT' && '중간품 LOT 번호 *'}
                {formData.component_type === 'ASSEMBLY' && '조립품 번호 *'}
                {formData.component_type === 'PALLET' && '팔레트 ID *'}
              </Label>
              <Input
                id="component_ref"
                value={
                  formData.component_type === 'LOT' ? (formData.component_lot_no || '') :
                  formData.component_type === 'ASSEMBLY' ? (formData.component_assembly_no || '') :
                  (formData.component_pallet_id || '')
                }
                onChange={(e) => {
                  if (formData.component_type === 'LOT') {
                    setFormData({ ...formData, component_lot_no: e.target.value });
                  } else if (formData.component_type === 'ASSEMBLY') {
                    setFormData({ ...formData, component_assembly_no: e.target.value });
                  } else {
                    setFormData({ ...formData, component_pallet_id: e.target.value });
                  }
                }}
                placeholder={
                  formData.component_type === 'LOT' ? '예: LOT-2024-001' :
                  formData.component_type === 'ASSEMBLY' ? '예: ASSY-2024-001' :
                  '예: PLT-2024-001'
                }
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="component_part_name">구성품명 *</Label>
              <Input
                id="component_part_name"
                value={formData.component_part_name || ''}
                onChange={(e) => setFormData({ ...formData, component_part_name: e.target.value })}
                placeholder="예: 프론트 브라켓"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="required_quantity_per_unit">단위당 필요 수량 *</Label>
              <Input
                id="required_quantity_per_unit"
                type="number"
                value={formData.required_quantity_per_unit || ''}
                onChange={(e) => setFormData({ ...formData, required_quantity_per_unit: parseInt(e.target.value) })}
                placeholder="예: 2"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="total_consumed_quantity">총 소비 수량 *</Label>
              <Input
                id="total_consumed_quantity"
                type="number"
                value={formData.total_consumed_quantity || ''}
                onChange={(e) => setFormData({ ...formData, total_consumed_quantity: parseInt(e.target.value) })}
                placeholder="예: 100"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="added_date">등록일 *</Label>
              <Input
                id="added_date"
                type="date"
                value={formData.added_date || ''}
                onChange={(e) => setFormData({ ...formData, added_date: e.target.value })}
                className="bg-[#151520] border-border"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedComponent(null);
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
            <AlertDialogTitle>구성요소 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 구성요소를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedComponent && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    조립품: <span className="font-mono">{selectedComponent.assembly_lot_no}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    구성품: {selectedComponent.component_part_name}
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    소비수량: {selectedComponent.total_consumed_quantity}
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
