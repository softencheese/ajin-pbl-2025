import { useState } from 'react';
import { Card, Button, Tag, Modal, Form, Select, Input, Checkbox, message, Space, Popconfirm, Alert } from 'antd';
import { WifiOutlined, CloseCircleOutlined, EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { readerLocationApi } from '../../api/readerLocations';
import { processApi } from '../../api/processes';
import type { ReaderLocation, ReaderLocationCreateRequest, LocationType } from '../../types/readerLocation';

const locationTypeOptions: { label: string; value: LocationType }[] = [
  { label: 'IN (투입)', value: 'IN' },
  { label: 'OUT (산출)', value: 'OUT' },
  { label: 'HOLD (보류)', value: 'HOLD' },
  { label: 'DEFECT (불량)', value: 'DEFECT' },
  { label: 'FINISH (완료)', value: 'FINISH' },
  { label: 'RETURN (반환)', value: 'RETURN' },
];

export function ProcessMappingPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReader, setEditingReader] = useState<ReaderLocation | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: readers = [], error: readersError } = useQuery({
    queryKey: ['readerLocations'],
    queryFn: () => readerLocationApi.getAll(),
    retry: 1,
  });

  const { data: processes = [], error: processesError } = useQuery({
    queryKey: ['processes'],
    queryFn: () => processApi.getAll(),
    retry: 1,
  });

  const createMutation = useMutation({
    mutationFn: (payload: ReaderLocationCreateRequest) => readerLocationApi.create(payload),
    onSuccess: () => {
      message.success('리더기가 등록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readerLocations'] });
      handleCloseModal();
    },
    onError: () => {
      message.error('리더기 등록에 실패했습니다.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ReaderLocationCreateRequest> }) =>
      readerLocationApi.update(id, payload),
    onSuccess: () => {
      message.success('리더기 정보가 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readerLocations'] });
      handleCloseModal();
    },
    onError: () => {
      message.error('리더기 수정에 실패했습니다.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => readerLocationApi.delete(id),
    onSuccess: () => {
      message.success('리더기가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['readerLocations'] });
    },
    onError: () => {
      message.error('리더기 삭제에 실패했습니다.');
    },
  });

  const handleOpenModal = (reader?: ReaderLocation) => {
    if (reader) {
      setEditingReader(reader);
      form.setFieldsValue({
        port_name: reader.port_name,
        process_id: reader.process_id,
        location_type: reader.location_type,
        description: reader.description,
        is_active: reader.is_active,
      });
    } else {
      setEditingReader(null);
      form.resetFields();
      form.setFieldsValue({ is_active: true });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingReader(null);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    if (editingReader) {
      updateMutation.mutate({ id: editingReader.id, payload: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  // Group readers by process
  const unregisteredReaders = readers.filter(r => !r.process_id);
  const groupedReaders = processes.map(process => ({
    process,
    readers: readers.filter(r => r.process_id === process.id),
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>공정 배치 관리</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
          새 리더기 등록
        </Button>
      </div>

      {(readersError || processesError) && (
        <Alert
          message="데이터 로드 오류"
          description="API 서버가 실행 중인지 확인해주세요. (http://localhost:8000)"
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {unregisteredReaders.length > 0 && (
        <Card title="미등록 리더기" style={{ marginBottom: 16 }}>
          {unregisteredReaders.map(reader => (
            <div key={reader.id} style={{ marginBottom: 8 }}>
              <WifiOutlined style={{ marginRight: 8 }} />
              <span style={{ fontWeight: 'bold', marginRight: 8 }}>{reader.port_name}</span>
              <Button size="small" type="link" onClick={() => handleOpenModal(reader)}>
                등록하기
              </Button>
            </div>
          ))}
        </Card>
      )}

      {groupedReaders.map(({ process, readers: processReaders }) => (
        <Card
          key={process.id}
          title={`${process.process_name} ${process.production_line ? `(${process.production_line})` : ''}`}
          style={{ marginBottom: 16 }}
        >
          {processReaders.length === 0 ? (
            <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>
              등록된 리더기가 없습니다
            </div>
          ) : (
            processReaders.map(reader => (
              <div
                key={reader.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: '1px solid #f0f0f0',
                }}
              >
                <div>
                  {reader.is_connected ? (
                    <WifiOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                  ) : (
                    <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                  )}
                  <span style={{ fontWeight: 'bold', marginRight: 8 }}>{reader.port_name}</span>
                  <Tag>{reader.location_type}</Tag>
                  {reader.is_connected ? (
                    <Tag color="success">연결됨</Tag>
                  ) : (
                    <Tag color="error">끊김</Tag>
                  )}
                  {!reader.is_active && <Tag color="default">비활성</Tag>}
                  {reader.description && (
                    <span style={{ color: '#999', marginLeft: 8 }}>- {reader.description}</span>
                  )}
                </div>
                <Space>
                  <Button
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => handleOpenModal(reader)}
                  >
                    편집
                  </Button>
                  <Popconfirm
                    title="리더기 삭제"
                    description="정말 이 리더기를 삭제하시겠습니까?"
                    onConfirm={() => handleDelete(reader.id)}
                    okText="삭제"
                    cancelText="취소"
                  >
                    <Button size="small" danger icon={<DeleteOutlined />}>
                      삭제
                    </Button>
                  </Popconfirm>
                </Space>
              </div>
            ))
          )}
        </Card>
      ))}

      <Modal
        title={editingReader ? '리더기 수정' : '새 리더기 등록'}
        open={isModalOpen}
        onCancel={handleCloseModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ is_active: true }}
        >
          <Form.Item
            name="port_name"
            label="포트 이름"
            rules={[{ required: true, message: '포트 이름을 입력하세요' }]}
          >
            <Input placeholder="예: COM3, 192.168.1.100:9001" />
          </Form.Item>

          <Form.Item
            name="process_id"
            label="공정"
            rules={[{ required: true, message: '공정을 선택하세요' }]}
          >
            <Select placeholder="공정 선택">
              {processes.map(process => (
                <Select.Option key={process.id} value={process.id}>
                  {process.process_name} {process.production_line && `(${process.production_line})`}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="location_type"
            label="위치 타입"
            rules={[{ required: true, message: '위치 타입을 선택하세요' }]}
          >
            <Select placeholder="위치 타입 선택" options={locationTypeOptions} />
          </Form.Item>

          <Form.Item name="description" label="설명">
            <Input.TextArea rows={3} placeholder="리더기 설명 (선택사항)" />
          </Form.Item>

          <Form.Item name="is_active" valuePropName="checked">
            <Checkbox>활성 상태</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
