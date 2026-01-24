import { useMemo } from 'react';
import { Layout, Menu } from 'antd';
import type { MenuProps } from 'antd';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  SettingOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  SearchOutlined,
  InboxOutlined,
  FieldTimeOutlined,
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
    if (path.startsWith('/items')) return 'items';
    if (path.startsWith('/parts')) return 'parts';
    if (path.startsWith('/processes')) return 'processes';
    if (path.startsWith('/lots/pallets')) return 'lots-pallets';
    if (path.startsWith('/pallets')) return 'pallets';
    if (path.startsWith('/monitoring')) return 'monitoring';
    if (path.startsWith('/fifo')) return 'fifo';
    if (path.startsWith('/traceability')) return 'traceability';
    if (path.startsWith('/inventory')) return 'inventory';
    return 'dashboard';
  }, [location.pathname]);

  // Menu items using the new items API
  const menuItems: MenuProps['items'] = [
    // 임시 주석처리 (화면 개발시 다시 주석 해제)
    // {
    //   key: 'dashboard',
    //   icon: <DashboardOutlined />,
    //   label: <Link to="/">대시보드</Link>,
    // },
    {
      key: 'items',
      icon: <DatabaseOutlined />,
      label: <Link to="/items">품목 관리</Link>,
    },
    {
      key: 'processes',
      icon: <SettingOutlined />,
      label: <Link to="/processes">공정 관리</Link>,
    },
    {
      key: 'lots',
      icon: <DatabaseOutlined />,
      label: 'LOT 관리',
      children: [
        {
          key: 'lots-pallets',
          label: <Link to="/lots/pallets">LOT-팔레트-RFID</Link>,
        },
      ],
    },
    {
      key: 'fifo',
      icon: <FieldTimeOutlined />,
      label: <Link to="/fifo">FIFO 모니터링</Link>,
    },
    {
      key: 'traceability',
      icon: <SearchOutlined />,
      label: <Link to="/traceability">추적성 조회</Link>,
    },
  ];

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
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
          />
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
