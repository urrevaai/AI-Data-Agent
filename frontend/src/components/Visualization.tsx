import React from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

// The props are now much simpler: just the data and the suggestion object from the backend.
interface VisualizationProps {
  data: any[];
  suggestion: {
    chart_type?: string;
    x_axis?: string;
    y_axis?: string[] | string;
    title?: string;
  };
}

// A custom tooltip for better styling
const ChartTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-gray-800 border border-gray-700 rounded-md shadow-lg">
        <p className="label text-sm text-blue-400">{`${label}`}</p>
        {payload.map((pld: any, index: number) => (
          <p key={index} className="intro text-xs" style={{ color: pld.color }}>
            {`${pld.name}: ${pld.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

const Visualization: React.FC<VisualizationProps> = ({ data, suggestion }) => {
  const { chart_type = 'table', x_axis, y_axis, title } = suggestion || {};

  if (!data || data.length === 0) {
    return <p className="text-gray-500 text-center p-4">No data to visualize.</p>;
  }

  // Determine candidate keys
  const allKeys = Object.keys(data[0] || {});
  const firstStringKey = allKeys.find(k => typeof (data[0] as any)[k] === 'string');
  const inferredXAxis = x_axis || firstStringKey || allKeys[0];

  // Collect numeric-like keys across the dataset
  const numericLikeKeys = Array.from(new Set(
    allKeys.filter(k => k !== inferredXAxis && data.some(row => {
      const v = (row as any)[k];
      const n = typeof v === 'number' ? v : parseFloat(v);
      return Number.isFinite(n);
    }))
  ));

  // Use suggestion y_axis if present, otherwise inferred numeric-like keys
  const rawYAxisKeys = Array.isArray(y_axis) ? y_axis : (y_axis ? [y_axis] : numericLikeKeys);
  // Keep only keys that exist in data
  const yAxisKeys = rawYAxisKeys.filter(k => allKeys.includes(k));

  // Final chart type guard
  const getChartType = () => {
    const typeStr = (chart_type || 'table').toLowerCase();
    if (typeStr.includes('bar')) return 'bar';
    if (typeStr.includes('line')) return 'line';
    if (typeStr.includes('pie')) return 'pie';
    return 'table';
  };
  const finalChartType = getChartType();

  // Coerce y values to numbers where possible; use null when not numeric
  const coercedData = data.map(row => {
    const next: any = { ...row };
    yAxisKeys.forEach(k => {
      const v = (row as any)[k];
      const n = typeof v === 'number' ? v : parseFloat(v);
      next[k] = Number.isFinite(n) ? n : null;
    });
    return next;
  });

  const renderChart = () => {
    switch (finalChartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={coercedData}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis dataKey={inferredXAxis} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
              <Tooltip content={<ChartTooltip />} />
              <Legend />
              {yAxisKeys.map((key, i) => <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} />)}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={coercedData}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis dataKey={inferredXAxis} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
              <Tooltip content={<ChartTooltip />} />
              <Legend />
              {yAxisKeys.map((key, i) => <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} />)}
            </LineChart>
          </ResponsiveContainer>
        );
    
      case 'pie':
        // For pie charts, we need a name and a value. We use the backend's hints.
        const nameKey = inferredXAxis || 'name';
        const dataKey = yAxisKeys[0] || 'value';
         return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={coercedData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: any) => {
                  const { percent, ...entry } = props || {};
                  const p = typeof percent === 'number' ? percent : 0;
                  return `${entry[nameKey]} ${(p * 100).toFixed(0)}%`;
                }}
                outerRadius={80}
                fill="#8884d8"
                dataKey={dataKey}
                nameKey={nameKey}
              >
                {coercedData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'table':
      default:
        const headers = Object.keys(data[0]);
        return (
          <div className="overflow-x-auto rounded-lg border border-gray-700">
            <table className="min-w-full divide-y divide-gray-600">
              <thead className="bg-gray-800">
                <tr>{headers.map(h => <th key={h} className="py-3 px-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">{h.replace(/_/g, ' ')}</th>)}</tr>
              </thead>
              <tbody className="bg-gray-900 divide-y divide-gray-700">
                {data.map((row, i) => <tr key={i}>{headers.map(h => <td key={h} className="py-4 px-4 text-sm text-gray-400 whitespace-nowrap">{String((row as any)[h] ?? '-')}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
        );
    }
  };

  return (
    <div>
        <h3 className="text-center font-bold mb-2 text-gray-300">{title || ''}</h3>
        {renderChart()}
    </div>
  )
};

export default Visualization;