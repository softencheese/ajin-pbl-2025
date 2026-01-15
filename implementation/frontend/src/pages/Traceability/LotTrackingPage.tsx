import { useState } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Table,
  Modal,
  Space,
  Tag,
  DatePicker,
  Card,
  Row,
  Col,
  Statistic,
  Alert,
  message,
  Descriptions,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  ExpandOutlined,
  ShrinkOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface Pallet {
  id: string;
  palletNo: string;
  paletteNumber: number;
  rfidEpc: string | null;
  quantity: number;
  status: string;
}

interface LotTraceData {
  lotNumber: string;
  itemCode: string;
  itemName: string;
  itemType: 'RAW' | 'WIP' | 'PRODUCT';
  quantity: number;
  initialQuantity: number;
  consumed: number;
  status: string;
  processName: string;
  productionDate: string;
  inputTime: string;
  outputTime?: string;
  supplier?: string;
  workerName?: string;
  barcode?: string;
  qcPassed?: boolean;
  hasParent: boolean;
  parents: string[];
  children: string[];
  pallets: Pallet[];
}

// Mock database
const mockLotDatabase: Record<string, LotTraceData> = {
  'IN-241210-001': {
    lotNumber: 'IN-241210-001',
    itemCode: 'STEEL-SPCC',
    itemName: 'SPCC 냉연강판',
    itemType: 'RAW',
    quantity: 0,
    initialQuantity: 500,
    consumed: 500,
    status: 'CONSUMED',
    processName: '입고',
    productionDate: '2024-12-10',
    inputTime: '2024-12-10 14:30:00',
    supplier: '포스코',
    barcode: '251018226687',
    hasParent: false,
    parents: [],
    children: ['SH-241211-001'],
    pallets: [],
  },
  'SH-241211-001': {
    lotNumber: 'SH-241211-001',
    itemCode: '71412-T6000S',
    itemName: 'PNL-FR DR INR LH',
    itemType: 'WIP',
    quantity: 0,
    initialQuantity: 400,
    consumed: 400,
    status: 'CONSUMED',
    processName: '샤링',
    productionDate: '2024-12-11',
    inputTime: '2024-12-11 08:00:00',
    outputTime: '2024-12-11 09:30:00',
    workerName: '김철수',
    barcode: 'SH-BAR-001',
    hasParent: true,
    parents: ['IN-241210-001'],
    children: ['PR-241211-001'],
    pallets: [
      {
        id: 'SH-241211-001-PLT-001',
        palletNo: 'PLT-2024-030',
        paletteNumber: 1,
        rfidEpc: 'E2801170000002036B3D8CC9',
        quantity: 50,
        status: 'Deregistered',
      },
      {
        id: 'SH-241211-001-PLT-002',
        palletNo: 'PLT-2024-031',
        paletteNumber: 2,
        rfidEpc: 'E2801170000002036B3D8CCA',
        quantity: 50,
        status: 'Deregistered',
      },
    ],
  },
  'PR-241211-001': {
    lotNumber: 'PR-241211-001',
    itemCode: '71412-T6000S-PR',
    itemName: 'PNL-FR DR INR (프레스)',
    itemType: 'WIP',
    quantity: 0,
    initialQuantity: 400,
    consumed: 400,
    status: 'CONSUMED',
    processName: '프레스',
    productionDate: '2024-12-11',
    inputTime: '2024-12-11 11:30:00',
    outputTime: '2024-12-11 13:15:00',
    workerName: '박민수',
    barcode: 'PR-BAR-001',
    hasParent: true,
    parents: ['SH-241211-001'],
    children: ['AS-241215-001'],
    pallets: [
      {
        id: 'PR-241211-001-PLT-001',
        palletNo: 'PLT-2024-040',
        paletteNumber: 1,
        rfidEpc: 'E2801170000002036B3D8CD1',
        quantity: 50,
        status: 'Deregistered',
      },
    ],
  },
  'AS-241215-001': {
    lotNumber: 'AS-241215-001',
    itemCode: '76211-GI000',
    itemName: 'ASSY-FR DR MODULE',
    itemType: 'PRODUCT',
    quantity: 50,
    initialQuantity: 50,
    consumed: 0,
    status: 'STOCK',
    processName: '조립',
    productionDate: '2024-12-15',
    inputTime: '2024-12-15 14:00:00',
    outputTime: '2024-12-15 16:30:00',
    workerName: '강지은',
    qcPassed: true,
    hasParent: true,
    parents: ['PR-241211-001'],
    children: [],
    pallets: [
      {
        id: 'AS-241215-001-PLT-001',
        palletNo: 'PLT-2024-052',
        paletteNumber: 1,
        rfidEpc: 'E2801170000002036B3D8CDD',
        quantity: 50,
        status: 'Finished',
      },
    ],
  },
  'IN-241208-002': {
    lotNumber: 'IN-241208-002',
    itemCode: 'STEEL-SPCC',
    itemName: 'SPCC 냉연강판',
    itemType: 'RAW',
    quantity: 300,
    initialQuantity: 500,
    consumed: 200,
    status: 'STOCK',
    processName: '입고',
    productionDate: '2024-12-08',
    inputTime: '2024-12-08 10:00:00',
    supplier: '포스코',
    barcode: '251018226688',
    hasParent: false,
    parents: [],
    children: ['SH-241209-003'],
    pallets: [],
  },
  'SH-241209-003': {
    lotNumber: 'SH-241209-003',
    itemCode: '71412-T6000S',
    itemName: 'PNL-FR DR INR LH',
    itemType: 'WIP',
    quantity: 250,
    initialQuantity: 250,
    consumed: 0,
    status: 'STOCK',
    processName: '샤링',
    productionDate: '2024-12-09',
    inputTime: '2024-12-09 09:00:00',
    outputTime: '2024-12-09 10:30:00',
    workerName: '김철수',
    hasParent: true,
    parents: ['IN-241208-002'],
    children: [],
    pallets: [
      {
        id: 'SH-241209-003-PLT-001',
        palletNo: 'PLT-2024-025',
        paletteNumber: 1,
        rfidEpc: 'E2801170000002036B3D8CC8',
        quantity: 50,
        status: 'Stock',
      },
      {
        id: 'SH-241209-003-PLT-002',
        palletNo: 'PLT-2024-026',
        paletteNumber: 2,
        rfidEpc: 'E2801170000002036B3D8CC9',
        quantity: 50,
        status: 'Stock',
      },
    ],
  },
};

