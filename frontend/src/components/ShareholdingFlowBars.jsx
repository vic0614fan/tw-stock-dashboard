// 大戶持股比例依產業排行。mode="level"（只有一週快照）顯示目前比例的單向橫條，
// mode="change"（兩週以上）顯示週對週變化的雙向橫條（增碼=紅、減碼=綠，跟其他區塊色彩語意一致）
export default function ShareholdingFlowBars({ data, onItemClick }) {
  if (!data || data.industries.length === 0) {
    return <p className="empty-hint">尚無大戶持股資料，請先抓取大戶持股比例</p>;
  }

  if (data.mode === "level") {
    return (
      <div className="flow-bars">
        {data.industries.map((i) => (
          <div
            className={`flow-row${onItemClick ? " clickable" : ""}`}
            key={i.industry}
            onClick={onItemClick ? () => onItemClick(i.industry) : undefined}
          >
            <span className="flow-name">{i.industry}</span>
            <div className="flow-bar-track">
              <div
                className="flow-bar-fill buy"
                style={{ left: 0, width: `${i.avg_ratio}%`, borderRadius: 3 }}
              />
            </div>
            <span className="flow-value">平均 {i.avg_ratio.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    );
  }

  const maxAbs = Math.max(...data.industries.map((i) => Math.abs(i.avg_change)), 0.1);

  return (
    <div className="flow-bars">
      {data.industries.map((i) => {
        const pct = (Math.abs(i.avg_change) / maxAbs) * 50;
        const isUp = i.avg_change >= 0;
        return (
          <div
            className={`flow-row${onItemClick ? " clickable" : ""}`}
            key={i.industry}
            onClick={onItemClick ? () => onItemClick(i.industry) : undefined}
          >
            <span className="flow-name">{i.industry}</span>
            <div className="flow-bar-track">
              <div className="flow-bar-center" />
              <div
                className={`flow-bar-fill ${isUp ? "buy" : "sell"}`}
                style={isUp ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
              />
            </div>
            <span className={`flow-value ${isUp ? "count-bullish" : "count-bearish"}`}>
              {isUp ? "增碼" : "減碼"} {Math.abs(i.avg_change).toFixed(2)} 個百分點
            </span>
          </div>
        );
      })}
    </div>
  );
}
