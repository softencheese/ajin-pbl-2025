import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert } from 'antd';
import {
  InboxOutlined,
  CheckCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useDashboardStats, useProcessStatus, useRecentActivities } from '../../hooks/useDashboard';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: processStatus, isLoading: processLoading } = useProcessStatus();
  const { data: recentActivities, isLoading: activityLoading } = useRecentActivities();

  // 클릭 가능한 카드 스타일
  const clickableCardStyle = {
    cursor: 'pointer',
    transition: 'box-shadow 0.3s',
  };

  if (statsError) {
    return (
      <div>
        <h1 style={{ marginBottom: 24 }}>대시보드</h1>
        <Alert
          message="API 서버 연결 오류"
          description="대시보드 데이터를 불러올 수 없습니다. API 서버(http://localhost:8000)가 실행 중인지 확인해주세요."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Alert
          message="개발 환경 안내"
          description="현재 프론트엔드만 실행 중입니다. 전체 기능을 사용하려면 백엔드 API 서버를 먼저 시작해주세요."
          type="info"
          showIcon
        />
      </div>
    );
  }

  const activityColumns = [
    {
      title: '시간',
      dataIndex: 'scan_time',
      key: 'scan_time',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
      width: 180,
    },
    {
      title: '팔레트',
      dataIndex: 'pallet_no',
      key: 'pallet_no',
    },
    {
      title: '이벤트',
      dataIndex: 'event_type',
      key: 'event_type',
    },
    {
      title: '공정',
      dataIndex: 'process_name',
      key: 'process_name',
      render: (name: string) => name || '-',
    },
    {
      title: '이전 상태',
      dataIndex: 'previous_status',
      key: 'previous_status',
      render: (status: string) => status || '-',
    },
    {
      title: '새 상태',
      dataIndex: 'new_status',
      key: 'new_status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          Stock: 'green',
          Consuming: 'orange',
          Producing: 'blue',
          Finished: 'purple',
          Hold: 'gold',
          Defect: 'red',
        };
        return status ? <Tag color={colorMap[status] || 'default'}>{status}</Tag> : '-';
      },
    },
    {
      title: '작업자',
      dataIndex: 'worker_name',
      key: 'worker_name',
      render: (name: string) => name || '-',
    },
  ];

  // 공정별 차트 데이터 변환
  const processChartData = processStatus?.processes?.map(p => ({
    process_name: p.process_name,
    active_pallets: p.active_pallets,
    ...p.status_breakdown,
  })) || [];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>대시보드</h1>

      {statsLoading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" tip="데이터를 불러오는 중..." />
        </div>
      ) : (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/lots/pallets')}
              >
                <Statistic
                  title="활성 팔레트"
                  value={stats?.active_pallets || 0}
                  prefix={<InboxOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/fifo')}
              >
                <Statistic
                  title="총 재고 수량"
                  value={stats?.total_stock || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/lots/pallets')}
              >
                <Statistic
                  title="금일 생산량"
                  value={stats?.today_production || 0}
                  prefix={<SyncOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/monitoring')}
              >
                <Statistic
                  title="리더기 연결"
                  value={`${stats?.reader_status?.connected || 0} / ${stats?.reader_status?.total || 0}`}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card
                title="공정별 활성 팔레트"
                loading={processLoading}
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/processes')}
              >
                {processChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={processChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="process_name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="active_pallets" name="활성 팔레트" fill="#1890ff" />
                      <Bar dataKey="Stock" name="재고" fill="#52c41a" />
                      <Bar dataKey="Consuming" name="소비중" fill="#fa8c16" />
                      <Bar dataKey="Producing" name="생산중" fill="#722ed1" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                    데이터가 없습니다
                  </div>
                )}
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card
                title="공정별 현황 요약"
                loading={processLoading}
                hoverable
                style={clickableCardStyle}
                onClick={() => navigate('/processes')}
              >
                <Table
                  dataSource={processStatus?.processes || []}
                  columns={[
                    { title: '공정', dataIndex: 'process_name', key: 'process_name' },
                    { title: '라인', dataIndex: 'production_line', key: 'production_line' },
                    { title: '활성 팔레트', dataIndex: 'active_pallets', key: 'active_pallets' },
                  ]}
                  rowKey="process_id"
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
          </Row>

          <Card
            title="최근 활동"
            loading={activityLoading}
            hoverable
            style={clickableCardStyle}
            onClick={() => navigate('/traceability')}
          >
            <Table
              dataSource={recentActivities?.activities || []}
              columns={activityColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 800 }}
            />
          </Card>
        </>
      )}
    </div>
  );
}
