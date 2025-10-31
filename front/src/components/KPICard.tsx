import { Card } from './ui/card';
import { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  change?: number;
  unit?: string;
}

export function KPICard({ title, value, icon: Icon, change, unit }: KPICardProps) {
  const hasPositiveChange = change !== undefined && change > 0;
  const hasNegativeChange = change !== undefined && change < 0;

  return (
    <Card className="bg-[#151520] border-border p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-muted-foreground text-sm mb-2">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl text-foreground">{value}</span>
            {unit && <span className="text-muted-foreground text-sm">{unit}</span>}
          </div>
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {hasPositiveChange && <TrendingUp className="size-4 text-green-400" />}
              {hasNegativeChange && <TrendingDown className="size-4 text-red-400" />}
              <span className={hasPositiveChange ? "text-green-400 text-sm" : "text-red-400 text-sm"}>
                {change > 0 ? '+' : ''}{change}
              </span>
            </div>
          )}
        </div>
        <div className="bg-blue-600/20 p-3 rounded-lg">
          <Icon className="size-6 text-blue-400" />
        </div>
      </div>
    </Card>
  );
}
