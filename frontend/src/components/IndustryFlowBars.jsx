// 主力資金流向（依產業）：以零為中心的雙向橫條圖，買超（正）往右、賣超（負）往左，
// 跟 SentimentBars 的「多空共識」不是同一種資料，色彩語意沿用同一套（買超=紅、賣超=綠）
export default function IndustryFlowBars({ industries }) {
  if (industries.length === 0) {
    return <p className="empty-hint">尚無資金流向資料，請先抓取盤後資料</p>;
  }

  const maxAbs = Math.max(...industries.map((i) => Math.abs(i.total_net_lots)), 1);

  return (
    <div className="flow-bars">
      {industries.map((i) => {
        const pct = (Math.abs(i.total_net_lots) / maxAbs) * 50;
        const isBuy = i.total_net_lots >= 0;
        return (
          <div className="flow-row" key={i.industry}>
            <span className="flow-name">{i.industry}</span>
            <div className="flow-bar-track">
              <div className="flow-bar-center" />
              <div
                className={`flow-bar-fill ${isBuy ? "buy" : "sell"}`}
                style={isBuy ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
                title={`${isBuy ? "買超" : "賣超"} ${Math.abs(i.total_net_lots).toLocaleString()} 張`}
              />
            </div>
            <span className={`flow-value ${isBuy ? "count-bullish" : "count-bearish"}`}>
              {isBuy ? "買超" : "賣超"} {Math.abs(i.total_net_lots).toLocaleString()} 張
            </span>
          </div>
        );
      })}
    </div>
  );
}
