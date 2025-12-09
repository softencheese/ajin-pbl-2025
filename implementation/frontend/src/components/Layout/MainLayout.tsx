import { useMemo } from 'react';
import { Layout, Menu } from 'antd';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  SettingOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  SearchOutlined,
  InboxOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

export function MainLayout() {
  const location = useLocation();

  // Determine selected key based on current path
  const selectedKey = useMemo(() => {
    const path = location.pathname;
    if (path === '/') return 'dashboard';
    if (path.startsWith('/process-mapping')) return 'process-mapping';
    if (path.startsWith('/materials')) return 'materials';
    if (path.startsWith('/parts')) return 'parts';
    if (path.startsWith('/pallets')) return 'pallets';
    if (path.startsWith('/monitoring')) return 'monitoring';
    if (path.startsWith('/traceability')) return 'traceability';
    if (path.startsWith('/inventory')) return 'inventory';
    return 'dashboard';
  }, [location.pathname]);

  return (
    <Layout style={{ minHeight: '100vh', backgroundColor: '#f0f2f5' }}>
      <Header style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', padding: '0 24px' }}>
        🏭 AJIN RFID 물류 추적 시스템
      </Header>

      <Layout style={{ backgroundColor: '#f0f2f5' }}>
        <Sider width={200} theme="light" style={{ backgroundColor: 'white' }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
          >
            <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
              <Link to="/">대시보드</Link>
            </Menu.Item>
            {/* <Menu.Item key="monitoring" icon={<MonitorOutlined />}>
              <Link to="/monitoring">모니터링</Link>
            </Menu.Item> */}
            <Menu.Item key="process-mapping" icon={<SettingOutlined />}>
              <Link to="/process-mapping">공정 배치</Link>
            </Menu.Item>
            <Menu.SubMenu key="master" icon={<DatabaseOutlined />} title="마스터 데이터">
              <Menu.Item key="materials">
                <Link to="/materials">원자재</Link>
              </Menu.Item>
              <Menu.Item key="parts">
                <Link to="/parts">품번</Link>
              </Menu.Item>
              <Menu.Item key="pallets">
                <Link to="/pallets">팔레트</Link>
              </Menu.Item>
            </Menu.SubMenu>
            <Menu.Item key="traceability" icon={<SearchOutlined />}>
              <Link to="/traceability">추적성 조회</Link>
            </Menu.Item>
            {/* <Menu.Item key="inventory" icon={<InboxOutlined />}>
              <Link to="/inventory">재고 현황</Link>
            </Menu.Item> */}
          </Menu>
        </Sider>

        <Layout style={{ padding: '24px', backgroundColor: '#f0f2f5' }}>
          <Content
            style={{
              background: 'white',
              padding: '24px',
              minHeight: 280,
              borderRadius: '8px',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)'
            }}
          >
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}
