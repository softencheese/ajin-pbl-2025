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

interface Process {
  id: number;
  process_code: string;
  process_name: string;
  process_order: number;
  production_line: string;
  description?: string;
  is_active: boolean;
}

export function ProcessesManager() {
  const [processes, setProcesses] = useState<Process[]>([
    {
      id: 1,
      process_code: 'SHARING',
      process_name: '샤링',
      process_order: 1,
      production_line: 'LINE-A',
      description: '코일 절단 공정',
      is_active: true
    },
    {
      id: 2,
      process_code: 'PRESSING',
      process_name: '프레스',
      process_order: 2,
      production_line: 'LINE-A',
      description: '프레스 성형 공정',
      is_active: true
    },
    {
      id: 3,
      process_code: 'ASSEMBLY',
      process_name: '조립',
      process_order: 3,
      production_line: 'LINE-B',
      description: '부품 조립 공정',
      is_active: true
    },
    {
      id: 4,
      process_code: 'SHIPPING',
      process_name: '출하',
      process_order: 4,
      production_line: 'WAREHOUSE',
      description: '최종 제품 출하',
      is_active: true
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<Process>>({});

  const handleCreate = () => {
    if (!formData.process_code || !formData.process_name || !formData.process_order || !formData.production_line) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newProcess: Process = {
      id: Math.max(...processes.map(p => p.id), 0) + 1,
      process_code: formData.process_code,
      process_name: formData.process_name,
      process_order: formData.process_order,
      production_line: formData.production_line,
      description: formData.description,
      is_active: formData.is_active ?? true,
    };

    setProcesses([...processes, newProcess]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('공정이 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedProcess || !formData.process_code || !formData.process_name || !formData.process_order || !formData.production_line) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setProcesses(processes.map(p => 
      p.id === selectedProcess.id 
        ? { ...p, ...formData } as Process
        : p
    ));
    setIsEditDialogOpen(false);
    setSelectedProcess(null);
    setFormData({});
    toast.success('공정 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedProcess) return;
    
    setProcesses(processes.filter(p => p.id !== selectedProcess.id));
    setIsDeleteDialogOpen(false);
    setSelectedProcess(null);
    toast.success('공정이 삭제되었습니다.');
  };

  const openEditDialog = (process: Process) => {
    setSelectedProcess(process);
    setFormData(process);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (process: Process) => {
    setSelectedProcess(process);
    setIsDeleteDialogOpen(true);
  };

  const filteredProcesses = processes.filter(p => 
    p.process_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.process_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.production_line.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="공정 코드, 공정명, 생산라인 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ is_active: true });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          공정 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>공정 코드</TableHead>
              <TableHead>공정명</TableHead>
              <TableHead>공정 순서</TableHead>
              <TableHead>생산 라인</TableHead>
              <TableHead>설명</TableHead>
              <TableHead>상태</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredProcesses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground h-32">
                  등록된 공정이 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredProcesses.sort((a, b) => a.process_order - b.process_order).map((process) => (
                <TableRow key={process.id} className="border-border">
                  <TableCell className="font-mono">{process.process_code}</TableCell>
                  <TableCell>{process.process_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{process.process_order}</Badge>
                  </TableCell>
                  <TableCell>{process.production_line}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {process.description || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={process.is_active ? 'default' : 'secondary'}>
                      {process.is_active ? '활성' : '비활성'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(process)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(process)}
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
          setSelectedProcess(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? '공정 등록' : '공정 수정'}</DialogTitle>
            <DialogDescription>
              공정의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="process_code">공정 코드 *</Label>
              <Input
                id="process_code"
                value={formData.process_code || ''}
                onChange={(e) => setFormData({ ...formData, process_code: e.target.value })}
                placeholder="예: SHARING"
                className="bg-[#151520] border-border"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="process_name">공정명 *</Label>
              <Input
                id="process_name"
                value={formData.process_name || ''}
                onChange={(e) => setFormData({ ...formData, process_name: e.target.value })}
                placeholder="예: 샤링"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="process_order">공정 순서 *</Label>
              <Input
                id="process_order"
                type="number"
                value={formData.process_order || ''}
                onChange={(e) => setFormData({ ...formData, process_order: parseInt(e.target.value) })}
                placeholder="예: 1"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="production_line">생산 라인 *</Label>
              <Input
                id="production_line"
                value={formData.production_line || ''}
                onChange={(e) => setFormData({ ...formData, production_line: e.target.value })}
                placeholder="예: LINE-A"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="is_active">상태</Label>
              <select
                id="is_active"
                value={formData.is_active ? 'true' : 'false'}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                className="w-full px-3 py-2 bg-[#151520] border border-border rounded-md text-sm"
              >
                <option value="true">활성</option>
                <option value="false">비활성</option>
              </select>
            </div>

            <div className="space-y-2 col-span-2">
              <Label htmlFor="description">설명</Label>
              <Input
                id="description"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="공정 설명"
                className="bg-[#151520] border-border"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedProcess(null);
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
            <AlertDialogTitle>공정 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 공정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedProcess && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    공정코드: <span className="font-mono">{selectedProcess.process_code}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    공정명: {selectedProcess.process_name}
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
