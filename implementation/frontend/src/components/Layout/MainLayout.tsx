import { useMemo, useEffect } from 'react';
import { Layout, Menu, Modal } from 'antd';
import type { MenuProps } from 'antd';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useWebSocket } from '../../hooks/useWebSocket';
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
    const { on, off } = useWebSocket();

    useEffect(() => {
        const handleScanEvent = (data: any) => {
            // Check if the pallet transitioned to Defect, Hold, or Scrap
            if (data.status === 'Defect' || data.status === 'Hold' || data.status === 'Scrap') {
                const statusMap: Record<string, { label: string; color: string; isDanger: boolean }> = {
                    Defect: { label: '불량(Defect)', color: 'red', isDanger: true },
                    Hold: { label: '보류(Hold)', color: '#faad14', isDanger: false },
                    Scrap: { label: '폐기(Scrap)', color: '#cf1322', isDanger: true },
                };

                const statusInfo = statusMap[data.status] || { label: data.status, color: 'black', isDanger: false };
                const simpleLabel = statusInfo.label.split('(')[0];

                Modal.warning({
                    title: `🚨 ${statusInfo.label} 발생 알림`,
                    content: (
                        <div style={{ marginTop: '16px' }}>
                            <p><b>팔레트:</b> {data.pallet_no || '자동 바인딩 생성'}</p>
                            {data.process_code && data.process_code !== 'UNKNOWN' && (
                                <p><b>공정:</b> {data.process_code}</p>
                            )}
                            <p><b>위치:</b> {data.port_name}</p>
                            <p><b>RFID/바코드:</b> {data.identifier}</p>
                            <p style={{ color: statusInfo.color, marginTop: '12px', fontWeight: 'bold' }}>
                                해당 팔레트가 {simpleLabel} 상태로 전환되었습니다. 조치가 필요합니다.
                            </p>
                        </div>
                    ),
                    okText: '확인',
                    centered: true,
                    okButtonProps: { danger: statusInfo.isDanger },
                });
            }
        };

        const handleScanError = (data: any) => {
            if (data.type === 'FIFO_VIOLATION') {
                Modal.error({
                    title: '🚨 FIFO 위반 알림',
                    content: (
                        <div style={{ marginTop: '16px' }}>
                            <p><b>위치:</b> {data.port_name}</p>
                            <p><b>RFID/바코드:</b> {data.identifier}</p>
                            <p style={{ color: 'red', marginTop: '12px', fontWeight: 'bold' }}>
                                선입선출(FIFO) 위반!
                            </p>
                            <p>
                                {data.message}
                            </p>
                        </div>
                    ),
                    okText: '확인',
                    centered: true,
                });
            } else {
                Modal.error({
                    title: '스캔 에러',
                    content: `[${data.port_name}] ${data.message}`,
                    centered: true,
                });
            }
        };

        const handleFifoScan = (data: any) => {
            if (data.status === 'BLOCKED') {
                Modal.error({
                    title: '🚨 FIFO 위반 (진입 차단)',
                    content: (
                        <div style={{ marginTop: '16px' }}>
                            <p><b>팔레트:</b> {data.pallet_no}</p>
                            <p style={{ color: 'red', marginTop: '12px', fontWeight: 'bold' }}>
                                선입선출 위반! 투입이 차단되었습니다.
                            </p>
                            <p>
                                먼저 생산된 재고를 확인하세요. <br />
                                <b>정말 투입해야 한다면 한 번 더 스캔하세요.</b>
                            </p>
                        </div>
                    ),
                    okText: '확인',
                    centered: true,
                });
            } else if (data.status === 'FORCED_PASS') {
                Modal.warning({
                    title: '⚠️ FIFO 예외 투입 진행',
                    content: (
                        <div style={{ marginTop: '16px' }}>
                            <p><b>팔레트:</b> {data.pallet_no}</p>
                            <p style={{ color: '#faad14', marginTop: '12px', fontWeight: 'bold' }}>
                                예외 투입 승인!
                            </p>
                            <p>
                                순서가 맞지 않지만 작업자 판단에 의해 투입을 진행합니다.
                                (이력에 기록됨)
                            </p>
                        </div>
                    ),
                    okText: '확인',
                    centered: true,
                });
            }
        };

        on('scan_event', handleScanEvent);
        on('scan_error', handleScanError);
        on('fifo_scan', handleFifoScan);

        return () => {
            off('scan_event', handleScanEvent);
            off('scan_error', handleScanError);
            off('fifo_scan', handleFifoScan);
        };
    }, [on, off]);

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
        if (path.startsWith('/lots/history')) return 'lots-history';
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
                {
                    key: 'lots-history',
                    label: <Link to="/lots/history">LOT 히스토리</Link>,
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
