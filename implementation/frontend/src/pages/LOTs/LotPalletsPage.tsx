import { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Table,
  Modal,
  Space,
  Tag,
  InputNumber,
  DatePicker,
  message,
  Alert,
  Card,
  Row,
  Col,
  Collapse,
  Progress,
} from 'antd';
import {
  PlusOutlined,
  TagsOutlined,
  BarcodeScannerOutlined,
  ExpandOutlined,
  ShrinkOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { itemApi } from '../../api/items';
import type { Item } from '../../types/item';

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;

interface Palette {
  id: string;
  paletteNumber: number;
  quantity: number;
  rfidEpc: string | null;
  status: string;
  rfidRegisteredAt?: string;
}

interface LotData {
  lotNumber: string;
  itemCode: string;
  itemName: string;
  itemType: 'RAW' | 'WIP' | 'PRODUCT';
  quantity: number;
  initialQuantity: number;
  status: string;
  productionDate: string;
  barcode: string;
  palettes: Palette[];
  paletteCount: number;
  rfidRegistered: number;
  processName?: string;
  workerName?: string;
  supplier?: string;
  notes?: string;
  inputLot?: string;
  inputQuantity?: number;
}

interface BulkRfidItem {
  lotNumber: string;
  itemCode: string;
  itemName: string;
  paletteId: string;
  paletteNumber: number;
  quantity: number;
  rfidEpc?: string;
}

export function LotPalletsPage() {
  const [form] = Form.useForm();
  const [lotData, setLotData] = useState<LotData[]>([]);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [processType, setProcessType] = useState<string>('RAW');
  const [paletteCount, setPaletteCount] = useState<number>(0);

  // Fetch items from API
  const { data: itemsData } = useQuery({
    queryKey: ['items'],
    queryFn: () => itemApi.getAll({ is_active: true }),
  });

  // Modals
  const [paletteDetailModal, setPaletteDetailModal] = useState<{
    visible: boolean;
    lot: LotData | null;
    palette: Palette | null;
  }>({ visible: false, lot: null, palette: null });

  const [rfidModal, setRfidModal] = useState<{
    visible: boolean;
    lotNumber: string;
    paletteId: string;
  }>({ visible: false, lotNumber: '', paletteId: '' });

  const [bulkRfidModal, setBulkRfidModal] = useState<{
    visible: boolean;
    items: BulkRfidItem[];
    currentIndex: number;
  }>({ visible: false, items: [], currentIndex: 0 });

  // Filters
  const [filterLotNumber, setFilterLotNumber] = useState<string>('');
  const [filterItemType, setFilterItemType] = useState<string>('');
  const [filterItemCode, setFilterItemCode] = useState<string>('');
  const [filterDate, setFilterDate] = useState<string>('');

  // LOT counters
  const [lotCounters, setLotCounters] = useState({
    IN: 1,
    SH: 1,
    PR: 1,
    AS: 1,
  });
  const [barcodeCounter, setBarcodeCounter] = useState(1);

  // Get filtered items based on process type
  const getFilteredItems = (): Item[] => {
    if (!itemsData?.items) return [];

    // Map process types to item types
    const processItemTypeMap: Record<string, string[]> = {
      'RAW': ['RAW'], // 원자재 입고
      '2': ['WIP'], // 샤링 - WIP 생산
      '3': ['WIP'], // 프레스 - WIP 생산
      '4': ['PRODUCT'], // 조립 - 완제품 생산
    };

    const allowedTypes = processItemTypeMap[processType] || [];
    return itemsData.items.filter(item => allowedTypes.includes(item.item_type));
  };

  // Get unique suppliers from items
  const getSupplierOptions = () => {
    if (!itemsData?.items) return [];

    const suppliers = itemsData.items
      .map(item => item.default_supplier)
      .filter((supplier): supplier is string => supplier != null && supplier !== '');

    const uniqueSuppliers = Array.from(new Set(suppliers));

    return uniqueSuppliers.map(supplier => ({
      value: supplier,
      label: supplier,
    }));
  };

  // Calculate palette count when quantity or capacity changes
  const calculatePaletteCount = (quantity: number, capacity: number) => {
    if (processType === 'RAW') {
      setPaletteCount(0);
      return;
    }
    const count = Math.ceil(quantity / capacity);
    setPaletteCount(count);
  };

  // Generate LOT number
  const generateLotNumber = (type: string) => {
    const prefixMap: Record<string, string> = {
      RAW: 'IN',
      '2': 'SH',
      '3': 'PR',
      '4': 'AS',
    };
    const prefix = prefixMap[type] || 'XX';
    const today = dayjs().format('YYMMDD');
    const seq = String(lotCounters[prefix as keyof typeof lotCounters] || 1).padStart(3, '0');
    return `${prefix}-${today}-${seq}`;
  };

  // Generate barcode
  const generateBarcode = () => {
    const today = dayjs().format('YYMMDD');
    const seq = String(barcodeCounter).padStart(6, '0');
    return `BC${today}${seq}`;
  };

  // Handle process type change
  const handleProcessTypeChange = (value: string) => {
    setProcessType(value);
    const lotNumber = generateLotNumber(value);
    form.setFieldsValue({ lotNumber, barcode: generateBarcode() });

    if (value === 'RAW') {
      setPaletteCount(0);
    } else {
      const quantity = form.getFieldValue('quantity') || 0;
      const capacity = form.getFieldValue('paletteCapacity') || 1;
      calculatePaletteCount(quantity, capacity);
    }
  };

  // Create LOT
  const handleCreateLot = (values: any) => {
    const isRaw = processType === 'RAW';

    if (isRaw) {
      // Create raw material LOT
      const lot: LotData = {
        lotNumber: values.lotNumber,
        itemCode: values.rawItemId,
        itemName: 'Raw Material', // In real app, get from selection
        itemType: 'RAW',
        quantity: values.quantity,
        initialQuantity: values.quantity,
        status: 'STOCK',
        productionDate: values.productionDate.format('YYYY-MM-DD'),
        supplier: Array.isArray(values.supplier) ? values.supplier[0] : values.supplier,
        barcode: values.barcode,
        notes: values.notes,
        palettes: [],
        paletteCount: 0,
        rfidRegistered: 0,
      };

      setLotData([...lotData, lot]);
      setLotCounters({ ...lotCounters, IN: lotCounters.IN + 1 });
      message.success(`원자재 LOT ${lot.lotNumber} 등록 완료!`);
    } else {
      // Create production LOT with palettes
      const palettes: Palette[] = [];
      const capacity = values.paletteCapacity;
      const quantity = values.quantity;
      const count = Math.ceil(quantity / capacity);

      for (let i = 1; i <= count; i++) {
        const paletteQuantity = i === count
          ? quantity - (capacity * (count - 1))
          : capacity;

        palettes.push({
          id: `${values.lotNumber}-PLT-${String(i).padStart(3, '0')}`,
          paletteNumber: i,
          quantity: paletteQuantity,
          rfidEpc: null,
          status: 'Generated',
        });
      }

      const lot: LotData = {
        lotNumber: values.lotNumber,
        itemCode: values.prodItemId,
        itemName: 'Production Item', // In real app, get from selection
        itemType: processType === '4' ? 'PRODUCT' : 'WIP',
        quantity: values.quantity,
        initialQuantity: values.quantity,
        status: 'STOCK',
        productionDate: values.productionDate.format('YYYY-MM-DD'),
        processName: ['샤링', '프레스', '조립'][parseInt(processType) - 2],
        workerName: values.worker,
        barcode: values.barcode,
        palettes,
        paletteCount: count,
        rfidRegistered: 0,
        inputLot: values.inputLot,
        inputQuantity: values.inputQuantity,
        notes: values.notes,
      };

      setLotData([...lotData, lot]);
      const prefix = values.lotNumber.split('-')[0] as keyof typeof lotCounters;
      setLotCounters({ ...lotCounters, [prefix]: lotCounters[prefix] + 1 });
      message.success(`생산 LOT ${lot.lotNumber} 생성 완료! 팔레트 ${count}개 자동 생성됨`);
    }

    setBarcodeCounter(barcodeCounter + 1);
    form.resetFields();
    handleProcessTypeChange('RAW');
  };

  // Register RFID
  const handleRegisterRfid = (rfidEpc: string) => {
    const { lotNumber, paletteId } = rfidModal;

    setLotData(lotData.map(lot => {
      if (lot.lotNumber === lotNumber) {
        const updatedPalettes = lot.palettes.map(p => {
          if (p.id === paletteId) {
            return {
              ...p,
              rfidEpc,
              status: 'Empty',
              rfidRegisteredAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
            };
          }
          return p;
        });

        return {
          ...lot,
          palettes: updatedPalettes,
          rfidRegistered: updatedPalettes.filter(p => p.rfidEpc).length,
        };
      }
      return lot;
    }));

    setRfidModal({ visible: false, lotNumber: '', paletteId: '' });
    message.success('RFID 등록 완료!');
  };

  // Open bulk RFID registration
  const handleOpenBulkRfid = () => {
    const items: BulkRfidItem[] = [];

    lotData.forEach(lot => {
      if (lot.palettes.length > 0) {
        lot.palettes.forEach(palette => {
          if (!palette.rfidEpc) {
            items.push({
              lotNumber: lot.lotNumber,
              itemCode: lot.itemCode,
              itemName: lot.itemName,
              paletteId: palette.id,
              paletteNumber: palette.paletteNumber,
              quantity: palette.quantity,
            });
          }
        });
      }
    });

    if (items.length === 0) {
      message.info('등록할 팔레트가 없습니다.');
      return;
    }

    setBulkRfidModal({ visible: true, items, currentIndex: 0 });
  };

  // Register next bulk RFID
  const handleBulkRfidNext = (rfidEpc: string) => {
    const { items, currentIndex } = bulkRfidModal;
    const currentItem = items[currentIndex];

    // Update item with RFID
    items[currentIndex].rfidEpc = rfidEpc;

    // Update lotData
    setLotData(lotData.map(lot => {
      if (lot.lotNumber === currentItem.lotNumber) {
        const updatedPalettes = lot.palettes.map(p => {
          if (p.id === currentItem.paletteId) {
            return {
              ...p,
              rfidEpc,
              status: 'Empty',
              rfidRegisteredAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
            };
          }
          return p;
        });

        return {
          ...lot,
          palettes: updatedPalettes,
          rfidRegistered: updatedPalettes.filter(p => p.rfidEpc).length,
        };
      }
      return lot;
    }));

    // Move to next item
    setBulkRfidModal({
      ...bulkRfidModal,
      currentIndex: currentIndex + 1,
    });
  };

  // Filtered data
  const filteredData = lotData.filter(lot => {
    const matchLotNumber = !filterLotNumber || lot.lotNumber.toLowerCase().includes(filterLotNumber.toLowerCase());
    const matchItemType = !filterItemType || lot.itemType === filterItemType;
    const matchItemCode = !filterItemCode || lot.itemCode.toLowerCase().includes(filterItemCode.toLowerCase());
    const matchDate = !filterDate || lot.productionDate === filterDate;
    return matchLotNumber && matchItemType && matchItemCode && matchDate;
  });

  const hasUnregisteredRfid = lotData.some(
    lot => lot.palettes.length > 0 && lot.rfidRegistered < lot.paletteCount
  );

  // Initialize form
  useEffect(() => {
    form.setFieldsValue({
      processType: 'RAW',
      lotNumber: generateLotNumber('RAW'),
      barcode: generateBarcode(),
      quantity: 500,
      paletteCapacity: 50,
      productionDate: dayjs(),
      supplier: '포스코',
      worker: '김철수',
      inputQuantity: 400,
    });
  }, []);

  // LOT table columns
  const lotColumns: ColumnsType<LotData> = [
    {
      title: 'LOT 번호',
      dataIndex: 'lotNumber',
      key: 'lotNumber',
      width: 150,
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: '품목 유형',
      dataIndex: 'itemType',
      key: 'itemType',
      width: 100,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          RAW: 'cyan',
          WIP: 'orange',
          PRODUCT: 'green',
        };
        const labelMap: Record<string, string> = {
          RAW: '원자재',
          WIP: '재공품',
          PRODUCT: '완제품',
        };
        return <Tag color={colorMap[type]}>{labelMap[type]}</Tag>;
      },
    },
    {
      title: '품목코드',
      dataIndex: 'itemCode',
      key: 'itemCode',
      width: 150,
    },
    {
      title: '수량',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      render: (qty: number) => `${qty}개`,
    },
    {
      title: '팔레트 수',
      dataIndex: 'paletteCount',
      key: 'paletteCount',
      width: 100,
      render: (count: number, record: LotData) =>
        record.itemType === 'RAW' ? '-' : `${count}개`,
    },
    {
      title: '생산/입고일',
      dataIndex: 'productionDate',
      key: 'productionDate',
      width: 120,
    },
    {
      title: 'RFID 상태',
      key: 'rfidStatus',
      width: 120,
      render: (_, record: LotData) => {
        if (record.itemType === 'RAW') return '-';
        if (record.rfidRegistered === record.paletteCount) {
          return <Tag color="success">완료</Tag>;
        }
        if (record.rfidRegistered > 0) {
          return <Tag color="warning">{record.rfidRegistered}/{record.paletteCount}</Tag>;
        }
        return <Tag color="error">미등록</Tag>;
      },
    },
  ];

  // Palette table columns
  const paletteColumns: ColumnsType<Palette> = [
    {
      title: '팔레트 ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string, record: Palette, index: number, lot?: LotData) => (
        <Button
          type="link"
          onClick={() => setPaletteDetailModal({ visible: true, lot: lot!, palette: record })}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '팔레트 번호',
      dataIndex: 'paletteNumber',
      key: 'paletteNumber',
      render: (num: number) => `#${num}`,
    },
    {
      title: '수량',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (qty: number) => `${qty}개`,
    },
    {
      title: 'RFID 상태',
      key: 'rfidStatus',
      render: (_, record: Palette) => (
        <Tag color={record.rfidEpc ? 'success' : 'default'}>
          {record.rfidEpc ? '등록완료' : '미등록'}
        </Tag>
      ),
    },
    {
      title: '작업',
      key: 'action',
      render: (_, record: Palette, index: number, lot?: LotData) =>
        !record.rfidEpc && (
          <Button
            size="small"
            type="primary"
            onClick={() => setRfidModal({
              visible: true,
              lotNumber: lot!.lotNumber,
              paletteId: record.id
            })}
          >
            RFID 등록
          </Button>
        ),
    },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>LOT - 팔레트 - RFID 통합 관리</h1>

      <Card title="LOT 생성 / 팔레트 - RFID 등록" style={{ marginBottom: 24 }}>
        <Alert
          message={
            processType === 'RAW'
              ? '원자재는 팔레트/RFID 추적이 필요 없습니다. LOT만 생성하여 추적성을 시작합니다.'
              : processType === '2'
              ? '샤링 공정: 재공품(WIP)을 생산합니다. 팔레트가 자동으로 분할되고 RFID 태그를 등록할 수 있습니다.'
              : processType === '3'
              ? '프레스 공정: 재공품(WIP)을 생산합니다. 팔레트가 자동으로 분할되고 RFID 태그를 등록할 수 있습니다.'
              : processType === '4'
              ? '조립 공정: 완제품(PRODUCT)을 생산합니다. 팔레트가 자동으로 분할되고 RFID 태그를 등록할 수 있습니다.'
              : '생산 LOT 생성 시 팔레트가 자동으로 분할되고, RFID 태그를 등록할 수 있습니다.'
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateLot}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                name="processType"
                label="공정"
                rules={[{ required: true }]}
              >
                <Select onChange={handleProcessTypeChange}>
                  <Option value="RAW">원자재</Option>
                  <Option value="2">샤링 (SH)</Option>
                  <Option value="3">프레스 (PR)</Option>
                  <Option value="4">조립 (AS)</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={6}>
              <Form.Item name="lotNumber" label="LOT 번호 (자동 생성)">
                <Input disabled style={{ backgroundColor: '#d4edda', fontWeight: 600 }} />
              </Form.Item>
            </Col>

            <Col span={6}>
              <Form.Item name="barcode" label="바코드 (자동 생성)">
                <Input disabled style={{ backgroundColor: '#d4edda', fontWeight: 600 }} />
              </Form.Item>
            </Col>

            <Col span={6}>
              <Form.Item name="quantity" label="수량" rules={[{ required: true }]}>
                <InputNumber
                  min={1}
                  style={{ width: '100%' }}
                  onChange={(val) => {
                    const capacity = form.getFieldValue('paletteCapacity') || 1;
                    calculatePaletteCount(val || 0, capacity);
                  }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            {processType === 'RAW' ? (
              <>
                <Col span={8}>
                  <Form.Item name="rawItemId" label="품목 (원자재)" rules={[{ required: true }]}>
                    <Select
                      placeholder="선택하세요"
                      showSearch
                      filterOption={(input, option) =>
                        (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                      }
                      onChange={(value) => {
                        // Auto-fill supplier when item is selected
                        const selectedItem = itemsData?.items.find(item => item.item_code === value);
                        if (selectedItem?.default_supplier) {
                          form.setFieldsValue({ supplier: [selectedItem.default_supplier] });
                        }
                      }}
                      options={getFilteredItems().map(item => ({
                        value: item.item_code,
                        label: `${item.item_code} - ${item.item_name}`,
                      }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="supplier" label="공급사" rules={[{ required: true }]}>
                    <Select
                      placeholder="선택 또는 입력하세요"
                      showSearch
                      mode="tags"
                      maxTagCount={1}
                      filterOption={(input, option) =>
                        (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                      }
                      options={getSupplierOptions()}
                    />
                  </Form.Item>
                </Col>
              </>
            ) : (
              <>
                <Col span={8}>
                  <Form.Item name="prodItemId" label="품목 (생산품)" rules={[{ required: true }]}>
                    <Select
                      placeholder="선택하세요"
                      showSearch
                      filterOption={(input, option) =>
                        (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                      }
                      options={getFilteredItems().map(item => ({
                        value: item.item_code,
                        label: `${item.item_code} - ${item.item_name}`,
                      }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item name="paletteCapacity" label="팔레트당 적재량" rules={[{ required: true }]}>
                    <InputNumber
                      min={1}
                      style={{ width: '100%' }}
                      onChange={(val) => {
                        const quantity = form.getFieldValue('quantity') || 0;
                        calculatePaletteCount(quantity, val || 1);
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item label="필요 팔레트 수">
                    <Input value={paletteCount} disabled style={{ backgroundColor: '#d4edda', fontWeight: 600 }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="worker" label="작업자" rules={[{ required: true }]}>
                    <Input placeholder="예: 김철수" />
                  </Form.Item>
                </Col>
              </>
            )}

            <Col span={8}>
              <Form.Item name="productionDate" label={processType === 'RAW' ? '입고일' : '생산일'} rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          {processType !== 'RAW' && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="inputLot" label="투입 원자재/중간품 LOT">
                  <Select placeholder="선택하세요">
                    {lotData.filter(l => l.quantity > 0).map(l => (
                      <Option key={l.lotNumber} value={l.lotNumber}>
                        {l.lotNumber} - {l.itemCode} ({l.quantity}개 재고)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="inputQuantity" label="투입 수량">
                  <InputNumber min={1} style={{ width: '100%' }} placeholder="투입할 수량" />
                </Form.Item>
              </Col>
            </Row>
          )}

          <Form.Item name="notes" label="비고">
            <TextArea rows={2} placeholder="추가 정보 입력" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button htmlType="submit" type="primary" icon={<PlusOutlined />}>
                {processType === 'RAW' ? '원자재 입고 등록' : '생산 LOT 생성'}
              </Button>
              <Button onClick={() => form.resetFields()}>취소</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>LOT 목록</h2>
        {hasUnregisteredRfid && (
          <Button type="primary" icon={<TagsOutlined />} onClick={handleOpenBulkRfid}>
            RFID 대량등록
          </Button>
        )}
      </div>

      {lotData.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Input
                placeholder="LOT 번호 검색"
                prefix={<SearchOutlined />}
                value={filterLotNumber}
                onChange={(e) => setFilterLotNumber(e.target.value)}
                allowClear
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="품목 유형"
                value={filterItemType}
                onChange={setFilterItemType}
                style={{ width: '100%' }}
                allowClear
              >
                <Option value="RAW">원자재</Option>
                <Option value="WIP">재공품</Option>
                <Option value="PRODUCT">완제품</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Input
                placeholder="품목코드 검색"
                value={filterItemCode}
                onChange={(e) => setFilterItemCode(e.target.value)}
                allowClear
              />
            </Col>
            <Col span={6}>
              <DatePicker
                placeholder="생산/입고일"
                onChange={(date) => setFilterDate(date ? date.format('YYYY-MM-DD') : '')}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      <Table
        dataSource={filteredData}
        columns={lotColumns}
        rowKey="lotNumber"
        expandable={{
          expandedRowKeys,
          onExpand: (expanded, record) => {
            setExpandedRowKeys(expanded
              ? [...expandedRowKeys, record.lotNumber]
              : expandedRowKeys.filter(key => key !== record.lotNumber)
            );
          },
          expandedRowRender: (record) => (
            <Table
              dataSource={record.palettes}
              columns={paletteColumns.map(col => ({
                ...col,
                render: col.render
                  ? (text: any, palette: Palette, index: number) =>
                      col.render!(text, palette, index, record)
                  : undefined,
              }))}
              rowKey="id"
              pagination={false}
              size="small"
            />
          ),
          rowExpandable: (record) => record.palettes.length > 0,
        }}
        pagination={{ pageSize: 10 }}
        locale={{
          emptyText: (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#6c757d' }}>
              <div style={{ fontSize: 48, marginBottom: 15 }}>📦</div>
              <h3>생성된 LOT이 없습니다</h3>
              <p>상단 양식을 작성하여 새 LOT을 생성하세요</p>
            </div>
          ),
        }}
      />

      {/* Palette Detail Modal */}
      <Modal
        title="팔레트 상세 정보"
        open={paletteDetailModal.visible}
        onCancel={() => setPaletteDetailModal({ visible: false, lot: null, palette: null })}
        footer={null}
        width={600}
      >
        {paletteDetailModal.palette && paletteDetailModal.lot && (
          <div>
            <h3>팔레트 기본 정보</h3>
            <div style={{ marginBottom: 16 }}>
              <div style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <strong>팔레트 ID:</strong> {paletteDetailModal.palette.id}
              </div>
              <div style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <strong>팔레트 번호:</strong> #{paletteDetailModal.palette.paletteNumber}
              </div>
              <div style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <strong>소속 LOT:</strong> {paletteDetailModal.lot.lotNumber}
              </div>
              <div style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <strong>수량:</strong> {paletteDetailModal.palette.quantity}개
              </div>
            </div>

            {paletteDetailModal.palette.rfidEpc ? (
              <Alert
                message="RFID 등록 완료"
                description={
                  <div>
                    <div><strong>RFID EPC:</strong> {paletteDetailModal.palette.rfidEpc}</div>
                    <div><strong>등록 일시:</strong> {paletteDetailModal.palette.rfidRegisteredAt}</div>
                  </div>
                }
                type="success"
                showIcon
              />
            ) : (
              <Alert
                message="RFID 매칭 필요"
                description="이 팔레트에 RFID가 등록되지 않았습니다."
                type="warning"
                showIcon
                action={
                  <Button
                    size="small"
                    type="primary"
                    onClick={() => {
                      setPaletteDetailModal({ visible: false, lot: null, palette: null });
                      setRfidModal({
                        visible: true,
                        lotNumber: paletteDetailModal.lot!.lotNumber,
                        paletteId: paletteDetailModal.palette!.id,
                      });
                    }}
                  >
                    RFID 등록
                  </Button>
                }
              />
            )}
          </div>
        )}
      </Modal>

      {/* RFID Registration Modal */}
      <Modal
        title="RFID 등록"
        open={rfidModal.visible}
        onCancel={() => setRfidModal({ visible: false, lotNumber: '', paletteId: '' })}
        footer={null}
      >
        <RfidRegistrationForm
          onSubmit={handleRegisterRfid}
          onCancel={() => setRfidModal({ visible: false, lotNumber: '', paletteId: '' })}
        />
      </Modal>

      {/* Bulk RFID Registration Modal */}
      <Modal
        title="RFID 대량등록"
        open={bulkRfidModal.visible}
        onCancel={() => setBulkRfidModal({ visible: false, items: [], currentIndex: 0 })}
        footer={null}
        width={800}
      >
        <BulkRfidRegistration
          items={bulkRfidModal.items}
          currentIndex={bulkRfidModal.currentIndex}
          onNext={handleBulkRfidNext}
          onSkip={() => setBulkRfidModal({ ...bulkRfidModal, currentIndex: bulkRfidModal.currentIndex + 1 })}
          onComplete={() => {
            setBulkRfidModal({ visible: false, items: [], currentIndex: 0 });
            message.success('모든 RFID 등록 완료!');
          }}
        />
      </Modal>
    </div>
  );
}

// RFID Registration Form Component
function RfidRegistrationForm({ onSubmit, onCancel }: { onSubmit: (rfid: string) => void; onCancel: () => void }) {
  const [rfid, setRfid] = useState('');
  const [scanning, setScanning] = useState(false);

  const handleScan = () => {
    setScanning(true);
    // Simulate RFID scan
    setTimeout(() => {
      const simulatedRfid = 'E280' + Math.random().toString(36).substr(2, 20).toUpperCase();
      setRfid(simulatedRfid);
      setScanning(false);
      message.success('RFID 스캔 완료!');
    }, 3000);
  };

  return (
    <div>
      <Input
        placeholder="RFID EPC 번호를 입력하거나 스캔하세요"
        value={rfid}
        onChange={(e) => setRfid(e.target.value)}
        disabled={scanning}
        style={{ marginBottom: 16 }}
      />

      {scanning && (
        <Alert
          message="RFID 스캔 대기 중..."
          description="RFID 리더기를 태그에 가까이 대주세요"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Space>
        <Button type="primary" onClick={() => onSubmit(rfid)} disabled={!rfid || scanning}>
          등록
        </Button>
        <Button onClick={handleScan} disabled={scanning}>
          스캔 모드
        </Button>
        <Button onClick={onCancel}>취소</Button>
      </Space>
    </div>
  );
}

// Bulk RFID Registration Component
function BulkRfidRegistration({
  items,
  currentIndex,
  onNext,
  onSkip,
  onComplete,
}: {
  items: BulkRfidItem[];
  currentIndex: number;
  onNext: (rfid: string) => void;
  onSkip: () => void;
  onComplete: () => void;
}) {
  const [rfid, setRfid] = useState('');

  const currentItem = items[currentIndex];
  const progress = (currentIndex / items.length) * 100;

  if (currentIndex >= items.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
        <Alert
          message="모든 RFID 등록 완료!"
          description={`${items.length}개의 팔레트에 RFID가 성공적으로 등록되었습니다.`}
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Button type="primary" onClick={onComplete}>닫기</Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h3>등록 진행 상황</h3>
        <div style={{ marginBottom: 8 }}>
          <span>진행률: {currentIndex} / {items.length} 완료</span>
          <span style={{ float: 'right', fontWeight: 'bold' }}>{Math.round(progress)}%</span>
        </div>
        <Progress percent={progress} status="active" />
      </div>

      {currentItem && (
        <Card
          title="현재 등록 대상"
          size="small"
          style={{ marginBottom: 16, backgroundColor: '#fff3cd' }}
        >
          <Row gutter={[16, 8]}>
            <Col span={12}><strong>LOT:</strong> {currentItem.lotNumber}</Col>
            <Col span={12}><strong>품목:</strong> {currentItem.itemName}</Col>
            <Col span={12}><strong>팔레트:</strong> {currentItem.paletteId}</Col>
            <Col span={12}><strong>수량:</strong> {currentItem.quantity}개</Col>
          </Row>
        </Card>
      )}

      <Input
        placeholder="RFID EPC 번호를 입력하거나 스캔하세요"
        value={rfid}
        onChange={(e) => setRfid(e.target.value)}
        onPressEnter={() => rfid && onNext(rfid)}
        autoFocus
        style={{ marginBottom: 16 }}
      />

      <Space>
        <Button
          type="primary"
          onClick={() => {
            onNext(rfid);
            setRfid('');
          }}
          disabled={!rfid}
        >
          등록 후 다음
        </Button>
        <Button onClick={onSkip}>건너뛰기</Button>
      </Space>

      <div style={{ marginTop: 24, maxHeight: 300, overflowY: 'auto' }}>
        <h4>미등록 팔레트 목록</h4>
        <Table
          dataSource={items}
          columns={[
            {
              title: '상태',
              key: 'status',
              width: 60,
              render: (_, record, index) =>
                index < currentIndex ? '✅' : index === currentIndex ? '⏳' : '⏸️',
            },
            { title: 'LOT', dataIndex: 'lotNumber', key: 'lot' },
            { title: '팔레트', dataIndex: 'paletteId', key: 'palette' },
            { title: '수량', dataIndex: 'quantity', key: 'quantity' },
            {
              title: 'RFID EPC',
              dataIndex: 'rfidEpc',
              key: 'rfid',
              render: (text: string) => text || '-',
            },
          ]}
          rowKey="paletteId"
          pagination={false}
          size="small"
        />
      </div>
    </div>
  );
}
