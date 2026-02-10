import { useState } from 'react';
import {
  Table,
  Card,
  Tag,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Modal,
  Descriptions,
  Timeline,
  Alert,
  Spin,
  Empty,
  Button,
} from 'antd';
import {
  SearchOutlined,
  HistoryOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { lotApi } from '../../api/lots';
import { genealogyApi, LotGenealogyResponse } from '../../api/genealogy';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface LotItem {
  id: number;
  lot_number: string;
  item?: {
    id: number;
    item_code: string;
    item_name: string;
    item_type: string;
  };
  quantity: number;
  initial_quantity: number;
  status: string;
  production_date: string;
  process_name?: string;
  supplier?: string;
  worker_name?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export function LotHistoryPage() {
  // Filters
  const [searchText, setSearchText] = useState('');
  const [itemTypeFilter, setItemTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);

  // Genealogy Modal
  const [genealogyModal, setGenealogyModal] = useState<{
    visible: boolean;
    lotId: number | null;
    lotNumber: string;
  }>({ visible: false, lotId: null, lotNumber: '' });

  // Fetch lots
  const { data: lotsData, isLoading, error, refetch } = useQuery({
    queryKey: ['lots-history', searchText, itemTypeFilter, statusFilter, dateRange, page, perPage],
    queryFn: () => lotApi.getAll({
      search: searchText || undefined,
      item_type: itemTypeFilter || undefined,
      status: statusFilter || undefined,
      page,
      per_page: perPage,
    }),
  });

  // Fetch genealogy for selected lot
  const { data: genealogyData, isLoading: genealogyLoading } = useQuery({
    queryKey: ['lot-genealogy', genealogyModal.lotId],
    queryFn: () => genealogyApi.getByLotId(genealogyModal.lotId!),
    enabled: !!genealogyModal.lotId,
  });

  const getItemTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      RAW: '원자재',
      WIP: '재공품',
      PRODUCT: '완제품',
    };
    return labels[type] || type;
  };

  const getItemTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      RAW: 'cyan',
      WIP: 'orange',
      PRODUCT: 'green',
    };
    return colors[type] || 'default';
  };

  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      WAIT: '대기',
      PROCESS: '공정중',
      STOCK: '재고',
      CONSUMED: '소진',
      SHIPPED: '출하',
      HOLD: '보류',
      DEFECT: '불량',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      WAIT: 'default',
      PROCESS: 'processing',
      STOCK: 'blue',
      CONSUMED: 'default',
      SHIPPED: 'green',
      HOLD: 'gold',
      DEFECT: 'red',
    };
    return colors[status] || 'default';
  };

  const columns: ColumnsType<LotItem> = [
    {
      title: 'LOT 번호',
      dataIndex: 'lot_number',
      key: 'lot_number',
      render: (text: string, record: LotItem) => (
        <Button
          type="link"
          onClick={() => setGenealogyModal({
            visible: true,
            lotId: record.id,
            lotNumber: text,
          })}
          style={{ padding: 0 }}
        >
          <strong>{text}</strong>
        </Button>
      ),
    },
    {
      title: '품목',
      key: 'item',
      render: (_, record: LotItem) => (
        record.item ? (
          <div>
            <Tag color={getItemTypeColor(record.item.item_type)}>
              {getItemTypeLabel(record.item.item_type)}
            </Tag>
            <div style={{ fontSize: 12, color: '#666' }}>
              {record.item.item_code}
            </div>
          </div>
        ) : '-'
      ),
    },
    {
      title: '수량',
      key: 'quantity',
      render: (_, record: LotItem) => (
        <span>
          {record.quantity}/{record.initial_quantity}
          {record.quantity < record.initial_quantity && (
            <span style={{ color: '#faad14', marginLeft: 4 }}>
              (-{record.initial_quantity - record.quantity})
            </span>
          )}
        </span>
      ),
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>
      ),
    },
    {
      title: '생산일',
      dataIndex: 'production_date',
      key: 'production_date',
    },
    {
      title: '공정',
      dataIndex: 'process_name',
      key: 'process_name',
      render: (text: string) => text || '-',
    },
    {
      title: '공급사/작업자',
      key: 'supplier_worker',
      render: (_, record: LotItem) => record.supplier || record.worker_name || '-',
    },
    {
      title: '족보',
      key: 'genealogy',
      width: 70,
      render: (_, record: LotItem) => (
        <Button
          size="small"
          icon={<HistoryOutlined />}
          onClick={() => setGenealogyModal({
            visible: true,
            lotId: record.id,
            lotNumber: record.lot_number,
          })}
        />
      ),
    },
  ];

  const renderGenealogyContent = (data: LotGenealogyResponse | undefined) => {
    if (!data) return null;

    const hasParents = data.parents && data.parents.length > 0;
    const hasChildren = data.children && data.children.length > 0;

    if (!hasParents && !hasChildren) {
      return (
        <Empty
          description="이 LOT의 족보 정보가 없습니다."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      );
    }

    return (
      <div>
        {/* Current LOT Info */}
        <Card size="small" style={{ marginBottom: 16, backgroundColor: '#e6f7ff' }}>
          <Descriptions column={3} size="small">
            <Descriptions.Item label="LOT 번호">
              <strong>{data.lot.lot_number}</strong>
            </Descriptions.Item>
            <Descriptions.Item label="품목 코드">
              {data.lot.item_code || '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Row gutter={24}>
          {/* Parents (Input LOTs) */}
          <Col span={12}>
            <Card
              title={
                <span>
                  <ArrowLeftOutlined style={{ marginRight: 8 }} />
                  투입 LOT (부모)
                </span>
              }
              size="small"
            >
              {hasParents ? (
                <Timeline
                  items={data.parents.map((parent, idx) => ({
                    key: idx,
                    color: getItemTypeColor(parent.item_type),
                    children: (
                      <div>
                        <div>
                          <strong>{parent.lot_number}</strong>
                        </div>
                        <div>
                          <Tag color={getItemTypeColor(parent.item_type)}>
                            {getItemTypeLabel(parent.item_type)}
                          </Tag>
                          <span style={{ marginLeft: 8 }}>{parent.item_code}</span>
                        </div>
                        {parent.quantity_consumed && (
                          <div style={{ color: '#666', fontSize: 12 }}>
                            투입량: {parent.quantity_consumed}개
                          </div>
                        )}
                      </div>
                    ),
                  }))}
                />
              ) : (
                <Empty
                  description="투입 LOT 없음 (원자재)"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </Card>
          </Col>

          {/* Children (Output LOTs) */}
          <Col span={12}>
            <Card
              title={
                <span>
                  <ArrowRightOutlined style={{ marginRight: 8 }} />
                  생산 LOT (자식)
                </span>
              }
              size="small"
            >
              {hasChildren ? (
                <Timeline
                  items={data.children.map((child, idx) => ({
                    key: idx,
                    color: getItemTypeColor(child.item_type),
                    children: (
                      <div>
                        <div>
                          <strong>{child.lot_number}</strong>
                        </div>
                        <div>
                          <Tag color={getItemTypeColor(child.item_type)}>
                            {getItemTypeLabel(child.item_type)}
                          </Tag>
                          <span style={{ marginLeft: 8 }}>{child.item_code}</span>
                        </div>
                        {child.quantity_consumed && (
                          <div style={{ color: '#666', fontSize: 12 }}>
                            사용량: {child.quantity_consumed}개
                          </div>
                        )}
                      </div>
                    ),
                  }))}
                />
              ) : (
                <Empty
                  description="생산된 LOT 없음"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>LOT 이력 관리</h1>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          새로고침
        </Button>
      </div>

      {error && (
        <Alert
          message="데이터 로드 오류"
          description="LOT 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Input
              placeholder="LOT 번호, 품목 검색"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => {
                setSearchText(e.target.value);
                setPage(1);
              }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="품목 유형"
              value={itemTypeFilter}
              onChange={(value) => {
                setItemTypeFilter(value);
                setPage(1);
              }}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="">전체</Option>
              <Option value="RAW">원자재</Option>
              <Option value="WIP">재공품</Option>
              <Option value="PRODUCT">완제품</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="상태"
              value={statusFilter}
              onChange={(value) => {
                setStatusFilter(value);
                setPage(1);
              }}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="">전체</Option>
              <Option value="STOCK">재고</Option>
              <Option value="CONSUMED">소진</Option>
              <Option value="SHIPPED">출하</Option>
              <Option value="HOLD">보류</Option>
              <Option value="DEFECT">불량</Option>
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              placeholder={['시작일', '종료일']}
              onChange={(dates) => {
                setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null);
                setPage(1);
              }}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </Card>

      {/* LOT Table */}
      <Table
        dataSource={lotsData?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: lotsData?.page || 1,
          pageSize: lotsData?.per_page || 20,
          total: lotsData?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `총 ${total}개`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage);
            setPerPage(newPageSize);
          },
        }}
        locale={{
          emptyText: (
            <Empty
              description="LOT 이력이 없습니다"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ),
        }}
      />

      {/* Genealogy Modal */}
      <Modal
        title={
          <span>
            <HistoryOutlined style={{ marginRight: 8 }} />
            LOT 족보 - {genealogyModal.lotNumber}
          </span>
        }
        open={genealogyModal.visible}
        onCancel={() => setGenealogyModal({ visible: false, lotId: null, lotNumber: '' })}
        footer={null}
        width={800}
      >
        {genealogyLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
          </div>
        ) : (
          renderGenealogyContent(genealogyData)
        )}
      </Modal>
    </div>
  );
}
