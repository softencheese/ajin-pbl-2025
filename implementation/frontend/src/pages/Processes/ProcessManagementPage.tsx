import { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  message,
  Space,
  Popconfirm,
  Alert,
  Select,
  Tag,
  Badge,
  Spin,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { processApi } from '../../api/processes';
import { readerLocationApi } from '../../api/readerLocations';
import type { Process, ProcessCreateRequest } from '../../types/process';
import type { ReaderLocation, ReaderLocationCreateRequest, LocationType } from '../../types/readerLocation';
import dayjs from 'dayjs';

const { Option } = Select;

export function ProcessManagementPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProcess, setEditingProcess] = useState<Process | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Reader management states
  const [isReaderModalOpen, setIsReaderModalOpen] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [isReaderFormOpen, setIsReaderFormOpen] = useState(false);
  const [editingReader, setEditingReader] = useState<ReaderLocation | null>(null);
  const [readerForm] = Form.useForm();

  // Reader test states
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [testingReader, setTestingReader] = useState<ReaderLocation | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; data?: any } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Connection status states
  const [connectionStatus, setConnectionStatus] = useState<Record<string, { connected: boolean; active_readers: number; total_readers: number }>>({});

  // Fetch processes
  const { data: processes, isLoading, error } = useQuery({
    queryKey: ['processes'],
    queryFn: () => processApi.getAll(),
    retry: 1,
  });

  // Fetch readers for selected process
  const { data: readers, isLoading: isLoadingReaders } = useQuery({
    queryKey: ['readers', selectedProcess?.id],
    queryFn: () => readerLocationApi.getAll({ process_id: selectedProcess?.id }),
    enabled: !!selectedProcess,
    retry: 1,
  });

  // Create process mutation
  const createMutation = useMutation({
    mutationFn: (payload: ProcessCreateRequest) => processApi.create(payload),
    onSuccess: () => {
      message.success('공정이 등록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['processes'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '공정 등록에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Update process mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ProcessCreateRequest> }) =>
      processApi.update(id, payload),
    onSuccess: () => {
      message.success('공정 정보가 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['processes'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '공정 수정에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Delete process mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => processApi.delete(id),
    onSuccess: () => {
      message.success('공정이 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['processes'] });
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '공정 삭제에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Create reader mutation
  const createReaderMutation = useMutation({
    mutationFn: (payload: ReaderLocationCreateRequest) => readerLocationApi.create(payload),
    onSuccess: () => {
      message.success('리더기가 등록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readers'] });
      handleCloseReaderForm();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '리더기 등록에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Update reader mutation
  const updateReaderMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ReaderLocationCreateRequest> }) =>
      readerLocationApi.update(id, payload),
    onSuccess: () => {
      message.success('리더기 정보가 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readers'] });
      handleCloseReaderForm();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '리더기 수정에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Delete reader mutation
  const deleteReaderMutation = useMutation({
    mutationFn: (id: number) => readerLocationApi.delete(id),
    onSuccess: () => {
      message.success('리더기가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readers'] });
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '리더기 삭제에 실패했습니다.';
      message.error(errorMsg);
    },
  });

  // Fetch connection status periodically
  useEffect(() => {
    const fetchConnectionStatus = async () => {
      try {
        const status = await processApi.getConnectionStatus();
        setConnectionStatus(status);
      } catch (error) {
        console.error('Failed to fetch connection status:', error);
      }
    };

    // Initial fetch
    fetchConnectionStatus();

    // Poll every 5 seconds
    const interval = setInterval(fetchConnectionStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  // Get unique process codes from existing processes
  const getProcessCodeOptions = () => {
    if (!processes?.items) return [];
    const codes = Array.from(new Set(processes.items.map(p => p.process_code)));
    return codes.map(code => ({ value: code, label: code }));
  };

  // Get unique process names from existing processes
  const getProcessNameOptions = () => {
    if (!processes?.items) return [];
    const names = Array.from(new Set(processes.items.map(p => p.process_name)));
    return names.map(name => ({ value: name, label: name }));
  };

  // Get unique production lines from existing processes
  const getProductionLineOptions = () => {
    if (!processes?.items) return [];
    const lines = Array.from(new Set(
      processes.items
        .map(p => p.production_line)
        .filter((line): line is string => line != null && line !== '')
    ));
    return lines.map(line => ({ value: line, label: line }));
  };

  const handleOpenModal = (process?: Process) => {
    if (process) {
      setEditingProcess(process);
      form.setFieldsValue(process);
    } else {
      setEditingProcess(null);
      form.resetFields();
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProcess(null);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    // Extract value from tags mode (arrays) or use as-is if strings
    const extractValue = (val: any) => {
      if (Array.isArray(val)) {
        return val.length > 0 ? val[0] : undefined;
      }
      return val || undefined;
    };

    const payload: ProcessCreateRequest = {
      process_code: extractValue(values.process_code),
      process_name: extractValue(values.process_name),
      process_order: values.process_order,
      production_line: extractValue(values.production_line),
    };

    if (editingProcess) {
      updateMutation.mutate({ id: editingProcess.id, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleOpenReaderModal = (process: Process) => {
    setSelectedProcess(process);
    setIsReaderModalOpen(true);
  };

  const handleCloseReaderModal = () => {
    setIsReaderModalOpen(false);
    setSelectedProcess(null);
  };

  const handleOpenReaderForm = (reader?: ReaderLocation) => {
    if (reader) {
      setEditingReader(reader);
      readerForm.setFieldsValue(reader);
    } else {
      setEditingReader(null);
      readerForm.resetFields();
      readerForm.setFieldsValue({ is_active: true });
    }
    setIsReaderFormOpen(true);
  };

  const handleCloseReaderForm = () => {
    setIsReaderFormOpen(false);
    setEditingReader(null);
    readerForm.resetFields();
  };

  const handleReaderSubmit = (values: any) => {
    const payload: ReaderLocationCreateRequest = {
      port_name: values.port_name,
      process_id: selectedProcess!.id,
      location_type: values.location_type,
      description: values.description || undefined,
      is_active: values.is_active !== undefined ? values.is_active : true,
    };

    if (editingReader) {
      updateReaderMutation.mutate({ id: editingReader.id, payload });
    } else {
      createReaderMutation.mutate(payload);
    }
  };

  const handleTestConnection = async (reader: ReaderLocation) => {
    setTestingReader(reader);
    setTestResult(null);
    setIsTestModalOpen(true);
    setIsTesting(true);

    try {
      const result = await readerLocationApi.testConnection(reader.port_name);
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error?.response?.data?.detail || '연결 테스트에 실패했습니다.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleCloseTestModal = () => {
    setIsTestModalOpen(false);
    setTestingReader(null);
    setTestResult(null);
    setIsTesting(false);
  };

  // Filter processes based on search text
  const filteredProcesses = processes?.items?.filter((process) => {
    if (!searchText) return true;
    const search = searchText.toLowerCase();
    return (
      process.process_code.toLowerCase().includes(search) ||
      process.process_name.toLowerCase().includes(search) ||
      process.production_line?.toLowerCase().includes(search)
    );
  });

  const getLocationTypeLabel = (type: LocationType): string => {
    const labels: Record<LocationType, string> = {
      IN: '입고',
      OUT: '출고',
      HOLD: '보류',
      DEFECT: '불량',
      FINISH: '완료',
      RETURN: '반품',
    };
    return labels[type] || type;
  };

  const getLocationTypeColor = (type: LocationType): string => {
    const colors: Record<LocationType, string> = {
      IN: 'blue',
      OUT: 'green',
      HOLD: 'orange',
      DEFECT: 'red',
      FINISH: 'purple',
      RETURN: 'gold',
    };
    return colors[type] || 'default';
  };

  const processColumns = [
    {
      title: '연결 상태',
      key: 'connection_status',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: Process) => {
        const status = connectionStatus[record.id];
        const isConnected = status?.connected || false;

        return (
          <Badge
            status={isConnected ? 'success' : 'error'}
            text={isConnected ? '연결됨' : '연결 안됨'}
          />
        );
      },
      sorter: (a: Process, b: Process) => {
        const aConnected = connectionStatus[a.id]?.connected || false;
        const bConnected = connectionStatus[b.id]?.connected || false;
        return Number(bConnected) - Number(aConnected);
      },
    },
    {
      title: '공정코드',
      dataIndex: 'process_code',
      key: 'process_code',
      width: 150,
      render: (text: string) => <strong>{text}</strong>,
      sorter: (a: Process, b: Process) => a.process_code.localeCompare(b.process_code),
    },
    {
      title: '공정명',
      dataIndex: 'process_name',
      key: 'process_name',
      width: 200,
      sorter: (a: Process, b: Process) => a.process_name.localeCompare(b.process_name),
    },
    {
      title: '공정순서',
      dataIndex: 'process_order',
      key: 'process_order',
      width: 100,
      sorter: (a: Process, b: Process) => a.process_order - b.process_order,
      defaultSortOrder: 'ascend' as const,
    },
    {
      title: '생산라인',
      dataIndex: 'production_line',
      key: 'production_line',
      width: 150,
      render: (text: string) => text || '-',
      sorter: (a: Process, b: Process) => {
        const aLine = a.production_line || '';
        const bLine = b.production_line || '';
        return aLine.localeCompare(bLine);
      },
    },
    {
      title: '등록일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
      sorter: (a: Process, b: Process) => {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      },
    },
    {
      title: '작업',
      key: 'actions',
      width: 250,
      fixed: 'right' as const,
      render: (_: any, record: Process) => (
        <Space>
          <Button
            size="small"
            icon={<ApiOutlined />}
            onClick={() => handleOpenReaderModal(record)}
          >
            리더기
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="공정 삭제"
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

  const readerColumns = [
    {
      title: '포트번호',
      dataIndex: 'port_name',
      key: 'port_name',
      width: 150,
      render: (text: string) => <strong>{text}</strong>,
      sorter: (a: ReaderLocation, b: ReaderLocation) => a.port_name.localeCompare(b.port_name),
    },
    {
      title: '위치유형',
      dataIndex: 'location_type',
      key: 'location_type',
      width: 100,
      render: (type: LocationType) => (
        <Tag color={getLocationTypeColor(type)}>{getLocationTypeLabel(type)}</Tag>
      ),
      sorter: (a: ReaderLocation, b: ReaderLocation) => a.location_type.localeCompare(b.location_type),
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      render: (text: string) => text || '-',
      sorter: (a: ReaderLocation, b: ReaderLocation) => {
        const aDesc = a.description || '';
        const bDesc = b.description || '';
        return aDesc.localeCompare(bDesc);
      },
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Badge status={isActive ? 'success' : 'default'} text={isActive ? '활성' : '비활성'} />
      ),
      sorter: (a: ReaderLocation, b: ReaderLocation) => Number(b.is_active) - Number(a.is_active),
    },
    {
      title: '작업',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: ReaderLocation) => (
        <Space>
          <Button
            size="small"
            icon={<SyncOutlined />}
            onClick={() => handleTestConnection(record)}
          >
            테스트
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenReaderForm(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="리더기 삭제"
            description="정말 삭제하시겠습니까?"
            onConfirm={() => deleteReaderMutation.mutate(record.id)}
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
        <h1>공정 관리</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
          공정 등록
        </Button>
      </div>

      {error && (
        <Alert
          message="데이터 로드 오류"
          description="공정 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="공정코드, 공정명, 생산라인으로 검색"
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 300 }}
          allowClear
        />
      </div>

      <Table
        dataSource={filteredProcesses || []}
        columns={processColumns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `총 ${total}개`,
        }}
        scroll={{ x: 1200 }}
      />

      {/* Process Form Modal */}
      <Modal
        title={editingProcess ? '공정 수정' : '새 공정 등록'}
        open={isModalOpen}
        onCancel={handleCloseModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
        okText={editingProcess ? '수정' : '등록'}
        cancelText="취소"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="process_code"
            label="공정코드"
            rules={[{ required: true, message: '공정코드를 입력하세요' }]}
          >
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              disabled={!!editingProcess}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getProcessCodeOptions()}
            />
          </Form.Item>

          <Form.Item
            name="process_name"
            label="공정명"
            rules={[{ required: true, message: '공정명을 입력하세요' }]}
          >
            <Select
              placeholder="선택 또는 입력하세요"
              showSearch
              mode="tags"
              maxTagCount={1}
              filterOption={(input, option) =>
                (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
              }
              options={getProcessNameOptions()}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="process_order"
                label="공정순서"
                rules={[
                  { required: true, message: '공정순서를 입력하세요' },
                  { type: 'number', min: 1, message: '1 이상의 숫자를 입력하세요' },
                ]}
              >
                <InputNumber
                  placeholder="예: 1, 2, 3"
                  style={{ width: '100%' }}
                  min={1}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="production_line"
                label="생산라인"
                tooltip="선택사항: 해당 공정이 수행되는 생산라인을 입력하세요"
              >
                <Select
                  placeholder="선택 또는 입력하세요"
                  showSearch
                  mode="tags"
                  maxTagCount={1}
                  allowClear
                  filterOption={(input, option) =>
                    (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={getProductionLineOptions()}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Reader Management Modal */}
      <Modal
        title={`RFID 리더기 관리 - ${selectedProcess?.process_name || ''}`}
        open={isReaderModalOpen}
        onCancel={handleCloseReaderModal}
        footer={[
          <Button key="close" onClick={handleCloseReaderModal}>
            닫기
          </Button>,
        ]}
        width={900}
      >
        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenReaderForm()}
          >
            리더기 추가
          </Button>
        </div>

        <Table
          dataSource={readers?.items || []}
          columns={readerColumns}
          rowKey="id"
          loading={isLoadingReaders}
          pagination={false}
          scroll={{ x: 800 }}
        />
      </Modal>

      {/* Reader Form Modal */}
      <Modal
        title={editingReader ? '리더기 수정' : '새 리더기 등록'}
        open={isReaderFormOpen}
        onCancel={handleCloseReaderForm}
        onOk={() => readerForm.submit()}
        confirmLoading={createReaderMutation.isPending || updateReaderMutation.isPending}
        width={600}
        okText={editingReader ? '수정' : '등록'}
        cancelText="취소"
      >
        <Form
          form={readerForm}
          layout="vertical"
          onFinish={handleReaderSubmit}
          initialValues={{ is_active: true }}
        >
          <Form.Item
            name="port_name"
            label="포트번호"
            rules={[{ required: true, message: '포트번호를 입력하세요' }]}
          >
            <Input placeholder="예: COM3, /dev/ttyUSB0, 192.168.1.100:8080" />
          </Form.Item>

          <Form.Item
            name="location_type"
            label="위치유형"
            rules={[{ required: true, message: '위치유형을 선택하세요' }]}
          >
            <Select placeholder="위치유형을 선택하세요">
              <Option value="IN">입고 (IN)</Option>
              <Option value="OUT">출고 (OUT)</Option>
              <Option value="HOLD">보류 (HOLD)</Option>
              <Option value="DEFECT">불량 (DEFECT)</Option>
              <Option value="FINISH">완료 (FINISH)</Option>
              <Option value="RETURN">반품 (RETURN)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="설명"
            tooltip="리더기 위치나 용도에 대한 설명을 입력하세요"
          >
            <Input.TextArea
              placeholder="예: 공정 입구 리더기, 1층 좌측"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="활성화 상태"
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>활성</Option>
              <Option value={false}>비활성</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Reader Test Modal */}
      <Modal
        title="RFID 리더기 연결 테스트"
        open={isTestModalOpen}
        onCancel={handleCloseTestModal}
        footer={[
          <Button key="close" onClick={handleCloseTestModal}>
            닫기
          </Button>,
          <Button
            key="retry"
            type="primary"
            icon={<SyncOutlined />}
            onClick={() => testingReader && handleTestConnection(testingReader)}
            loading={isTesting}
          >
            재시도
          </Button>,
        ]}
        width={600}
      >
        {testingReader && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 8 }}>
                <strong>포트번호:</strong> {testingReader.port_name}
              </div>
              <div style={{ marginBottom: 8 }}>
                <strong>위치유형:</strong>{' '}
                <Tag color={getLocationTypeColor(testingReader.location_type)}>
                  {getLocationTypeLabel(testingReader.location_type)}
                </Tag>
              </div>
              {testingReader.description && (
                <div>
                  <strong>설명:</strong> {testingReader.description}
                </div>
              )}
            </div>

            {isTesting ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>연결 테스트 중...</div>
              </div>
            ) : testResult ? (
              <Alert
                message={testResult.success ? '연결 성공' : '연결 실패'}
                description={
                  <div>
                    <div>{testResult.message}</div>
                    {testResult.data && (
                      <pre style={{ marginTop: 12, fontSize: '12px' }}>
                        {JSON.stringify(testResult.data, null, 2)}
                      </pre>
                    )}
                  </div>
                }
                type={testResult.success ? 'success' : 'error'}
                icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                showIcon
              />
            ) : null}
          </div>
        )}
      </Modal>
    </div>
  );
}
