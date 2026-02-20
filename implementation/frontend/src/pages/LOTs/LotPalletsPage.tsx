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
    Progress,
    Descriptions,
} from 'antd';
import {
    PlusOutlined,
    TagsOutlined,
    SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { itemApi } from '../../api/items';
import { lotApi } from '../../api/lots';
import { palletApi } from '../../api/pallets';
import type { Item } from '../../types/item';
import type { Pallet } from '../../types/pallet';

const { Option } = Select;
const { TextArea } = Input;

interface Palette {
    id: string;
    paletteNumber: number;
    quantity: number;
    rfidEpc: string | null;
    status: string;
    rfidRegisteredAt?: string;
    rfidDeregisteredAt?: string;
}

interface LotData {
    lotNumber: string;
    itemCode: string;
    itemName: string;
    itemType: 'RAW' | 'WIP' | 'PRODUCT';
    quantity: number;
    initialQuantity: number;
    producedQuantity: number;
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
        queryFn: () => itemApi.getAll({ is_active: true, per_page: 100 }),
    });

    // Fetch lots from API
    const { data: lotsApiData, refetch: refetchLots } = useQuery({
        queryKey: ['lots'],
        queryFn: () => lotApi.getAll({ per_page: 100 }),
    });

    // Fetch pallets from API
    const { data: palletsApiData, refetch: refetchPallets } = useQuery({
        queryKey: ['pallets'],
        queryFn: () => palletApi.getAll({ per_page: 100 }),
    });

    // Transform API data to local format
    useEffect(() => {
        if (lotsApiData?.items && palletsApiData?.items) {
            console.log('🔍 Transforming LOT data...');
            console.log('Lots:', lotsApiData.items.length, 'Pallets:', palletsApiData.items.length);

            // Debug: Show sample lot IDs and pallet lot_ids
            if (lotsApiData.items.length > 0) {
                console.log('📋 Sample LOT IDs:', lotsApiData.items.slice(0, 3).map((l: any) => ({ id: l.id, lot_number: l.lot_number })));
            }
            if (palletsApiData.items.length > 0) {
                console.log('📦 Sample Pallet lot_ids:', palletsApiData.items.slice(0, 5).map((p: Pallet) => ({ pallet_no: p.pallet_no, lot_id: p.lot_id })));
            }

            const transformedLots: LotData[] = lotsApiData.items.map((lot: any) => {
                // Find pallets for this lot
                const lotPallets = palletsApiData.items.filter((p: Pallet) => {
                    const matches = p.lot_id === lot.id;
                    if (matches) {
                        console.log(`  ✅ Pallet ${p.pallet_no} matches LOT ${lot.lot_number} (lot_id: ${p.lot_id} === ${lot.id})`);
                    }
                    return matches;
                });

                if (lotPallets.length > 0) {
                    console.log(`LOT ${lot.lot_number} (ID: ${lot.id}) has ${lotPallets.length} pallets`);
                    console.log(`  Pallet details for LOT ${lot.lot_number}:`, lotPallets.map((p: Pallet) => ({
                        pallet_no: p.pallet_no,
                        quantity: p.quantity,
                        rfid_epc: p.rfid_epc,
                        status: p.status,
                        lot_id: p.lot_id
                    })));
                } else {
                    // Only log for non-RAW lots
                    if (lot.item?.item_type !== 'RAW') {
                        console.log(`⚠️ LOT ${lot.lot_number} (ID: ${lot.id}, Type: ${lot.item?.item_type}) has 0 pallets`);
                    }
                }

                // Sort pallets by pallet_no or id for consistent ordering
                lotPallets.sort((a, b) => (a.pallet_no || '').localeCompare(b.pallet_no || ''));

                const palettes: Palette[] = lotPallets.map((p: Pallet, index: number) => ({
                    id: p.pallet_no,
                    paletteNumber: index + 1,
                    quantity: p.quantity || 0,
                    rfidEpc: p.rfid_epc || null,
                    status: p.status || 'Generated',
                    rfidRegisteredAt: p.tag_registered_at,
                    rfidDeregisteredAt: p.tag_deregistered_at,
                }));

                return {
                    lotNumber: lot.lot_number,
                    itemCode: lot.item?.item_code || '',
                    itemName: lot.item?.item_name || '',
                    itemType: lot.item?.item_type || 'RAW',
                    quantity: lot.quantity,
                    initialQuantity: lot.initial_quantity,
                    producedQuantity: lot.produced_quantity || 0,
                    status: lot.status,
                    productionDate: lot.production_date,
                    barcode: lot.barcode || lot.lot_number,
                    palettes,
                    paletteCount: palettes.length,
                    rfidRegistered: palettes.filter(p => p.rfidEpc).length,
                    processName: lot.process_name,
                    workerName: lot.worker_name,
                    supplier: lot.supplier,
                    notes: lot.notes,
                };
            });

            console.log('✅ Transformed lots:', transformedLots);
            console.log('📊 Summary:', {
                totalLots: transformedLots.length,
                lotsWithPallets: transformedLots.filter(l => l.paletteCount > 0).length,
                totalPallets: transformedLots.reduce((sum, l) => sum + l.paletteCount, 0)
            });
            setLotData(transformedLots);
        }
    }, [lotsApiData, palletsApiData]);


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
    const [pageSize, setPageSize] = useState<number>(10);

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

    // Get available input lots based on current process type
    const getAvailableInputLots = () => {
        if (!lotsApiData?.items) return [];

        // Filter mapping: process type -> required item type and process
        const inputLotFilters: Record<string, (lot: any) => boolean> = {
            '2': (lot) => lot.item?.item_type === 'RAW' && lot.quantity > 0, // 샤링: 원자재만
            '3': (lot) => lot.item?.item_type === 'WIP' && lot.process_id === 2 && lot.quantity > 0, // 프레스: 샤링 공정 WIP만
            '4': (lot) => lot.item?.item_type === 'WIP' && lot.process_id === 3 && lot.quantity > 0, // 조립: 프레스 공정 WIP만
        };

        const filterFn = inputLotFilters[processType];
        if (!filterFn) return [];

        return lotsApiData.items.filter(filterFn);
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

    // Handle process type change
    const handleProcessTypeChange = (value: string) => {
        setProcessType(value);

        if (value === 'RAW') {
            setPaletteCount(0);
        } else {
            const quantity = form.getFieldValue('quantity') || 0;
            const capacity = form.getFieldValue('paletteCapacity') || 1;
            calculatePaletteCount(quantity, capacity);
        }
    };

    // Create LOT
    const handleCreateLot = async (values: any) => {
        const isRaw = processType === 'RAW';

        try {
            if (isRaw) {
                // Create raw material LOT via API
                const selectedItem = itemsData?.items.find(item => item.item_code === values.rawItemId);

                if (!selectedItem) {
                    throw new Error('품목을 선택해주세요');
                }

                const createdLot = await lotApi.receiving({
                    item_id: selectedItem.id,
                    quantity: values.quantity,
                    production_date: values.productionDate.format('YYYY-MM-DD'),
                    supplier: Array.isArray(values.supplier) ? values.supplier[0] : values.supplier,
                    notes: values.notes,
                });

                console.log('✅ Raw material LOT created:', createdLot);

                // Refresh LOT data
                await refetchLots();

                message.success(`원자재 LOT ${createdLot.lot_number} 등록 완료!`);
            } else {
                // Create production LOT via API
                const selectedItem = itemsData?.items.find(item => item.item_code === values.prodItemId);

                if (!selectedItem) {
                    throw new Error('품목을 선택해주세요');
                }

                const processIdMap: Record<string, number> = {
                    '2': 2, // SHEARING
                    '3': 3, // PRESS
                    '4': 4, // ASSEMBLY
                };

                const requestData = {
                    item_id: selectedItem.id,
                    process_id: processIdMap[processType],
                    quantity: values.quantity,
                    production_date: values.productionDate.format('YYYY-MM-DD'),
                    worker_name: values.worker,
                    notes: values.notes,
                    palette_capacity: values.paletteCapacity,
                    qc_passed: false,
                    input_lots: values.inputLot ? [{
                        lot_id: parseInt(values.inputLot),
                        quantity_consumed: values.inputQuantity || 0,
                    }] : undefined,
                };

                console.log('🚀 Creating LOT with data:', requestData);

                const createdLot = await lotApi.create(requestData);

                console.log('✅ LOT created:', createdLot);

                // Wait a bit for the database transaction to complete and pallets to be created
                // This ensures the pallets are committed before we refetch
                await new Promise(resolve => setTimeout(resolve, 500));

                // Refresh data - wait for both to complete
                console.log('🔄 Refreshing LOT and pallet data...');
                await Promise.all([refetchLots(), refetchPallets()]);

                console.log('✅ Data refresh complete');

                message.success(`생산 LOT ${createdLot.lot_number} 생성 완료! 팔레트 ${Math.ceil(values.quantity / values.paletteCapacity)}개 생성됨`);
            }

            // Reset form and restore initial values
            form.resetFields();
            initializeFormValues();
            handleProcessTypeChange('RAW');
        } catch (error: any) {
            console.error('❌ LOT 생성 오류:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'LOT 생성 중 오류가 발생했습니다.';
            message.error(errorMessage);
        }
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

    // Initialize form with default values
    const initializeFormValues = () => {
        form.setFieldsValue({
            processType: 'RAW',
            quantity: 500,
            paletteCapacity: 50,
            productionDate: dayjs(),
            supplier: '포스코',
            worker: '김철수',
            inputQuantity: 400,
        });
    };

    useEffect(() => {
        initializeFormValues();
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
            title: '수량 (누적/현재/목표)',
            dataIndex: 'quantity',
            key: 'quantity',
            width: 140,
            render: (qty: number, record: LotData) => (
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.85em', color: '#666' }}>현재수량:</span>
                        <Tag color={qty > 0 ? "green" : "default"} style={{ margin: 0 }}>{qty}</Tag>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.85em', color: '#666' }}>누적생산:</span>
                        <Tag color="blue" style={{ margin: 0 }}>{record.producedQuantity}</Tag>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.85em', color: '#666' }}>목표수량:</span>
                        <Tag color="default" style={{ margin: 0 }}>{record.initialQuantity}</Tag>
                    </div>
                </Space>
            ),
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

    // Palette table columns generator
    const getPaletteColumns = (lot: LotData): ColumnsType<Palette> => [
        {
            title: '팔레트 번호',
            dataIndex: 'paletteNumber',
            key: 'paletteNumber',
            render: (num: number) => `#${num}`,
        },
        {
            title: '팔레트 ID',
            dataIndex: 'id',
            key: 'id',
            render: (text: string, record: Palette) => (
                <Button
                    type="link"
                    onClick={() => setPaletteDetailModal({ visible: true, lot, palette: record })}
                >
                    {text}
                </Button>
            ),
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
            render: (_, record: Palette) =>
                record.rfidEpc ? (
                    <Tag color="success">등록완료</Tag>
                ) : (
                    <Button
                        size="small"
                        type="primary"
                        onClick={() => setRfidModal({
                            visible: true,
                            lotNumber: lot.lotNumber,
                            paletteId: record.id
                        })}
                    >
                        RFID 등록
                    </Button>
                ),
        },
        {
            title: '태그 등록 시각',
            dataIndex: 'rfidRegisteredAt',
            key: 'rfidRegisteredAt',
            render: (value: string) => value || '-',
        },
        {
            title: '태그 해제 시각',
            dataIndex: 'rfidDeregisteredAt',
            key: 'rfidDeregisteredAt',
            render: (value: string) => value || '-',
        },
        {
            title: '팔레트 상태',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                const statusMap: Record<string, { color: string; label: string }> = {
                    Generated: { color: 'default', label: '생성됨' },
                    Empty: { color: 'default', label: '비어있음' },
                    Stock: { color: 'blue', label: '재고' },
                    Consuming: { color: 'orange', label: '소비중' },
                    Producing: { color: 'purple', label: '생산중' },
                    Finished: { color: 'green', label: '완료' },
                    Deregistered: { color: 'default', label: '해제됨' },
                    Hold: { color: 'gold', label: '보류' },
                    Defect: { color: 'red', label: '불량' },
                };
                const info = statusMap[status] || { color: 'default', label: status };
                return <Tag color={info.color}>{info.label}</Tag>;
            },
        },
        {
            title: '상세 정보',
            key: 'detail',
            render: (_, record: Palette) => (
                <Button
                    size="small"
                    onClick={() => setPaletteDetailModal({ visible: true, lot, palette: record })}
                >
                    상세 정보
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
                                ? '샤링 공정: 원자재(RAW)를 투입하여 재공품(WIP)을 생산합니다. 투입 LOT는 선택 사항이며, 팔레트가 자동으로 분할됩니다.'
                                : processType === '3'
                                    ? '프레스 공정: 샤링품(WIP)을 투입하여 재공품(WIP)을 생산합니다. 투입 LOT는 선택 사항이며, 팔레트가 자동으로 분할됩니다.'
                                    : processType === '4'
                                        ? '조립 공정: 프레스품(WIP)을 투입하여 완제품(PRODUCT)을 생산합니다. 투입 LOT는 선택 사항이며, 팔레트가 자동으로 분할됩니다.'
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

                        <Col span={6}>
                            <Form.Item name="productionDate" label={processType === 'RAW' ? '입고일' : '생산일'} rules={[{ required: true }]}>
                                <DatePicker style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>

                        {processType !== 'RAW' && (
                            <Col span={6}>
                                <Form.Item name="worker" label="작업자" rules={[{ required: true }]}>
                                    <Input placeholder="예: 김철수" />
                                </Form.Item>
                            </Col>
                        )}
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
                            </>
                        )}
                    </Row>

                    {processType !== 'RAW' && (
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    name="inputLot"
                                    label={
                                        processType === '2' ? '투입 원자재 LOT' :
                                            processType === '3' ? '투입 샤링품 LOT' :
                                                processType === '4' ? '투입 프레스품 LOT' :
                                                    '투입 LOT'
                                    }
                                >
                                    <Select
                                        placeholder={
                                            processType === '2' ? '원자재 LOT를 선택하세요' :
                                                processType === '3' ? '샤링품 LOT를 선택하세요' :
                                                    processType === '4' ? '프레스품 LOT를 선택하세요' :
                                                        '선택하세요'
                                        }
                                        allowClear
                                        showSearch
                                        filterOption={(input, option) =>
                                            (option?.children?.toString() || '').toLowerCase().includes(input.toLowerCase())
                                        }
                                        onChange={(lotId) => {
                                            if (lotId) {
                                                const selectedLot = getAvailableInputLots().find((lot: any) => lot.id === lotId);
                                                if (selectedLot) {
                                                    form.setFieldsValue({ inputQuantity: selectedLot.quantity });
                                                }
                                            } else {
                                                form.setFieldsValue({ inputQuantity: undefined });
                                            }
                                        }}
                                    >
                                        {getAvailableInputLots().map((lot: any) => (
                                            <Option key={lot.id} value={lot.id}>
                                                {lot.lot_number} - {lot.item?.item_code} ({lot.quantity}개 재고)
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
                            <Button onClick={() => { form.resetFields(); initializeFormValues(); }}>취소</Button>
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
                            columns={getPaletteColumns(record)}
                            rowKey="id"
                            pagination={false}
                            size="small"
                        />
                    ),
                    rowExpandable: (record) => record.palettes.length > 0,
                }}
                pagination={{
                    pageSize,
                    showSizeChanger: true,
                    pageSizeOptions: ['10', '20', '50', '100'],
                    onShowSizeChange: (_, size) => setPageSize(size),
                }}
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
                        <Descriptions column={1} bordered size="small">
                            <Descriptions.Item label="팔레트 ID">{paletteDetailModal.palette.id}</Descriptions.Item>
                            <Descriptions.Item label="팔레트 번호">#{paletteDetailModal.palette.paletteNumber}</Descriptions.Item>
                            <Descriptions.Item label="소속 LOT">{paletteDetailModal.lot.lotNumber}</Descriptions.Item>
                            <Descriptions.Item label="수량">{paletteDetailModal.palette.quantity}개</Descriptions.Item>
                            <Descriptions.Item label="팔레트 상태">
                                {(() => {
                                    const statusMap: Record<string, { color: string; label: string }> = {
                                        Generated: { color: 'default', label: '생성됨' },
                                        Empty: { color: 'default', label: '비어있음' },
                                        Stock: { color: 'blue', label: '재고' },
                                        Consuming: { color: 'orange', label: '소비중' },
                                        Producing: { color: 'purple', label: '생산중' },
                                        Finished: { color: 'green', label: '완료' },
                                        Deregistered: { color: 'default', label: '해제됨' },
                                        Hold: { color: 'gold', label: '보류' },
                                        Defect: { color: 'red', label: '불량' },
                                    };
                                    const info = statusMap[paletteDetailModal.palette.status] || { color: 'default', label: paletteDetailModal.palette.status };
                                    return <Tag color={info.color}>{info.label}</Tag>;
                                })()}
                            </Descriptions.Item>
                        </Descriptions>

                        <Descriptions title="RFID 정보" column={1} bordered size="small" style={{ marginTop: 16 }}>
                            <Descriptions.Item label="RFID 상태">
                                {paletteDetailModal.palette.rfidEpc ? (
                                    <Tag color="success">등록완료</Tag>
                                ) : (
                                    <Tag color="default">미등록</Tag>
                                )}
                            </Descriptions.Item>
                            {paletteDetailModal.palette.rfidEpc && (
                                <>
                                    <Descriptions.Item label="RFID EPC">{paletteDetailModal.palette.rfidEpc}</Descriptions.Item>
                                    <Descriptions.Item label="태그 등록 시각">{paletteDetailModal.palette.rfidRegisteredAt || '-'}</Descriptions.Item>
                                    <Descriptions.Item label="태그 해제 시각">{paletteDetailModal.palette.rfidDeregisteredAt || '-'}</Descriptions.Item>
                                </>
                            )}
                        </Descriptions>

                        {!paletteDetailModal.palette.rfidEpc && (
                            <Alert
                                message="RFID 매칭 필요"
                                description="이 팔레트에 RFID가 등록되지 않았습니다."
                                type="warning"
                                showIcon
                                style={{ marginTop: 16 }}
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
                            render: (_, __, index) =>
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
