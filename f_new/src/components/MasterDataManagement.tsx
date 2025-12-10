import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { RawMaterialsManager } from './master-data/RawMaterialsManager';
import { PartsManager } from './master-data/PartsManager';
import { ProcessesManager } from './master-data/ProcessesManager';
import { RfidReadersManager } from './master-data/RfidReadersManager';
import { LotsManager } from './master-data/LotsManager';
import { AssemblyLotsManager } from './master-data/AssemblyLotsManager';
import { AssemblyComponentsManager } from './master-data/AssemblyComponentsManager';
import { 
  Package, 
  Boxes, 
  GitBranch, 
  Radio, 
  FileText, 
  Layers,
  ListTree
} from 'lucide-react';

export function MasterDataManagement() {
  const [activeTab, setActiveTab] = useState('raw-materials');

  const tabs = [
    { value: 'raw-materials', label: '원자재 마스터', icon: Package },
    { value: 'parts', label: '품번 마스터', icon: Boxes },
    { value: 'processes', label: '공정 마스터', icon: GitBranch },
    { value: 'rfid-readers', label: 'RFID 리더기', icon: Radio },
    { value: 'lots', label: '중간품 LOT', icon: FileText },
    { value: 'assembly-lots', label: '조립품 LOT', icon: Layers },
    { value: 'assembly-components', label: '조립품 구성요소', icon: ListTree },
  ];

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-white">마스터 데이터 관리</h2>
        <p className="text-muted-foreground mt-1">
          원자재, 품번, 공정, LOT 등 시스템의 핵심 마스터 데이터 관리
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#151520] border border-border p-1 h-auto flex-wrap">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                <Icon className="size-4" />
                <span>{tab.label}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        <TabsContent value="raw-materials" className="space-y-4">
          <RawMaterialsManager />
        </TabsContent>

        <TabsContent value="parts" className="space-y-4">
          <PartsManager />
        </TabsContent>

        <TabsContent value="processes" className="space-y-4">
          <ProcessesManager />
        </TabsContent>

        <TabsContent value="rfid-readers" className="space-y-4">
          <RfidReadersManager />
        </TabsContent>

        <TabsContent value="lots" className="space-y-4">
          <LotsManager />
        </TabsContent>

        <TabsContent value="assembly-lots" className="space-y-4">
          <AssemblyLotsManager />
        </TabsContent>

        <TabsContent value="assembly-components" className="space-y-4">
          <AssemblyComponentsManager />
        </TabsContent>
      </Tabs>
    </div>
  );
}
