import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert } from 'antd';
import {
  InboxOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  StopOutlined,
  WarningOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useDashboardStats, useProcessSummary, useRecentActivity } from '../../hooks/useDashboard';
import dayjs from 'dayjs';

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: processSummary = [], isLoading: processLoading } = useProcessSummary();
  const { data: recentActivity = [], isLoading: activityLoading } = useRecentActivity();

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
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss'),
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
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
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
      title: '설명',
      dataIndex: 'description',
      key: 'description',
    },
  ];

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
              <Card>
                <Statistic
                  title="총 팔레트"
                  value={stats?.total_pallets || 0}
                  prefix={<InboxOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="재고"
                  value={stats?.stock_pallets || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="생산 중"
                  value={stats?.producing_pallets || 0}
                  prefix={<SyncOutlined spin />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="완료"
                  value={stats?.finished_pallets || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="투입 대기"
                  value={stats?.consuming_pallets || 0}
                  prefix={<ExperimentOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="보류"
                  value={stats?.hold_pallets || 0}
                  prefix={<StopOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="불량"
                  value={stats?.defect_pallets || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="총 LOT"
                  value={(stats?.total_lots || 0) + (stats?.total_assembly_lots || 0)}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="공정별 현황" loading={processLoading}>
                {processSummary && processSummary.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={processSummary}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="process_name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="pallet_count" name="팔레트 수" fill="#1890ff" />
                      <Bar dataKey="lot_count" name="LOT 수" fill="#52c41a" />
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
              <Card title="팔레트 상태 분포">
                {stats ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={[
                        { name: '재고', value: stats.stock_pallets },
                        { name: '투입', value: stats.consuming_pallets },
                        { name: '생산', value: stats.producing_pallets },
                        { name: '완료', value: stats.finished_pallets },
                        { name: '보류', value: stats.hold_pallets },
                        { name: '불량', value: stats.defect_pallets },
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" name="수량" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                    데이터가 없습니다
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          <Card title="최근 활동" loading={activityLoading}>
            <Table
              dataSource={Array.isArray(recentActivity) ? recentActivity : []}
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
