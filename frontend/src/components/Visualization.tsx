import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface VisualizationProps {
  type: 'bar' | 'line' | 'pie' | 'table';
  data: any[];
  suggestion: string;
  xAxisKey?: string;
  yAxisKey?: string;
  pieKey?: string;
  pieNameKey?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

const Visualization: React.FC<VisualizationProps> = ({ 
  type, 
  data, 
  suggestion, 
  xAxisKey, 
  yAxisKey, 
  pieKey, 
  pieNameKey 
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 bg-dark-card rounded-lg border border-dark-border">
        <p className="text-primary-muted text-center">No data available for visualization</p>
      </div>
    );
  }

  // Infer keys if not provided, using the first data object as a hint
  const inferKeys = (data: any[]) => {
    if (data.length > 0) {
      const keys = Object.keys(data[0]);
      return {
        inferredXAxisKey: keys[0],
        inferredYAxisKey: keys[1],
        inferredPieKey: keys[0], // For pie, value is usually the first key
        inferredPieNameKey: keys[1], // For pie, name is usually the second key
      };
    }
    return {
      inferredXAxisKey: 'name',
      inferredYAxisKey: 'value',
      inferredPieKey: 'value',
      inferredPieNameKey: 'name',
    };
  };

  const inferred = inferKeys(data);

  const resolvedXAxisKey = xAxisKey || inferred.inferredXAxisKey;
  const resolvedYAxisKey = yAxisKey || inferred.inferredYAxisKey;
  const resolvedPieKey = pieKey || inferred.inferredPieKey;
  const resolvedPieNameKey = pieNameKey || inferred.inferredPieNameKey;

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={resolvedXAxisKey} // Use resolved key
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E1E1E', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#E5E7EB'
                }}
              />
              <Bar dataKey={resolvedYAxisKey} fill="#3B82F6" radius={[4, 4, 0, 0]} /> {/* Use resolved key */}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={resolvedXAxisKey} // Use resolved key
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E1E1E', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#E5E7EB'
                }}
              />
              <Line 
                type="monotone" 
                dataKey={resolvedYAxisKey} // Use resolved key
                stroke="#3B82F6" 
                strokeWidth={3}
                dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props) => {
                  const entry = props as any; // Cast to any to access dynamic key
                  const name = entry[resolvedPieNameKey]; // Use resolved key
                  const percent = entry.percent;
                  const pct = typeof percent === 'number' ? Math.round(percent * 100) : 0;
                  return `${name ?? ''} ${pct}%`;
                }}
                outerRadius={80}
                fill="#8884d8"
                dataKey={resolvedPieKey} // Use resolved key
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E1E1E', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#E5E7EB'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'table':
        const columns = Object.keys(data[0] || {});
        return (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-border">
                  {columns.map((column) => (
                    <th
                      key={column}
                      className="text-left py-3 px-4 font-semibold text-primary-text bg-dark-hover"
                    >
                      {column.charAt(0).toUpperCase() + column.slice(1)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => (
                  <tr
                    key={index}
                    className="border-b border-dark-border hover:bg-dark-hover transition-colors"
                  >
                    {columns.map((column) => (
                      <td key={column} className="py-3 px-4 text-primary-muted">
                        {row[column]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      default:
        return <p className="text-primary-muted">Unsupported visualization type</p>;
    }
  };

  return (
    <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
      {suggestion && (
        <div className="p-4 border-b border-dark-border">
          <p className="text-sm text-primary-muted">{suggestion}</p>
        </div>
      )}
      <div className="p-4 min-h-[300px]"> {/* Added min-height for consistent chart area */}
        {renderChart()}
      </div>
    </div>
  );
};

export default Visualization;
