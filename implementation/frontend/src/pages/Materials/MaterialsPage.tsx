import { useState } from 'react';
import { Table, Button, Modal, Form, Input, DatePicker, Checkbox, message, Space, Popconfirm, Tag, Alert } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { materialApi } from '../../api/materials';
import type { Material, MaterialCreateRequest } from '../../types/material';
import dayjs from 'dayjs';

export function MaterialsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState<Material | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: materials = [], isLoading, error } = useQuery({
    queryKey: ['materials', searchText],
    queryFn: () => materialApi.getAll({ search: searchText }),
    retry: 1,
    
  });

  

  const createMutation = useMutation({
    mutationFn: (payload: MaterialCreateRequest) => materialApi.create(payload),
    onSuccess: () => {
      message.success('원자재가 등록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      handleCloseModal();
    },
    onError: () => {
      message.error('원자재 등록에 실패했습니다.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<MaterialCreateRequest> }) =>
      materialApi.update(id, payload),
    onSuccess: () => {
      message.success('원자재 정보가 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      handleCloseModal();
    },
    onError: () => {
      message.error('원자재 수정에 실패했습니다.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => materialApi.delete(id),
    onSuccess: () => {
      message.success('원자재가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['materials'] });
    },
    onError: () => {
      message.error('원자재 삭제에 실패했습니다.');
    },
  });

  const handleOpenModal = (material?: Material) => {
    if (material) {
      setEditingMaterial(material);
      form.setFieldsValue({
        ...material,
        receipt_date: dayjs(material.receipt_date),
      });
    } else {
      setEditingMaterial(null);
      form.resetFields();
      form.setFieldsValue({ qc_passed: true });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingMaterial(null);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    const payload = {
      ...values,
      receipt_date: values.receipt_date.format('YYYY-MM-DD'),
    };

    if (editingMaterial) {
      updateMutation.mutate({ id: editingMaterial.id, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleExportToCSV = () => {
    if (!materials || materials.length === 0) {
      message.warning('내보낼 데이터가 없습니다.');
      return;
    }

    // CSV 헤더
    const headers = ['코일 번호', '원자재명', '공급업체', '입고일자', 'QC 상태', '등록일'];

    // CSV 데이터 생성
    const csvData = materials.map((material: Material) => [
      material.coil_number,
      material.material_name,
      material.supplier || '-',
      dayjs(material.receipt_date).format('YYYY-MM-DD'),
      material.qc_passed ? '합격' : '불합격',
      dayjs(material.created_at).format('YYYY-MM-DD HH:mm'),
    ]);

    // CSV 문자열 생성 (엑셀에서 한글이 깨지지 않도록 BOM 추가)
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // BOM(Byte Order Mark) 추가 - 엑셀에서 한글 인코딩을 위해 필요
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

    // 파일명 생성 (현재 날짜 포함)
    const fileName = `원자재목록_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;

    // 다운로드 링크 생성 및 클릭
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', fileName);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    message.success('CSV 파일이 다운로드되었습니다.');
  };

  const columns = [
    {
      title: '코일 번호',
      dataIndex: 'coil_number',
      key: 'coil_number',
      width: 150,
    },
    {
      title: '원자재명',
      dataIndex: 'material_name',
      key: 'material_name',
    },
    {
      title: '공급업체',
      dataIndex: 'supplier',
      key: 'supplier',
    },
    {
      title: '입고일자',
      dataIndex: 'receipt_date',
      key: 'receipt_date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'QC 상태',
      dataIndex: 'qc_passed',
      key: 'qc_passed',
      render: (qc_passed: boolean) => (
        <Tag color={qc_passed ? 'success' : 'error'}>
          {qc_passed ? '합격' : '불합격'}
        </Tag>
      ),
    },
    {
      title: '등록일',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '작업',
      key: 'actions',
      width: 150,
      render: (_: any, record: Material) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="원자재 삭제"
            description="정말 삭제하시겠습니까?"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="삭제"
            cancelText="취소"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              삭제
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>원자재 관리</h1>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleExportToCSV}>
            엑셀 다운로드
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            원자재 등록
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="데이터 로드 오류"
          description="원자재 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="코일 번호, 원자재명, 공급업체로 검색"
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 300 }}
          allowClear
        />
      </div>

      <Table
        dataSource={Array.isArray(materials) ? materials : []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title={editingMaterial ? '원자재 수정' : '새 원자재 등록'}
        open={isModalOpen}
        onCancel={handleCloseModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ qc_passed: true }}
        >
          <Form.Item
            name="coil_number"
            label="코일 번호"
            rules={[{ required: true, message: '코일 번호를 입력하세요' }]}
          >
            <Input placeholder="예: C059461B" />
          </Form.Item>

          <Form.Item
            name="material_name"
            label="원자재명"
            rules={[{ required: true, message: '원자재명을 입력하세요' }]}
          >
            <Input placeholder="예: SPHC 1.6T" />
          </Form.Item>

          <Form.Item name="supplier" label="공급업체">
            <Input placeholder="예: 포스코" />
          </Form.Item>

          <Form.Item
            name="receipt_date"
            label="입고일자"
            rules={[{ required: true, message: '입고일자를 선택하세요' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="qc_passed" valuePropName="checked">
            <Checkbox>QC 합격</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
