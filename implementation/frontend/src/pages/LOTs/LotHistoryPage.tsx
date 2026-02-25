

import React, { useState } from 'react';
import {
    Table,
    Tag,
    Space,
    Input,
    Card,
    Typography,
    Breadcrumb,
    Button,
    Tooltip,
    Tabs,
} from 'antd';
import {
    HistoryOutlined,
    SearchOutlined,
    ReloadOutlined,
    ArrowRightOutlined,
    InfoCircleOutlined,
    DatabaseOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useQuery } from '@tanstack/react-query';
import { genealogyApi, type LotGenealogyWithDetails, type LotGenealogyRaw } from '../../api/genealogy';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export function LotHistoryPage() {
    const [searchText, setSearchText] = useState('');
    const [activeTab, setActiveTab] = useState('detailed');

    const { data: historyData, isLoading: isHistoryLoading, refetch: refetchHistory } = useQuery({
        queryKey: ['lot-genealogy-history'],
        queryFn: () => genealogyApi.getHistory(),
    });

    const { data: rawData, isLoading: isRawLoading, refetch: refetchRaw } = useQuery({
        queryKey: ['lot-genealogy-all'],
        queryFn: () => genealogyApi.getAll(),
        enabled: activeTab === 'raw',
    });

    const handleRefresh = () => {
        if (activeTab === 'detailed') refetchHistory();
        else refetchRaw();
    };

    const filteredDetailedData = historyData?.filter((item: LotGenealogyWithDetails) =>
        item.input_lot_number.toLowerCase().includes(searchText.toLowerCase()) ||
        item.output_lot_number.toLowerCase().includes(searchText.toLowerCase()) ||
        item.input_item_code.toLowerCase().includes(searchText.toLowerCase()) ||
        item.output_item_code.toLowerCase().includes(searchText.toLowerCase())
    );

    const filteredRawData = rawData?.filter((item: LotGenealogyRaw) =>
        String(item.input_lot_id).includes(searchText) ||
        String(item.output_lot_id).includes(searchText) ||
        String(item.id).includes(searchText)
    );

    // [Debug] Genealogy data logging
    React.useEffect(() => {
        if (historyData) {
            console.log('--- Lot Genealogy Detailed History ---');
            console.table(historyData);
        }
        if (rawData) {
            console.log('--- Lot Genealogy Raw Data (All) ---');
            console.table(rawData);
        }
    }, [historyData, rawData]);

    const getItemTypeColor = (type: string) => {
        switch (type) {
            case 'RAW': return 'cyan';
            case 'WIP': return 'orange';
            case 'PRODUCT': return 'green';
            default: return 'default';
        }
    };

    const getItemTypeLabel = (type: string) => {
        switch (type) {
            case 'RAW': return '원자재';
            case 'WIP': return '재공품';
            case 'PRODUCT': return '완제품';
            default: return type;
        }
    };

    const detailedColumns: ColumnsType<LotGenealogyWithDetails> = [
        {
            title: '일시',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180,
            render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
            sorter: (a: LotGenealogyWithDetails, b: LotGenealogyWithDetails) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
        },
        {
            title: '투입 (Parent)',
            key: 'input',
            render: (_: unknown, record: LotGenealogyWithDetails) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{record.input_lot_number || 'N/A'}</Text>
                    <Space>
                        <Tag color={getItemTypeColor(record.input_item_type)}>
                            {getItemTypeLabel(record.input_item_type)}
                        </Tag>
                        <Text type="secondary" size="small">{record.input_item_code || '-'}</Text>
                    </Space>
                </Space>
            ),
        },
        {
            title: '',
            key: 'arrow',
            width: 50,
            align: 'center',
            render: () => <ArrowRightOutlined style={{ color: '#bfbfbf' }} />,
        },
        {
            title: '생산 (Child)',
            key: 'output',
            render: (_: unknown, record: LotGenealogyWithDetails) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{record.output_lot_number || 'N/A'}</Text>
                    <Space>
                        <Tag color={getItemTypeColor(record.output_item_type)}>
                            {getItemTypeLabel(record.output_item_type)}
                        </Tag>
                        <Text type="secondary" size="small">{record.output_item_code || '-'}</Text>
                    </Space>
                </Space>
            ),
        },
        {
            title: '공정',
            dataIndex: 'process_name',
            key: 'process_name',
            width: 150,
            render: (name: string) => <Tag color="blue">{name || 'N/A'}</Tag>,
        },
        {
            title: '수량(소비/생산)',
            key: 'quantity',
            width: 120,
            align: 'right',
            render: (_: unknown, record: LotGenealogyWithDetails) => (
                <Space direction="vertical" size={0} style={{ width: '100%', alignItems: 'flex-end' }}>
                    <Text type="secondary" style={{ fontSize: '0.85em' }}>소비: {(record.quantity_consumed || 0).toLocaleString()}</Text>
                    <Text strong style={{ color: '#52c41a' }}>생산: {(record.quantity_produced || 0).toLocaleString()}</Text>
                </Space>
            ),
        },
        {
            title: '상세',
            key: 'action',
            width: 80,
            render: (_: unknown, record: LotGenealogyWithDetails) => (
                <Tooltip title="추적성 페이지에서 상세 확인">
                    <Button
                        type="text"
                        icon={<InfoCircleOutlined />}
                        href={`/traceability?lot=${record.output_lot_number}`}
                    />
                </Tooltip>
            ),
        },
    ];

    const rawColumns: ColumnsType<LotGenealogyRaw> = [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
        { title: 'Parent LOT ID', dataIndex: 'input_lot_id', key: 'input_lot_id' },
        { title: 'Child LOT ID', dataIndex: 'output_lot_id', key: 'output_lot_id' },
        { title: 'Process ID', dataIndex: 'process_id', key: 'process_id' },
        { title: 'Qty Consumed', dataIndex: 'quantity_consumed', key: 'quantity_consumed', align: 'right' },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')
        },
    ];

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                    <Breadcrumb items={[
                        { title: 'LOT 관리' },
                        { title: 'LOT 이력' },
                    ]} />
                    <Title level={2} style={{ margin: '8px 0 0 0' }}>
                        <HistoryOutlined style={{ marginRight: 12 }} />
                        LOT 생산 이력 (Genealogy)
                    </Title>
                </div>
                <Space>
                    <Input
                        placeholder="검색어 입력..."
                        prefix={<SearchOutlined />}
                        style={{ width: 300 }}
                        value={searchText}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchText(e.target.value)}
                        allowClear
                    />
                    <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
                        새로고침
                    </Button>
                </Space>
            </div>

            <Card styles={{ body: { padding: '0 24px 24px 24px' } }}>
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={[
                        {
                            key: 'detailed',
                            label: <span><HistoryOutlined />Detailed Info</span>,
                            children: (
                                <Table
                                    columns={detailedColumns}
                                    dataSource={filteredDetailedData}
                                    rowKey="id"
                                    loading={isHistoryLoading}
                                    pagination={{
                                        showSizeChanger: true,
                                        defaultPageSize: 20,
                                        showTotal: (total: number) => `총 ${total}건`,
                                    }}
                                    locale={{ emptyText: '공정 이력이 없습니다.' }}
                                />
                            )
                        },
                        {
                            key: 'raw',
                            label: <span><DatabaseOutlined />Raw Data (Debug)</span>,
                            children: (
                                <Table
                                    columns={rawColumns}
                                    dataSource={filteredRawData}
                                    rowKey="id"
                                    loading={isRawLoading}
                                    pagination={{
                                        showSizeChanger: true,
                                        defaultPageSize: 20,
                                        showTotal: (total: number) => `총 ${total}건`,
                                    }}
                                    locale={{ emptyText: '원본 데이터가 없습니다.' }}
                                />
                            )
                        }
                    ]}
                />
            </Card>

            <div style={{ marginTop: 24 }}>
                <Card size="small" style={{ backgroundColor: '#f0f2f5', border: 'none' }}>
                    <Space>
                        <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        <Text type="secondary">
                            LOT 이력은 각 공정에서 투입된 LOT와 생산된 LOT의 연결 관계를 보여줍니다.
                            상세한 전후방 추적은 [추적성] 메뉴를 이용해주세요.
                        </Text>
                    </Space>
                </Card>
            </div>
        </div>
    );
}
