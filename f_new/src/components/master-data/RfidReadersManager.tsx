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
import { Plus, Pencil, Trash2, Search, Radio } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface RfidReader {
  id: number;
  port_name: string;
  process_code: string;
  process_name: string;
  location_type: 'IN' | 'OUT' | 'HOLD' | 'DEFECT' | 'FINISH';
  description?: string;
  is_active: boolean;
  last_heartbeat?: string;
}

export function RfidReadersManager() {
  const [readers, setReaders] = useState<RfidReader[]>([
    {
      id: 1,
      port_name: 'COM3',
      process_code: 'SHARING',
      process_name: '샤링',
      location_type: 'IN',
      description: '샤링 공정 입고 리더기',
      is_active: true,
      last_heartbeat: '2024-12-02 10:30:15'
    },
    {
      id: 2,
      port_name: 'COM4',
      process_code: 'SHARING',
      process_name: '샤링',
      location_type: 'OUT',
      description: '샤링 공정 출고 리더기',
      is_active: true,
      last_heartbeat: '2024-12-02 10:30:12'
    },
    {
      id: 3,
      port_name: '192.168.1.100:9001',
      process_code: 'PRESSING',
      process_name: '프레스',
      location_type: 'IN',
      description: '프레스 공정 입고 리더기 (네트워크)',
      is_active: true,
      last_heartbeat: '2024-12-02 10:29:58'
    },
    {
      id: 4,
      port_name: '192.168.1.101:9001',
      process_code: 'PRESSING',
      process_name: '프레스',
      location_type: 'DEFECT',
      description: '프레스 불량품 리더기',
      is_active: true,
      last_heartbeat: '2024-12-02 10:30:05'
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedReader, setSelectedReader] = useState<RfidReader | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<Partial<RfidReader>>({});

  const handleCreate = () => {
    if (!formData.port_name || !formData.process_code || !formData.location_type) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    const newReader: RfidReader = {
      id: Math.max(...readers.map(r => r.id), 0) + 1,
      port_name: formData.port_name,
      process_code: formData.process_code,
      process_name: formData.process_name || '',
      location_type: formData.location_type,
      description: formData.description,
      is_active: formData.is_active ?? true,
      last_heartbeat: new Date().toLocaleString('ko-KR'),
    };

    setReaders([...readers, newReader]);
    setIsCreateDialogOpen(false);
    setFormData({});
    toast.success('RFID 리더기가 등록되었습니다.');
  };

  const handleUpdate = () => {
    if (!selectedReader || !formData.port_name || !formData.process_code || !formData.location_type) {
      toast.error('필수 항목을 모두 입력해주세요.');
      return;
    }

    setReaders(readers.map(r => 
      r.id === selectedReader.id 
        ? { ...r, ...formData } as RfidReader
        : r
    ));
    setIsEditDialogOpen(false);
    setSelectedReader(null);
    setFormData({});
    toast.success('리더기 정보가 수정되었습니다.');
  };

  const handleDelete = () => {
    if (!selectedReader) return;
    
    setReaders(readers.filter(r => r.id !== selectedReader.id));
    setIsDeleteDialogOpen(false);
    setSelectedReader(null);
    toast.success('리더기가 삭제되었습니다.');
  };

  const openEditDialog = (reader: RfidReader) => {
    setSelectedReader(reader);
    setFormData(reader);
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (reader: RfidReader) => {
    setSelectedReader(reader);
    setIsDeleteDialogOpen(true);
  };

  const filteredReaders = readers.filter(r => 
    r.port_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.process_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.process_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getLocationTypeBadge = (type: string) => {
    const variants: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
      IN: { label: '입고', variant: 'default' },
      OUT: { label: '출고', variant: 'secondary' },
      HOLD: { label: '보류', variant: 'outline' },
      DEFECT: { label: '불량', variant: 'destructive' },
      FINISH: { label: '완료', variant: 'default' },
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
            placeholder="포트, 공정 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#151520] border-border"
          />
        </div>
        <Button 
          onClick={() => {
            setFormData({ is_active: true, location_type: 'IN' });
            setIsCreateDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="size-4 mr-2" />
          리더기 등록
        </Button>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg bg-[#151520] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>포트명</TableHead>
              <TableHead>공정</TableHead>
              <TableHead>위치 유형</TableHead>
              <TableHead>설명</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>마지막 통신</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredReaders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground h-32">
                  등록된 RFID 리더기가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              filteredReaders.map((reader) => (
                <TableRow key={reader.id} className="border-border">
                  <TableCell className="font-mono flex items-center gap-2">
                    <Radio className="size-4 text-blue-400" />
                    {reader.port_name}
                  </TableCell>
                  <TableCell>
                    <div>
                      <div>{reader.process_name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{reader.process_code}</div>
                    </div>
                  </TableCell>
                  <TableCell>{getLocationTypeBadge(reader.location_type)}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {reader.description || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={reader.is_active ? 'default' : 'secondary'}>
                      {reader.is_active ? '활성' : '비활성'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {reader.last_heartbeat || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(reader)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(reader)}
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
          setSelectedReader(null);
        }
      }}>
        <DialogContent className="bg-[#0f0f14] border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle>{isCreateDialogOpen ? 'RFID 리더기 등록' : 'RFID 리더기 수정'}</DialogTitle>
            <DialogDescription>
              리더기의 정보를 입력하세요. * 표시는 필수 항목입니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="port_name">포트명 *</Label>
              <Input
                id="port_name"
                value={formData.port_name || ''}
                onChange={(e) => setFormData({ ...formData, port_name: e.target.value })}
                placeholder="예: COM3 또는 192.168.1.100:9001"
                className="bg-[#151520] border-border"
              />
            </div>
            
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
              <Label htmlFor="process_name">공정명</Label>
              <Input
                id="process_name"
                value={formData.process_name || ''}
                onChange={(e) => setFormData({ ...formData, process_name: e.target.value })}
                placeholder="예: 샤링"
                className="bg-[#151520] border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="location_type">위치 유형 *</Label>
              <select
                id="location_type"
                value={formData.location_type || 'IN'}
                onChange={(e) => setFormData({ ...formData, location_type: e.target.value as any })}
                className="w-full px-3 py-2 bg-[#151520] border border-border rounded-md text-sm"
              >
                <option value="IN">입고 (IN)</option>
                <option value="OUT">출고 (OUT)</option>
                <option value="HOLD">보류 (HOLD)</option>
                <option value="DEFECT">불량 (DEFECT)</option>
                <option value="FINISH">완료 (FINISH)</option>
              </select>
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
                placeholder="리더기 설명"
                className="bg-[#151520] border-border"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false);
              setIsEditDialogOpen(false);
              setFormData({});
              setSelectedReader(null);
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
            <AlertDialogTitle>RFID 리더기 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 리더기를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
              {selectedReader && (
                <div className="mt-4 p-3 bg-[#151520] rounded-md border border-border">
                  <div className="text-sm text-foreground">
                    포트: <span className="font-mono">{selectedReader.port_name}</span>
                  </div>
                  <div className="text-sm text-foreground mt-1">
                    공정: {selectedReader.process_name}
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
