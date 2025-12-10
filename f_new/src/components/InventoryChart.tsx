import { Card } from './ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const data = [
  { name: '사용 가능', value: 450, color: '#22c55e' },
  { name: '생산 중', value: 280, color: '#3b82f6' },
  { name: '검사 대기', value: 85, color: '#eab308' },
  { name: '보류/불량', value: 70, color: '#ef4444' },
];

export function InventoryChart() {
  return (
    <Card className="bg-[#151520] border-border p-6">
      <h3 className="mb-4">코일 상태별 분포</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1a1a24', 
              border: '1px solid #2a2a3a',
              borderRadius: '8px',
              color: '#ffffff'
            }}
            formatter={(value: number) => [`${value} 코일`, '수량']}
          />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            iconType="circle"
            formatter={(value) => <span style={{ color: '#8b8b9a', fontSize: '12px' }}>{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
}
