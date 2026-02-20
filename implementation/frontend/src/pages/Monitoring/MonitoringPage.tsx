import { useEffect, useState } from 'react';
import { Card, Table, Tag, Tabs, Badge, Statistic, Row, Col, Button, Alert } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import { usePallets } from '../../hooks/usePallets';
import { useQuery } from '@tanstack/react-query';
import { processApi } from '../../api/processes';
import type { Pallet } from '../../types/pallet';
import dayjs from 'dayjs';

interface ScanEvent {
  id: string;
  timestamp: string;
  pallet_no: string;
  event_type: string;
  process_name?: string;
  location_type?: string;
  status?: string;
  description: string;
}

export function MonitoringPage() {
  const { isConnected, on, off } = useWebSocket();
  const { data: allPallets = [], refetch, error: palletsError } = usePallets();
  const { data: processes = [], error: processesError } = useQuery({
    queryKey: ['processes'],
    queryFn: () => processApi.getAll(),
    retry: 1,
  });
  const [recentEvents, setRecentEvents] = useState<ScanEvent[]>([]);
  const [selectedProcessId, setSelectedProcessId] = useState<number | 'all'>('all');

  useEffect(() => {
    const handlePalletUpdate = () => {
      refetch();
    };

    const handleScanEvent = (event: any) => {
      const newEvent: ScanEvent = {
        id: `${event.pallet_no}-${event.timestamp || Date.now()}`,
        timestamp: event.timestamp || new Date().toISOString(),
        pallet_no: event.pallet_no,
        event_type: event.event_type || 'scan',
        process_name: event.process_name,
        location_type: event.location_type,
        status: event.status,
        description: event.description || `${event.pallet_no} 스캔됨`,
      };
      setRecentEvents((prev) => [newEvent, ...prev].slice(0, 50));
    };

    on('pallet_updated', handlePalletUpdate);
    on('scan_event', handleScanEvent);
    on('pallet_status_changed', handleScanEvent);

    return () => {
      off('pallet_updated', handlePalletUpdate);
      off('scan_event', handleScanEvent);
      off('pallet_status_changed', handleScanEvent);
    };
  }, [on, off, refetch]);

  const filteredPallets = selectedProcessId === 'all'
    ? allPallets
    : allPallets.filter(p => p.current_process_id === selectedProcessId);

  const statusCounts = {
    consuming: filteredPallets.filter(p => p.status === 'Consuming').length,
    producing: filteredPallets.filter(p => p.status === 'Producing').length,
    stock: filteredPallets.filter(p => p.status === 'Stock').length,
    finished: filteredPallets.filter(p => p.status === 'Finished').length,
  };

  const statusColorMap: Record<string, string> = {
    Generated: 'default',
    Empty: 'default',
    Stock: 'green',
    Consuming: 'orange',
    Producing: 'blue',
    Finished: 'purple',
    Deregistered: 'default',
    Hold: 'gold',
    Defect: 'red',
  };

  const palletColumns = [
    {
      title: '팔레트',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
      width: 130,
    },
    {
      title: 'LOT',
      dataIndex: ['lot', 'lot_no'],
      key: 'lot_no',
      render: (_: any, record: Pallet) => record.lot?.lot_no || '-',
    },
    {
      title: '품번',
      dataIndex: ['lot', 'part', 'part_number'],
      key: 'part_number',
      render: (_: any, record: Pallet) => record.lot?.part?.part_number || '-',
    },
    {
      title: '품명',
      dataIndex: ['lot', 'part', 'part_name'],
      key: 'part_name',
      render: (_: any, record: Pallet) => record.lot?.part?.part_name || '-',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => (
        <Tag color={statusColorMap[status] || 'default'}>{status}</Tag>
      ),
    },
    {
      title: '업데이트',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 100,
      render: (date: string) => dayjs(date).format('HH:mm:ss'),
    },
  ];

  const eventColumns = [
    {
      title: '시간',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 100,
      render: (date: string) => dayjs(date).format('HH:mm:ss'),
    },
    {
      title: '팔레트',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
      width: 120,
    },
    {
      title: '공정',
      dataIndex: 'process_name',
      key: 'process_name',
      render: (text: string) => text || '-',
    },
    {
      title: '위치',
      dataIndex: 'location_type',
      key: 'location_type',
      render: (text: string) => text || '-',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => status ? (
        <Tag color={statusColorMap[status] || 'default'}>{status}</Tag>
      ) : '-',
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
    },
  ];

  const processTabsItems = [
    {
      key: 'all',
      label: `전체 (${allPallets.length})`,
    },
    ...processes.map(process => ({
      key: String(process.id),
      label: `${process.process_name} (${allPallets.filter(p => p.current_process_id === process.id).length})`,
    })),
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>실시간 공정 모니터링</h1>
        <div>
          <Badge
            status={isConnected ? 'success' : 'error'}
            text={isConnected ? '실시간 연결됨' : '연결 끊김'}
            style={{ marginRight: 16 }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            새로고침
          </Button>
        </div>
      </div>

      {(palletsError || processesError) && (
        <Alert
          message="데이터 로드 오류"
          description="API 서버가 실행 중인지 확인해주세요. (http://localhost:8000)"
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Tabs
          activeKey={String(selectedProcessId)}
          onChange={(key) => setSelectedProcessId(key === 'all' ? 'all' : Number(key))}
          items={processTabsItems}
        />

        <Row gutter={16} style={{ marginTop: 16, marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="투입 대기"
                value={statusCounts.consuming}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="생산 중"
                value={statusCounts.producing}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="재고"
                value={statusCounts.stock}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="완료"
                value={statusCounts.finished}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <h3>팔레트 목록</h3>
        <Table
          dataSource={Array.isArray(filteredPallets) ? filteredPallets : []}
          columns={palletColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      <Card title={`최근 이벤트 (${recentEvents.length})`}>
        <Table
          dataSource={Array.isArray(recentEvents) ? recentEvents : []}
          columns={eventColumns}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  );
}
