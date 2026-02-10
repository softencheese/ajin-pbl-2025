import { useState } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Popconfirm,
  Tag,
  Alert,
  Switch,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { itemApi } from '../../api/items';
import type { Item, ItemCreateRequest, ItemUpdateRequest, ItemType } from '../../types/item';
import dayjs from 'dayjs';

const { Option } = Select;

export function ItemsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Item | null>(null);
  const [searchText, setSearchText] = useState('');
  const [itemTypeFilter, setItemTypeFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch items
  const { data: itemsData, isLoading, error } = useQuery({
    queryKey: ['items', searchText, itemTypeFilter, page, perPage],
    queryFn: () =>
      itemApi.getAll({
        search: searchText,
        item_type: itemTypeFilter || undefined,
        is_active: true,
        page: page,
        per_page: perPage,
      }),
    retry: 1,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (payload: ItemCreateRequest) => itemApi.create(payload),
    onSuccess: () => {
      message.success('품목이 등록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '품목 등록에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ItemUpdateRequest }) =>
      itemApi.update(id, payload),
    onSuccess: () => {
      message.success('품목 정보가 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '품목 수정에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => itemApi.delete(id),
    onSuccess: () => {
      message.success('품목이 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '품목 삭제에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  const handleOpenModal = (item?: Item) => {
    if (item) {
      setEditingItem(item);
      form.setFieldsValue({
        ...item,
        unit: item.unit || 'EA',
      });
    } else {
      setEditingItem(null);
      form.resetFields();
      form.setFieldsValue({ unit: 'EA', item_type: 'RAW' });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingItem(null);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    // Extract values from tags mode (arrays) or use as-is if strings
    const extractValue = (val: any) => {
      if (Array.isArray(val)) {
        return val.length > 0 ? val[0] : undefined;
      }
      return val || undefined;
    };

    const payload: ItemCreateRequest = {
      item_code: extractValue(values.item_code),
      item_name: extractValue(values.item_name),
      item_type: values.item_type,
      unit: values.unit || 'EA',
      spec: extractValue(values.spec),
      vehicle_model: extractValue(values.vehicle_model),
      default_supplier: values.default_supplier || undefined,
    };

    if (editingItem) {
      const updatePayload: ItemUpdateRequest = {
        item_name: extractValue(values.item_name),
        item_type: values.item_type,
        unit: values.unit,
        spec: extractValue(values.spec),
        vehicle_model: extractValue(values.vehicle_model),
        default_supplier: values.default_supplier || undefined,
        is_active: values.is_active !== undefined ? values.is_active : true,
      };
      updateMutation.mutate({ id: editingItem.id, payload: updatePayload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Get unique item codes from existing items
  const getItemCodeOptions = () => {
    if (!itemsData?.items) return [];

    const itemCodes = itemsData.items
      .map(item => item.item_code)
      .filter((code): code is string => code != null && code !== '');

    const uniqueCodes = Array.from(new Set(itemCodes));

    return uniqueCodes.map(code => ({
      value: code,
      label: code,
    }));
  };

  // Get unique item names from existing items
  const getItemNameOptions = () => {
    if (!itemsData?.items) return [];

    const itemNames = itemsData.items
      .map(item => item.item_name)
      .filter((name): name is string => name != null && name !== '');

    const uniqueNames = Array.from(new Set(itemNames));

    return uniqueNames.map(name => ({
      value: name,
      label: name,
    }));
  };

  // Get unique specs from existing items
  const getSpecOptions = () => {
    if (!itemsData?.items) return [];

    const specs = itemsData.items
      .map(item => item.spec)
      .filter((spec): spec is string => spec != null && spec !== '');

    const uniqueSpecs = Array.from(new Set(specs));

    return uniqueSpecs.map(spec => ({
      value: spec,
      label: spec,
    }));
  };

  // Get unique vehicle models from existing items
  const getVehicleModelOptions = () => {
    if (!itemsData?.items) return [];

    const models = itemsData.items
      .map(item => item.vehicle_model)
      .filter((model): model is string => model != null && model !== '');

    const uniqueModels = Array.from(new Set(models));

    return uniqueModels.map(model => ({
      value: model,
      label: model,
    }));
  };

  // 하나의 값만 유지하는 핸들러
  const handleSingleTagChange = (fieldName: string) => (value: string[]) => {
    // 마지막으로 선택/입력된 값만 유지
    const lastValue = value.length > 0 ? [value[value.length - 1]] : [];
    form.setFieldsValue({ [fieldName]: lastValue });
  };

  const handleExportToCSV = () => {
    if (!itemsData || itemsData.items.length === 0) {
      message.warning('내보낼 데이터가 없습니다.');
      return;
    }

    const headers = ['품목코드', '품목명', '품목유형', '단위', '규격', '차종', '기본공급사', '상태', '등록일'];
    const csvData = itemsData.items.map((item: Item) => [
      item.item_code,
      item.item_name,
      getItemTypeLabel(item.item_type),
      item.unit,
      item.spec || '-',
      item.vehicle_model || '-',
      item.default_supplier || '-',
      item.is_active ? '사용' : '미사용',
      dayjs(item.created_at).format('YYYY-MM-DD HH:mm'),
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const fileName = `품목목록_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;

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

  const getItemTypeLabel = (type: ItemType): string => {
    const labels: Record<ItemType, string> = {
      RAW: '원자재',
      WIP: '재공품',
      PRODUCT: '완제품',
    };
    return labels[type] || type;
  };

  const getItemTypeColor = (type: ItemType): string => {
    const colors: Record<ItemType, string> = {
      RAW: 'blue',
      WIP: 'orange',
      PRODUCT: 'green',
    };
    return colors[type] || 'default';
  };

  const columns = [
    {
      title: '품목코드',
      dataIndex: 'item_code',
      key: 'item_code',
      width: 150,
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: '품목명',
      dataIndex: 'item_name',
      key: 'item_name',
      width: 200,
    },
    {
      title: '품목유형',
      dataIndex: 'item_type',
      key: 'item_type',
      width: 100,
      render: (type: ItemType) => (
        <Tag color={getItemTypeColor(type)}>{getItemTypeLabel(type)}</Tag>
      ),
    },
    {
      title: '단위',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
    },
    {
      title: '규격',
      dataIndex: 'spec',
      key: 'spec',
      width: 150,
      render: (text: string) => text || '-',
    },
    {
      title: '차종',
      dataIndex: 'vehicle_model',
      key: 'vehicle_model',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '기본공급사',
      dataIndex: 'default_supplier',
      key: 'default_supplier',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '사용' : '미사용'}
        </Tag>
      ),
    },
    {
      title: '등록일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '작업',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Item) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="품목 삭제"
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
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1>품목 관리</h1>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleExportToCSV}>
            엑셀 다운로드
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            품목 등록
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="데이터 로드 오류"
          description="품목 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
        <Input
          placeholder="품목코드, 품목명으로 검색"
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value);
            setPage(1); // Reset to first page on search
          }}
          style={{ width: 300 }}
          allowClear
        />
        <Select
          placeholder="품목 유형"
          value={itemTypeFilter}
          onChange={(value) => {
            setItemTypeFilter(value);
            setPage(1); // Reset to first page on filter change
          }}
          style={{ width: 150 }}
          allowClear
        >
          <Option value="">전체</Option>
          <Option value="RAW">원자재</Option>
          <Option value="WIP">재공품</Option>
          <Option value="PRODUCT">완제품</Option>
        </Select>
      </div>

      <Table
        dataSource={itemsData?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: itemsData?.page || 1,
          pageSize: itemsData?.per_page || 20,
          total: itemsData?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `총 ${total}개`,
          onChange: (page, pageSize) => {
            setPage(page);
            setPerPage(pageSize);
          },
        }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingItem ? '품목 수정' : '새 품목 등록'}
        open={isModalOpen}
        onCancel={handleCloseModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={700}
        okText={editingItem ? '수정' : '등록'}
        cancelText="취소"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ unit: 'EA', item_type: 'RAW' }}
        >
          <Form.Item
            name="item_code"
            label="품목코드"
            rules={[{ required: true, message: '품목코드를 입력하세요' }]}
          >
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              disabled={!!editingItem}
              onChange={handleSingleTagChange('item_code')}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getItemCodeOptions()}
            />
          </Form.Item>

          <Form.Item
            name="item_name"
            label="품목명"
            rules={[{ required: true, message: '품목명을 입력하세요' }]}
          >
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              onChange={handleSingleTagChange('item_name')}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getItemNameOptions()}
            />
          </Form.Item>

          <Form.Item
            name="item_type"
            label="품목유형"
            rules={[{ required: true, message: '품목유형을 선택하세요' }]}
          >
            <Select>
              <Option value="RAW">원자재 (RAW)</Option>
              <Option value="WIP">재공품 (WIP)</Option>
              <Option value="PRODUCT">완제품 (PRODUCT)</Option>
            </Select>
          </Form.Item>

          <Form.Item name="unit" label="단위">
            <Select>
              <Option value="EA">EA (개)</Option>
              <Option value="KG">KG (킬로그램)</Option>
              <Option value="M">M (미터)</Option>
              <Option value="M2">M² (제곱미터)</Option>
              <Option value="SET">SET (세트)</Option>
              <Option value="ROLL">ROLL (롤)</Option>
            </Select>
          </Form.Item>

          <Form.Item name="spec" label="규격">
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              onChange={handleSingleTagChange('spec')}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getSpecOptions()}
            />
          </Form.Item>

          <Form.Item name="vehicle_model" label="적용 차종">
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              onChange={handleSingleTagChange('vehicle_model')}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getVehicleModelOptions()}
            />
          </Form.Item>

          <Form.Item
            name="default_supplier"
            label="기본 공급사"
            tooltip="원자재인 경우 주로 사용하는 공급사를 입력하세요"
          >
            <Input placeholder="예: 포스코, 현대제철 등" />
          </Form.Item>

          {editingItem && (
            <Form.Item name="is_active" label="사용 여부" valuePropName="checked">
              <Switch checkedChildren="사용" unCheckedChildren="미사용" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