export function LotTrackingPage() {
  const [form] = Form.useForm();
  const [searchResults, setSearchResults] = useState<LotTraceData[]>([]);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [detailModal, setDetailModal] = useState<{
    visible: boolean;
    lot: LotTraceData | null;
  }>({ visible: false, lot: null });

  // Statistics
  const [stats, setStats] = useState({
    totalPallets: 0,
    stockCount: 0,
    holdCount: 0,
    defectCount: 0,
  });

  // Handle search
  const handleSearch = (values: any) => {
    const { itemName, itemType, lotStatus, lotNumber } = values;

    // Filter lots
    const results = Object.values(mockLotDatabase)
      .filter(lot => {
        const matchItemName = !itemName || lot.itemName.includes(itemName);
        const matchItemType = !itemType || lot.itemType === itemType;
        const matchLotNumber = !lotNumber || lot.lotNumber.includes(lotNumber);
        const matchStatus = !lotStatus || lotStatus === 'all' || lot.status === lotStatus;
        return matchItemName && matchItemType && matchLotNumber && matchStatus;
      })
      .sort((a, b) => {
        // Sort by process order
        const processOrder: Record<string, number> = {
          '입고': 1,
          '부품 입고': 1,
          '샤링': 2,
          '프레스': 3,
          '조립': 4,
        };
        return (processOrder[a.processName] || 0) - (processOrder[b.processName] || 0);
      });

    setSearchResults(results);

    // Calculate statistics
    const allPallets = results.flatMap(lot => lot.pallets);
    setStats({
      totalPallets: allPallets.length,
      stockCount: allPallets.filter(p => p.status === 'Stock').length,
      holdCount: allPallets.filter(p => p.status === 'Hold').length,
      defectCount: allPallets.filter(p => p.status === 'Defect').length,
    });

    message.success(`${results.length}개의 LOT를 찾았습니다.`);
  };

  // Reset search
  const handleReset = () => {
    form.resetFields();
    setSearchResults([]);
    setExpandedRowKeys([]);
  };

  // Expand all
  const handleExpandAll = () => {
    const allKeys = searchResults
      .filter(lot => lot.children.length > 0)
      .map(lot => lot.lotNumber);
    setExpandedRowKeys(allKeys);
  };

  // Collapse all
  const handleCollapseAll = () => {
    setExpandedRowKeys([]);
  };

  // Export to CSV
  const handleExport = () => {
    if (searchResults.length === 0) {
      message.warning('내보낼 데이터가 없습니다.');
      return;
    }

    const headers = ['LOT 번호', '품목명', '품목코드', '품목 유형', '공정', '수량', '상태', '생산일'];
    const csvData = searchResults.map(lot => [
      lot.lotNumber,
      lot.itemName,
      lot.itemCode,
      lot.itemType,
      lot.processName,
      `${lot.quantity}/${lot.initialQuantity}`,
      lot.status,
      lot.productionDate,
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const fileName = `LOT추적_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;

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

  // Show detail modal
  const handleShowDetail = (lotNumber: string) => {
    const lot = mockLotDatabase[lotNumber];
    if (lot) {
      setDetailModal({ visible: true, lot });
    }
  };

  // Render child rows recursively
  const renderChildRows = (parentLot: LotTraceData, depth: number = 1): React.ReactNode => {
    if (!parentLot.children || parentLot.children.length === 0) {
      return null;
    }

    return parentLot.children.map(childLotNumber => {
      const childLot = mockLotDatabase[childLotNumber];
      if (!childLot) return null;

      const isExpanded = expandedRowKeys.includes(childLot.lotNumber);

      return (
        <div key={childLot.lotNumber}>
          <div
            style={{
              padding: '12px 10px',
              borderBottom: '1px solid #e9ecef',
              backgroundColor: '#f8f9fa',
              paddingLeft: `${30 * depth}px`,
            }}
          >
            <Row gutter={16} align="middle">
              <Col span={4}>
                {childLot.itemName}
              </Col>
              <Col span={4}>
                {childLot.children.length > 0 && (
                  <span
                    style={{ cursor: 'pointer', marginRight: 8, color: '#667eea' }}
                    onClick={() => {
                      setExpandedRowKeys(
                        isExpanded
                          ? expandedRowKeys.filter(key => key !== childLot.lotNumber)
                          : [...expandedRowKeys, childLot.lotNumber]
                      );
                    }}
                  >
                    {isExpanded ? '▼' : '▶'}
                  </span>
                )}
                <Tag color={getItemTypeColor(childLot.itemType)}>
                  {getItemTypeLabel(childLot.itemType)}
                </Tag>
                {childLot.processName}
              </Col>
              <Col span={3}>
                <Button type="link" onClick={() => handleShowDetail(childLot.lotNumber)}>
                  {childLot.lotNumber}
                </Button>
              </Col>
              <Col span={3}>{childLot.itemCode}</Col>
              <Col span={3}>
                <Tag color={getStatusColor(childLot.status)}>
                  {getStatusLabel(childLot.status)}
                </Tag>
              </Col>
              <Col span={2}>{childLot.quantity}/{childLot.initialQuantity}</Col>
              <Col span={3}>
                {childLot.pallets.length > 0 && (
                  <Tag color={getPalletStatusColor(childLot.pallets[0].status)}>
                    {childLot.pallets[0].status}
                  </Tag>
                )}
              </Col>
              <Col span={2}>
                <Button size="small" onClick={() => handleShowDetail(childLot.lotNumber)}>
                  보기
                </Button>
              </Col>
            </Row>
          </div>

          {isExpanded && renderChildRows(childLot, depth + 1)}
        </div>
      );
    });
  };

  // Table columns
  const columns: ColumnsType<LotTraceData> = [
    {
      title: '품명',
      dataIndex: 'itemName',
      key: 'itemName',
      width: 200,
    },
    {
      title: '공정/팔레트',
      key: 'process',
      width: 200,
      render: (_, record) => (
        <Space>
          {record.children.length > 0 && (
            <span
              style={{ cursor: 'pointer', color: '#667eea' }}
              onClick={() => {
                const isExpanded = expandedRowKeys.includes(record.lotNumber);
                setExpandedRowKeys(
                  isExpanded
                    ? expandedRowKeys.filter(key => key !== record.lotNumber)
                    : [...expandedRowKeys, record.lotNumber]
                );
              }}
            >
              {expandedRowKeys.includes(record.lotNumber) ? '▼' : '▶'}
            </span>
          )}
          <Tag color={getItemTypeColor(record.itemType)}>
            {getItemTypeLabel(record.itemType)}
          </Tag>
          <span>{record.processName}</span>
        </Space>
      ),
    },
    {
      title: 'LOT 번호',
      dataIndex: 'lotNumber',
      key: 'lotNumber',
      width: 150,
      render: (text: string) => (
        <Button type="link" onClick={() => handleShowDetail(text)}>
          {text}
        </Button>
      ),
    },
    {
      title: '품목코드',
      dataIndex: 'itemCode',
      key: 'itemCode',
      width: 150,
    },
    {
      title: 'LOT 상태',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusLabel(status)}
        </Tag>
      ),
    },
    {
      title: '수량',
      key: 'quantity',
      width: 120,
      render: (_, record) => `${record.quantity}/${record.initialQuantity}`,
    },
    {
      title: '팔레트 상태',
      key: 'palletStatus',
      width: 120,
      render: (_, record) =>
        record.pallets.length > 0 ? (
          <Tag color={getPalletStatusColor(record.pallets[0].status)}>
            {record.pallets[0].status}
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: '상세',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button size="small" onClick={() => handleShowDetail(record.lotNumber)}>
          보기
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>LOT 추적 및 관리</h1>

      <Card title="검색 조건" style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSearch}
          initialValues={{
            itemType: 'RAW',
            startDate: dayjs('2024-12-01'),
            endDate: dayjs('2024-12-17'),
            lotStatus: 'all',
          }}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="itemName" label="품명 (제품명/부품명)">
                <Input placeholder="예: PNL-FR DR INR" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="itemType" label="품목 유형">
                <Select>
                  <Option value="RAW">원자재 (RAW)</Option>
                  <Option value="WIP">재공품 (WIP)</Option>
                  <Option value="PRODUCT">완제품 (PRODUCT)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="startDate" label="시작 일시">
                <DatePicker showTime style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="endDate" label="종료 일시">
                <DatePicker showTime style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="lotNumber" label="LOT 번호 (선택)">
                <Input placeholder="예: SH-231211-001" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="lotStatus" label="LOT 상태">
                <Select>
                  <Option value="all">전체</Option>
                  <Option value="WAIT">대기 (WAIT)</Option>
                  <Option value="PROCESS">공정 진행 중 (PROCESS)</Option>
                  <Option value="STOCK">재고 (STOCK)</Option>
                  <Option value="CONSUMED">소비 완료 (CONSUMED)</Option>
                  <Option value="SHIPPED">출하 완료 (SHIPPED)</Option>
                  <Option value="HOLD">보류 (HOLD)</Option>
                  <Option value="DEFECT">불량 (DEFECT)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12} style={{ display: 'flex', alignItems: 'flex-end' }}>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                    검색
                  </Button>
                  <Button onClick={handleReset} icon={<ReloadOutlined />}>
                    초기화
                  </Button>
                </Space>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {searchResults.length > 0 && (
        <>
          <Card style={{ marginBottom: 16, backgroundColor: '#fff3cd' }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic title="전체 팔레트" value={stats.totalPallets} prefix="📦" />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Stock"
                  value={stats.stockCount}
                  prefix="✅"
                  valueStyle={{ color: '#28a745' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Hold"
                  value={stats.holdCount}
                  prefix="⚠️"
                  valueStyle={{ color: '#ffc107' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Defect"
                  value={stats.defectCount}
                  prefix="❌"
                  valueStyle={{ color: '#dc3545' }}
                />
              </Col>
            </Row>
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <Space>
              <Button icon={<ExpandOutlined />} onClick={handleExpandAll}>
                전체 확장
              </Button>
              <Button icon={<ShrinkOutlined />} onClick={handleCollapseAll}>
                전체 접기
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                엑셀 내보내기
              </Button>
            </Space>
          </Card>
        </>
      )}

      <Table
        dataSource={searchResults}
        columns={columns}
        rowKey="lotNumber"
        pagination={{ pageSize: 20 }}
        expandable={{
          expandedRowKeys,
          onExpand: (expanded, record) => {
            setExpandedRowKeys(
              expanded
                ? [...expandedRowKeys, record.lotNumber]
                : expandedRowKeys.filter(key => key !== record.lotNumber)
            );
          },
          expandedRowRender: (record) => (
            <div style={{ backgroundColor: '#f8f9fa' }}>
              {renderChildRows(record)}
            </div>
          ),
          rowExpandable: (record) => record.children.length > 0,
        }}
        locale={{
          emptyText: (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#6c757d' }}>
              <div style={{ fontSize: 48, marginBottom: 15 }}>🔍</div>
              <h3>검색 조건을 입력하고 검색 버튼을 클릭하세요</h3>
              <p>품명과 기간을 선택하여 공정 추적을 시작할 수 있습니다</p>
            </div>
          ),
        }}
      />

      {/* Detail Modal */}
      <Modal
        title="LOT 상세 정보 및 Genealogy"
        open={detailModal.visible}
        onCancel={() => setDetailModal({ visible: false, lot: null })}
        footer={null}
        width={800}
      >
        {detailModal.lot && (
          <div>
            <h3>기본 정보</h3>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="품목 유형">
                <Tag color={getItemTypeColor(detailModal.lot.itemType)}>
                  {getItemTypeLabel(detailModal.lot.itemType)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="품목코드">
                <strong>{detailModal.lot.itemCode}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="품명" span={2}>
                {detailModal.lot.itemName}
              </Descriptions.Item>
              <Descriptions.Item label="LOT 번호">
                <strong style={{ color: '#667eea' }}>{detailModal.lot.lotNumber}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="LOT 상태">
                <Tag color={getStatusColor(detailModal.lot.status)}>
                  {getStatusLabel(detailModal.lot.status)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="바코드">
                {detailModal.lot.barcode || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="공정">
                {detailModal.lot.processName}
              </Descriptions.Item>
              <Descriptions.Item label="생산/입고일">
                {detailModal.lot.productionDate}
              </Descriptions.Item>
              <Descriptions.Item label="수량">
                {detailModal.lot.quantity} / {detailModal.lot.initialQuantity} (초기)
              </Descriptions.Item>
              {detailModal.lot.workerName && (
                <Descriptions.Item label="작업자">
                  {detailModal.lot.workerName}
                </Descriptions.Item>
              )}
              {detailModal.lot.supplier && (
                <Descriptions.Item label="공급사">
                  {detailModal.lot.supplier}
                </Descriptions.Item>
              )}
              {detailModal.lot.qcPassed !== undefined && (
                <Descriptions.Item label="QC 합격">
                  {detailModal.lot.qcPassed ? '✅ 합격' : '❌ 불합격'}
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* Parent LOTs (Reverse Traceability) */}
            {detailModal.lot.parents && detailModal.lot.parents.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <h3>
                  ⬅️ 투입 LOT (역방향 추적)
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {detailModal.lot.parents.length}
                  </Tag>
                </h3>
                <div style={{ backgroundColor: '#f8f9fa', borderRadius: 8, padding: 15 }}>
                  {detailModal.lot.parents.map(parentLotNumber => {
                    const parentLot = mockLotDatabase[parentLotNumber];
                    if (!parentLot) return null;
                    return (
                      <Card
                        key={parentLotNumber}
                        size="small"
                        hoverable
                        onClick={() => setDetailModal({ visible: true, lot: parentLot })}
                        style={{
                          marginBottom: 10,
                          borderLeft: '4px solid #28a745',
                          cursor: 'pointer',
                        }}
                      >
                        <strong>{parentLot.lotNumber}</strong> - {parentLot.itemName}
                        <div style={{ fontSize: 12, color: '#6c757d', marginTop: 4 }}>
                          품목코드: {parentLot.itemCode} | 유형:{' '}
                          {getItemTypeLabel(parentLot.itemType)} | 수량: {parentLot.initialQuantity}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Child LOTs (Forward Traceability) */}
            {detailModal.lot.children && detailModal.lot.children.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <h3>
                  ➡️ 생산된 LOT (정방향 추적)
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {detailModal.lot.children.length}
                  </Tag>
                </h3>
                <div style={{ backgroundColor: '#f8f9fa', borderRadius: 8, padding: 15 }}>
                  {detailModal.lot.children.map(childLotNumber => {
                    const childLot = mockLotDatabase[childLotNumber];
                    if (!childLot) return null;
                    return (
                      <Card
                        key={childLotNumber}
                        size="small"
                        hoverable
                        onClick={() => setDetailModal({ visible: true, lot: childLot })}
                        style={{
                          marginBottom: 10,
                          borderLeft: '4px solid #17a2b8',
                          cursor: 'pointer',
                        }}
                      >
                        <strong>{childLot.lotNumber}</strong> - {childLot.itemName}
                        <div style={{ fontSize: 12, color: '#6c757d', marginTop: 4 }}>
                          품목코드: {childLot.itemCode} | 유형:{' '}
                          {getItemTypeLabel(childLot.itemType)} | 수량: {childLot.initialQuantity}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Pallets */}
            {detailModal.lot.pallets && detailModal.lot.pallets.length > 0 && (
              <div>
                <h3>
                  📦 팔레트 정보
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {detailModal.lot.pallets.length}
                  </Tag>
                </h3>
                <Table
                  dataSource={detailModal.lot.pallets}
                  columns={[
                    {
                      title: '팔레트 번호',
                      dataIndex: 'palletNo',
                      key: 'palletNo',
                      render: (text: string) => <strong>{text}</strong>,
                    },
                    {
                      title: 'RFID EPC',
                      dataIndex: 'rfidEpc',
                      key: 'rfidEpc',
                      render: (text: string) =>
                        text ? (
                          <code style={{ fontSize: 12 }}>{text}</code>
                        ) : (
                          <Tag color="default">미등록</Tag>
                        ),
                    },
                    {
                      title: '수량',
                      dataIndex: 'quantity',
                      key: 'quantity',
                    },
                    {
                      title: '팔레트 상태',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => (
                        <Tag color={getPalletStatusColor(status)}>{status}</Tag>
                      ),
                    },
                  ]}
                  rowKey="id"
                  pagination={false}
                  size="small"
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

// Helper functions
function getItemTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    RAW: '원자재',
    WIP: '재공품',
    PRODUCT: '완제품',
  };
  return labels[type] || type;
}

function getItemTypeColor(type: string): string {
  const colors: Record<string, string> = {
    RAW: 'cyan',
    WIP: 'orange',
    PRODUCT: 'green',
  };
  return colors[type] || 'default';
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    WAIT: '대기',
    PROCESS: '공정중',
    STOCK: '재고',
    CONSUMED: '소비완료',
    SHIPPED: '출하완료',
    HOLD: '보류',
    DEFECT: '불량',
  };
  return labels[status] || status;
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    WAIT: 'default',
    PROCESS: 'processing',
    STOCK: 'success',
    CONSUMED: 'default',
    SHIPPED: 'cyan',
    HOLD: 'warning',
    DEFECT: 'error',
  };
  return colors[status] || 'default';
}

function getPalletStatusColor(status: string): string {
  const colors: Record<string, string> = {
    Generated: 'default',
    Empty: 'default',
    Stock: 'success',
    Consuming: 'processing',
    Producing: 'default',
    Finished: 'cyan',
    Deregistered: 'default',
    Hold: 'warning',
    Defect: 'error',
  };
  return colors[status] || 'default';
}
