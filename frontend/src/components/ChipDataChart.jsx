import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function ChipDataChart({ data }) {
  const chartData = data.map((d) => ({
    date: d.date,
    融資餘額: d.margin_buy_balance,
    融券餘額: d.margin_sell_balance,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(v) => v.toLocaleString()} />
        <Tooltip
          formatter={(value) => `${value.toLocaleString()} 張`}
          labelFormatter={(label) => `日期：${label}`}
        />
        <Legend />
        <Line type="monotone" dataKey="融資餘額" stroke="#d97757" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="融券餘額" stroke="#7a8b99" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
