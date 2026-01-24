import { useEffect } from 'react';
import { Card, Table, Tag, Badge, Button, Statistic, Row, Col } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useQuery } from '@tanstack/react-query';
import { palletApi } from '../../api/pallets';
import type { FIFOQueueItem } from '../../types/pallet';
import dayjs from 'dayjs';

export function FIFOMonitoringPage() {
  const { isConnected, on, off } = useWebSocket();
  const { data, refetch } = useQuery({
    queryKey: ['fifo-queue'],
    queryFn: () => palletApi.getFIFOQueue(),
    refetchInterval: 10000, // 10초마다 자동 갱신
  });

  useEffect(() => {
    const handleFIFOScan = (event: any) => {
      // FIFO 스캔 이벤트 수신 시 즉시 갱신
      console.log('FIFO scan event received:', event);
      refetch();
    };

    const handlePalletUpdated = () => {
      // 팔레트 업데이트 이벤트 수신 시 갱신
      refetch();
    };

    on('fifo_scan', handleFIFOScan);
    on('pallet_updated', handlePalletUpdated);

    return () => {
      off('fifo_scan', handleFIFOScan);
      off('pallet_updated', handlePalletUpdated);
    };
  }, [on, off, refetch]);

  const items = data?.items || [];
  const stats = {
    waiting: items.filter(i => i.scan_status === 'WAITING').length,
    ok: items.filter(i => i.scan_status === 'OK').length,
    violation: items.filter(i => i.scan_status === 'VIOLATION').length,
  };

  const getRowClassName = (record: FIFOQueueItem) => {
    switch (record.scan_status) {
      case 'OK':
        return 'fifo-row-ok';
      case 'VIOLATION':
        return 'fifo-row-violation';
      default:
        return 'fifo-row-waiting';
    }
  };

  const columns = [
    {
      title: '순서',
      dataIndex: 'queue_position',
      key: 'queue_position',
      width: 80,
      render: (pos: number) => <strong>#{pos}</strong>,
    },
    {
      title: '팔레트 번호',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
      width: 150,
    },
    {
      title: 'LOT 번호',
      dataIndex: 'lot_no',
      key: 'lot_no',
      render: (text: string) => text || '-',
    },
    {
      title: '품목 코드',
      dataIndex: 'item_code',
      key: 'item_code',
      render: (text: string) => text || '-',
    },
    {
      title: '품목명',
      dataIndex: 'item_name',
      key: 'item_name',
      render: (text: string) => text || '-',
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '스캔 상태',
      dataIndex: 'scan_status',
      key: 'scan_status',
      width: 120,
      render: (status: string) => {
        const config = {
          WAITING: { color: 'default', text: '대기 중' },
          OK: { color: 'success', text: '정상' },
          VIOLATION: { color: 'error', text: '순서 위반' },
        };
        const { color, text } = config[status as keyof typeof config];
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '스캔 시간',
      dataIndex: 'scan_time',
      key: 'scan_time',
      width: 180,
      render: (date?: string) =>
        date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>FIFO 모니터링</h1>
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

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="대기 중"
              value={stats.waiting}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="정상 스캔"
              value={stats.ok}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="순서 위반"
              value={stats.violation}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={`FIFO 대기열 (총 ${data?.total || 0}개)`}>
        <Table
          dataSource={items}
          columns={columns}
          rowKey="pallet_id"
          rowClassName={getRowClassName}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>

      <style>{`
        .fifo-row-waiting {
          background-color: #fafafa;
        }
        .fifo-row-ok {
          background-color: #f6ffed;
        }
        .fifo-row-violation {
          background-color: #fff1f0;
        }
      `}</style>
    </div>
  );
}
