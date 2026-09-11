import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// TWSE 回傳的買賣超單位是「股」，換算成「張」(1張=1000股) 比較符合台股慣用的顯示方式
function toLots(shares) {
  return Math.round(shares / 1000);
}

export default function InstitutionalFlowChart({ data }) {
  const chartData = data.map((d) => ({
    date: d.date,
    外資: toLots(d.foreign_net),
    投信: toLots(d.trust_net),
    自營商: toLots(d.dealer_net),
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(v) => v.toLocaleString()} />
        <Tooltip
          formatter={(value) => `${value.toLocaleString()} 張`}
          labelFormatter={(label) => `日期：${label}`}
        />
        <Legend />
        <Bar dataKey="外資" stackId="flow" fill="#2563eb" />
        <Bar dataKey="投信" stackId="flow" fill="#16a34a" />
        <Bar dataKey="自營商" stackId="flow" fill="#f59e0b" />
      </BarChart>
    </ResponsiveContainer>
  );
}
