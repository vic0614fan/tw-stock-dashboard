import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// 比例比前一週下降超過這個百分點，畫成警示色（紅色實心點）
const WARN_DROP_THRESHOLD = 2;

function WarnDot({ cx, cy, payload }) {
  const color = payload.drop >= WARN_DROP_THRESHOLD ? "#b8452f" : "#d97757";
  const r = payload.drop >= WARN_DROP_THRESHOLD ? 5 : 3;
  return <circle cx={cx} cy={cy} r={r} fill={color} stroke="none" />;
}

export default function ShareholdingChart({ data }) {
  const chartData = data.map((d, i) => ({
    date: d.date,
    大戶持股比例: d.large_holder_ratio,
    drop: i > 0 ? data[i - 1].large_holder_ratio - d.large_holder_ratio : 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(v) => `${v}%`} domain={["auto", "auto"]} />
        <Tooltip
          formatter={(value) => `${value}%`}
          labelFormatter={(label) => `週別：${label}`}
        />
        <Line
          type="monotone"
          dataKey="大戶持股比例"
          stroke="#d97757"
          strokeWidth={2}
          dot={<WarnDot />}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
