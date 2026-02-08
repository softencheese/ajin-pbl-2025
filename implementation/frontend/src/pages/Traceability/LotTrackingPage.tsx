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
  Card,
  Row,
  Col,
  Statistic,
  message,
  Descriptions,
  Spin,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  ExpandOutlined,
  ShrinkOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { lotApi } from '../../api/lots';
import { palletApi } from '../../api/pallets';
import { genealogyApi, type LotGenealogyResponse } from '../../api/genealogy';
import type { Lot } from '../../types/lot';
import type { Pallet } from '../../types/pallet';

const { Option } = Select;

interface LotTraceData {
  id: number;
  lotNumber: string;
  itemCode: string;
  itemName: string;
  itemType: 'RAW' | 'WIP' | 'PRODUCT';
  quantity: number;
  initialQuantity: number;
  status: string;
  processName?: string;
  productionDate: string;
  supplier?: string;
  workerName?: string;
  barcode?: string;
  qcPassed?: boolean;
  parents?: string[];
  childLotNumbers?: string[];
  pallets?: Pallet[];
}

export function LotTrackingPage() {
  const [form] = Form.useForm();
  const [allLots, setAllLots] = useState<LotTraceData[]>([]); // All LOTs including children
  const [topLevelLots, setTopLevelLots] = useState<LotTraceData[]>([]); // Only top-level LOTs for table
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [detailModal, setDetailModal] = useState<{
    visible: boolean;
    lot: LotTraceData | null;
    genealogy: LotGenealogyResponse | null;
  }>({ visible: false, lot: null, genealogy: null });
  const [loading, setLoading] = useState(false);

  // Statistics
  const [stats, setStats] = useState({
    totalPallets: 0,
    stockCount: 0,
    holdCount: 0,
    defectCount: 0,
  });

  // Handle search
  const handleSearch = async (values: any) => {
    setLoading(true);
    try {
      const { itemName, itemType, lotStatus, lotNumber } = values;

      // Build search params
      const params: any = {};
      if (itemName) params.search = itemName;
      if (itemType) params.item_type = itemType;
      if (lotStatus && lotStatus !== 'all') params.status = lotStatus;
      if (lotNumber) params.search = lotNumber;

      // Fetch lots
      const lotsResponse = await lotApi.getAll(params);
      const lots = lotsResponse.items || [];

      // Transform lots to LotTraceData and fetch genealogy for each
      const lotMap = new Map<string, LotTraceData>();

      // Helper function to transform LOT
      const transformLot = async (lot: Lot): Promise<LotTraceData | null> => {
        // Validate required fields
        if (!lot || !lot.lot_number || !lot.id) {
          console.warn('Invalid lot data, skipping:', lot);
          return null;
        }

        // Fetch genealogy
        let genealogy: LotGenealogyResponse | null = null;
        try {
          genealogy = await genealogyApi.getByLotId(lot.id);
        } catch (error) {
          console.warn(`Failed to fetch genealogy for lot ${lot.id}:`, error);
        }

        // Fetch pallets for this lot
        let pallets: Pallet[] = [];
        try {
          const palletsData = await palletApi.getAll({ lot_id: lot.id });
          pallets = palletsData?.items || [];
        } catch (error) {
          console.warn(`Failed to fetch pallets for lot ${lot.id}:`, error);
        }

        return {
          id: lot.id,
          lotNumber: lot.lot_number,
          itemCode: lot.item?.item_code || '',
          itemName: lot.item?.item_name || '',
          itemType: (lot.item?.item_type || 'WIP') as 'RAW' | 'WIP' | 'PRODUCT',
          quantity: lot.quantity ?? 0,
          initialQuantity: lot.initial_quantity ?? 0,
          status: lot.status || 'WAIT',
          processName: lot.process_name,
          productionDate: lot.production_date || '',
          supplier: lot.supplier,
          workerName: lot.worker_name,
          barcode: lot.barcode,
          qcPassed: lot.qc_passed,
          parents: genealogy?.parents?.map(p => p.lot_number) || [],
          childLotNumbers: genealogy?.children?.map(c => c.lot_number) || [],
          pallets: pallets,
        };
      };

      // Process initial search results
      for (const lot of lots) {
        const transformed = await transformLot(lot);
        if (transformed) {
          lotMap.set(transformed.lotNumber, transformed);
        }
      }

      // Fetch all child LOTs recursively
      const fetchChildLots = async (parentLot: LotTraceData) => {
        if (!parentLot.childLotNumbers || parentLot.childLotNumbers.length === 0) {
          return;
        }

        for (const childLotNumber of parentLot.childLotNumbers) {
          // Skip if already processed
          if (lotMap.has(childLotNumber)) {
            continue;
          }

          try {
            // Fetch child LOT
            const childLotsResponse = await lotApi.getAll({ search: childLotNumber });
            const childLot = childLotsResponse.items?.find((l: Lot) => l.lot_number === childLotNumber);

            if (childLot) {
              const transformed = await transformLot(childLot);
              if (transformed) {
                lotMap.set(transformed.lotNumber, transformed);

                // Recursively fetch grandchildren
                await fetchChildLots(transformed);
              }
            }
          } catch (error) {
            console.warn(`Failed to fetch child LOT ${childLotNumber}:`, error);
          }
        }
      };

      // Fetch all descendants
      for (const lot of Array.from(lotMap.values())) {
        await fetchChildLots(lot);
      }

      const allLotsArray = Array.from(lotMap.values());

      // Separate top-level LOTs (from initial search) and all LOTs
      const topLevelLotsArray = allLotsArray.filter(lot =>
        lots.some((l: Lot) => l.lot_number === lot.lotNumber)
      );

      setAllLots(allLotsArray);
      setTopLevelLots(topLevelLotsArray);

      // Calculate statistics
      const allPallets = allLotsArray.flatMap(lot => lot.pallets || []);
      setStats({
        totalPallets: allPallets.length,
        stockCount: allPallets.filter(p => p.status === 'Stock').length,
        holdCount: allPallets.filter(p => p.status === 'Hold').length,
        defectCount: allPallets.filter(p => p.status === 'Defect').length,
      });

      message.success(`${topLevelLotsArray.length}개의 LOT를 찾았습니다.`);
    } catch (error) {
      console.error('Search failed:', error);
      message.error('검색 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Reset search
  const handleReset = () => {
    form.resetFields();
    setAllLots([]);
    setTopLevelLots([]);
    setExpandedRowKeys([]);
  };

  // Expand all
  const handleExpandAll = () => {
    const allKeys = topLevelLots
      .filter(lot => lot.childLotNumbers && lot.childLotNumbers.length > 0)
      .map(lot => lot.lotNumber);
    setExpandedRowKeys(allKeys);
  };

  // Collapse all
  const handleCollapseAll = () => {
    setExpandedRowKeys([]);
  };

  // Export to CSV
  const handleExport = () => {
    if (topLevelLots.length === 0) {
      message.warning('내보낼 데이터가 없습니다.');
      return;
    }

    const headers = ['LOT 번호', '품목명', '품목코드', '품목 유형', '공정', '수량', '상태', '생산일'];
    const csvData = topLevelLots.map(lot => [
      lot.lotNumber,
      lot.itemName,
      lot.itemCode,
      lot.itemType,
      lot.processName || '-',
      `${lot.quantity}/${lot.initialQuantity}`,
      lot.status,
      lot.productionDate,
    ]);

    const csvContent = [headers, ...csvData].map(row => row.join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `lot_tracking_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    message.success('CSV 파일이 다운로드되었습니다.');
  };

  // Show detail modal
  const handleShowDetail = async (lot: LotTraceData) => {
    try {
      const genealogy = await genealogyApi.getByLotId(lot.id);
      setDetailModal({ visible: true, lot, genealogy });
    } catch (error) {
      console.error('Failed to fetch genealogy:', error);
      setDetailModal({ visible: true, lot, genealogy: null });
    }
  };

  // Render child rows recursively
  const renderChildRows = (parentLot: LotTraceData, depth: number = 1): React.ReactNode => {
    if (!parentLot.childLotNumbers || parentLot.childLotNumbers.length === 0) {
      return null;
    }

    // Find child lots from all lots (not just top-level)
    const childLots = allLots.filter(lot =>
      parentLot.childLotNumbers?.includes(lot.lotNumber)
    );

    // If no child lots found, return null
    if (childLots.length === 0) {
      return null;
    }

    // Filter out invalid lots before mapping - more strict validation
    const validChildLots = childLots.filter(childLot => {
      const isValid = childLot &&
        childLot.lotNumber &&
        childLot.itemName &&
        childLot.itemCode &&
        typeof childLot.quantity === 'number' &&
        typeof childLot.initialQuantity === 'number' &&
        childLot.status &&
        childLot.productionDate;

      // Debug invalid lots
      if (!isValid) {
        console.warn('Invalid child lot filtered out:', {
          lotNumber: childLot?.lotNumber,
          itemName: childLot?.itemName,
          itemCode: childLot?.itemCode,
          quantity: childLot?.quantity,
          initialQuantity: childLot?.initialQuantity,
          status: childLot?.status,
          productionDate: childLot?.productionDate,
        });
      }

      return isValid;
    });

    if (validChildLots.length === 0) {
      console.warn(`No valid child lots for parent ${parentLot.lotNumber}`);
      return null;
    }

    const childElements = validChildLots.map(childLot => {
        const isExpanded = expandedRowKeys.includes(childLot.lotNumber);

        return (
          <div key={`child-${parentLot.lotNumber}-${childLot.lotNumber}`}>
            <div
              style={{
                padding: '12px 10px',
                borderBottom: '1px solid #f0f0f0',
                backgroundColor: depth % 2 === 0 ? '#fafafa' : '#ffffff',
                marginLeft: `${depth * 20}px`,
              }}
            >
              <Row gutter={16} align="middle">
                <Col span={4}>
                  {childLot.itemName || '-'}
                </Col>
                <Col span={4}>
                  {childLot.childLotNumbers && childLot.childLotNumbers.length > 0 && (
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
                  {childLot.processName || '-'}
                </Col>
                <Col span={3}>
                  <Button type="link" onClick={() => handleShowDetail(childLot)}>
                    {childLot.lotNumber}
                  </Button>
                </Col>
                <Col span={3}>{childLot.itemCode || '-'}</Col>
                <Col span={3}>
                  <Tag color={getStatusColor(childLot.status)}>
                    {getStatusLabel(childLot.status)}
                  </Tag>
                </Col>
                <Col span={2}>
                  {childLot.quantity ?? 0}/{childLot.initialQuantity ?? 0}
                </Col>
                <Col span={3}>
                  {childLot.pallets && childLot.pallets.length > 0 && (
                    <Tag color={getPalletStatusColor(childLot.pallets[0].status)}>
                      {childLot.pallets[0].status}
                    </Tag>
                  )}
                </Col>
                <Col span={2}>
                  <Button size="small" onClick={() => handleShowDetail(childLot)}>
                    보기
                  </Button>
                </Col>
              </Row>
            </div>

            {isExpanded && renderChildRows(childLot, depth + 1)}
          </div>
        );
      });

    // Return null if no valid children, otherwise wrap in fragment
    return childElements.length > 0 ? <>{childElements}</> : null;
  };

  // Table columns
  const columns: ColumnsType<LotTraceData> = [
    {
      title: '1품명',
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
          {record.childLotNumbers && record.childLotNumbers.length > 0 && (
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
          <span>{record.processName || '-'}</span>
        </Space>
      ),
    },
    {
      title: 'LOT 번호',
      dataIndex: 'lotNumber',
      key: 'lotNumber',
      width: 150,
      render: (text: string, record) => (
        <Button type="link" onClick={() => handleShowDetail(record)}>
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
        record.pallets && record.pallets.length > 0 ? (
          <Tag color={getPalletStatusColor(record.pallets[0].status)}>
            {record.pallets[0].status}
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: '생산일',
      dataIndex: 'productionDate',
      key: 'productionDate',
      width: 120,
    },
    {
      title: '작업',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button size="small" onClick={() => handleShowDetail(record)}>
          보기
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: 24 }}>LOT 추적 및 Genealogy</h1>

      {/* Search Form */}
      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline" onFinish={handleSearch}>
          <Form.Item name="itemName" label="품명">
            <Input placeholder="품명 검색" style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="itemType" label="품목 유형">
            <Select placeholder="선택" style={{ width: 150 }} allowClear>
              <Option value="RAW">원자재</Option>
              <Option value="WIP">재공품</Option>
              <Option value="PRODUCT">완제품</Option>
            </Select>
          </Form.Item>
          <Form.Item name="lotStatus" label="LOT 상태">
            <Select placeholder="선택" style={{ width: 150 }} allowClear>
              <Option value="all">전체</Option>
              <Option value="WAIT">대기</Option>
              <Option value="PROCESS">공정중</Option>
              <Option value="STOCK">재고</Option>
              <Option value="CONSUMED">소비완료</Option>
              <Option value="SHIPPED">출하완료</Option>
              <Option value="HOLD">보류</Option>
              <Option value="DEFECT">불량</Option>
            </Select>
          </Form.Item>
          <Form.Item name="lotNumber" label="LOT 번호">
            <Input placeholder="LOT 번호" style={{ width: 150 }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
                검색
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                초기화
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* Statistics */}
      {topLevelLots.length > 0 && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic title="총 팔레트 수" value={stats.totalPallets} suffix="개" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="재고 팔레트"
                  value={stats.stockCount}
                  suffix="개"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="보류 팔레트"
                  value={stats.holdCount}
                  suffix="개"
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="불량 팔레트"
                  value={stats.defectCount}
                  suffix="개"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>

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

      <Spin spinning={loading}>
        <Table
          dataSource={topLevelLots}
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
            expandedRowRender: (record) => {
              // Validate record before rendering
              if (!record || !record.lotNumber || !record.childLotNumbers || record.childLotNumbers.length === 0) {
                console.warn('Invalid record for expandedRowRender:', record?.lotNumber);
                return null;
              }

              const childContent = renderChildRows(record);

              // Only return content if it exists
              if (!childContent) {
                console.warn('No child content for:', record.lotNumber);
                return null;
              }

              return <div style={{ padding: '0' }}>{childContent}</div>;
            },
            rowExpandable: (record) => {
              // More strict check for expandable rows
              const hasValidChildren = Boolean(
                record &&
                record.childLotNumbers &&
                Array.isArray(record.childLotNumbers) &&
                record.childLotNumbers.length > 0 &&
                record.childLotNumbers.some(childLotNumber =>
                  allLots.some(lot => lot.lotNumber === childLotNumber)
                )
              );
              return hasValidChildren;
            },
            showExpandColumn: false,
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
      </Spin>

      {/* Detail Modal */}
      <Modal
        title="LOT 상세 정보 및 Genealogy"
        open={detailModal.visible}
        onCancel={() => setDetailModal({ visible: false, lot: null, genealogy: null })}
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
                <strong>{detailModal.lot.itemName}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="LOT 번호">
                <strong>{detailModal.lot.lotNumber}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="LOT 상태">
                <Tag color={getStatusColor(detailModal.lot.status)}>
                  {getStatusLabel(detailModal.lot.status)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="수량">
                {detailModal.lot.quantity} / {detailModal.lot.initialQuantity}
              </Descriptions.Item>
              <Descriptions.Item label="생산일">
                {detailModal.lot.productionDate}
              </Descriptions.Item>
              <Descriptions.Item label="공정">
                {detailModal.lot.processName || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="작업자">
                {detailModal.lot.workerName || '-'}
              </Descriptions.Item>
              {detailModal.lot.supplier && (
                <Descriptions.Item label="공급사" span={2}>
                  {detailModal.lot.supplier}
                </Descriptions.Item>
              )}
              {detailModal.lot.barcode && (
                <Descriptions.Item label="바코드" span={2}>
                  {detailModal.lot.barcode}
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* Parent LOTs (Reverse Traceability) */}
            {detailModal.genealogy?.parents && detailModal.genealogy.parents.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <h3>
                  ⬅️ 투입 LOT (역방향 추적)
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {detailModal.genealogy.parents.length}
                  </Tag>
                </h3>
                <div style={{ backgroundColor: '#f8f9fa', borderRadius: 8, padding: 15 }}>
                  {detailModal.genealogy.parents.map((parent, idx) => (
                    <Card
                      key={idx}
                      size="small"
                      style={{
                        marginBottom: 10,
                        borderLeft: '4px solid #28a745',
                      }}
                    >
                      <strong>{parent.lot_number}</strong> - {parent.item_code}
                      <div style={{ fontSize: 12, color: '#6c757d', marginTop: 4 }}>
                        유형: {getItemTypeLabel(parent.item_type as any)} |
                        소비량: {parent.quantity_consumed || '-'}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Child LOTs (Forward Traceability) */}
            {detailModal.genealogy?.children && detailModal.genealogy.children.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <h3>
                  ➡️ 생산된 LOT (정방향 추적)
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {detailModal.genealogy.children.length}
                  </Tag>
                </h3>
                <div style={{ backgroundColor: '#f8f9fa', borderRadius: 8, padding: 15 }}>
                  {detailModal.genealogy.children.map((child, idx) => (
                    <Card
                      key={idx}
                      size="small"
                      style={{
                        marginBottom: 10,
                        borderLeft: '4px solid #17a2b8',
                      }}
                    >
                      <strong>{child.lot_number}</strong> - {child.item_code}
                      <div style={{ fontSize: 12, color: '#6c757d', marginTop: 4 }}>
                        유형: {getItemTypeLabel(child.item_type as any)}
                      </div>
                    </Card>
                  ))}
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
                  size="small"
                  pagination={false}
                  columns={[
                    {
                      title: '팔레트 번호',
                      dataIndex: 'pallet_no',
                      key: 'pallet_no',
                    },
                    {
                      title: 'RFID EPC',
                      dataIndex: 'rfid_epc',
                      key: 'rfid_epc',
                    },
                    {
                      title: '상태',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => (
                        <Tag color={getPalletStatusColor(status)}>
                          {status}
                        </Tag>
                      ),
                    },
                    {
                      title: '수량',
                      dataIndex: 'quantity',
                      key: 'quantity',
                    },
                  ]}
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
