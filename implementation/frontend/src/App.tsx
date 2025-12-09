import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from './components/Layout/MainLayout';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { ProcessMappingPage } from './pages/ProcessMapping/ProcessMappingPage';
import { MaterialsPage } from './pages/Materials/MaterialsPage';
import { MonitoringPage } from './pages/Monitoring/MonitoringPage';
import { PlaceholderPage } from './pages/PlaceholderPage';

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
            <Route
              path="parts"
              element={<PlaceholderPage title="품번 관리" subtitle="품번(Part) 데이터를 관리합니다." />}
            />
            <Route
              path="pallets"
              element={<PlaceholderPage title="팔레트 관리" subtitle="팔레트와 RFID 태그를 관리합니다." />}
            />
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route
              path="traceability"
              element={<PlaceholderPage title="추적성 조회" subtitle="팔레트와 LOT의 이력을 조회합니다." />}
            />
            <Route
              path="inventory"
              element={<PlaceholderPage title="재고 현황" subtitle="Stock 상태의 팔레트를 조회합니다." />}
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
