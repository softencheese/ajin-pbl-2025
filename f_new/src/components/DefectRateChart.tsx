import { Card } from './ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { line: 'A 라인', defectRate: 2.3, pass: 97.7 },
  { line: 'B 라인', defectRate: 1.8, pass: 98.2 },
  { line: 'C 라인', defectRate: 3.1, pass: 96.9 },
  { line: 'D 라인', defectRate: 1.5, pass: 98.5 },
  { line: 'E 라인', defectRate: 2.7, pass: 97.3 },
];

export function DefectRateChart() {
  return (
    <Card className="bg-[#151520] border-border p-6">
      <h3 className="mb-4">생산 라인별 불량률</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
          <XAxis 
            dataKey="line" 
            stroke="#8b8b9a"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#8b8b9a"
            style={{ fontSize: '12px' }}
            label={{ value: '불량률 (%)', angle: -90, position: 'insideLeft', style: { fill: '#8b8b9a' } }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1a1a24', 
              border: '1px solid #2a2a3a',
              borderRadius: '8px',
              color: '#ffffff'
            }}
            formatter={(value: number) => [`${value}%`, '불량률']}
          />
          <Bar dataKey="defectRate" fill="#ef4444" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
