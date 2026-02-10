import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from './components/Layout/MainLayout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { ProcessMappingPage } from './pages/ProcessMapping/ProcessMappingPage';
import { MaterialsPage } from './pages/Materials/MaterialsPage';
import { MonitoringPage } from './pages/Monitoring/MonitoringPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { LotPalletsPage } from './pages/LOTs/LotPalletsPage';
import { LotHistoryPage } from './pages/LOTs/LotHistoryPage';
import { LotTrackingPage } from './pages/Traceability/LotTrackingPage';
import { ItemsPage } from './pages/Items/ItemsPage';
import { ProcessManagementPage } from './pages/Processes/ProcessManagementPage';
import { FIFOMonitoringPage } from './pages/FIFO/FIFOMonitoringPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ErrorPage } from './pages/ErrorPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="process-mapping" element={<ProcessMappingPage />} />
              <Route path="materials" element={<MaterialsPage />} />
              <Route path="items" element={<ItemsPage />} />
              <Route
                path="parts"
                element={<PlaceholderPage title="품번 관리" subtitle="품번(Part) 데이터를 관리합니다." />}
              />
              <Route path="processes" element={<ProcessManagementPage />} />
              <Route path="lots/pallets" element={<LotPalletsPage />} />
              <Route path="lots/history" element={<LotHistoryPage />} />
              <Route
                path="pallets"
                element={<PlaceholderPage title="팔레트 관리" subtitle="팔레트와 RFID 태그를 관리합니다." />}
              />
              <Route path="monitoring" element={<MonitoringPage />} />
              <Route path="fifo" element={<FIFOMonitoringPage />} />
              <Route path="traceability" element={<LotTrackingPage />} />
              <Route
                path="inventory"
                element={<PlaceholderPage title="재고 현황" subtitle="Stock 상태의 팔레트를 조회합니다." />}
              />
              <Route path="error" element={<ErrorPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
