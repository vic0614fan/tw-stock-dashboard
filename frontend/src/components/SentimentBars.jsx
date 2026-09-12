// 共用元件：依產業或依個股呈現多空分布橫條圖。items 需要 {key, label, bullish, bearish,
// neutral, total}，divergent 為 true 的項目（同時有人看多看空）會加上警示標籤
export default function SentimentBars({ items, onItemClick, emptyHint = "最近沒有可統計的意見／新聞資料" }) {
  if (items.length === 0) {
    return <p className="empty-hint">{emptyHint}</p>;
  }

  const maxTotal = Math.max(...items.map((i) => i.total));

  return (
    <div className="industry-bars">
      {items.map((i) => (
        <div
          className={`industry-row${onItemClick ? " clickable" : ""}`}
          key={i.key}
          onClick={onItemClick ? () => onItemClick(i) : undefined}
        >
          <span className="industry-name">
            {i.label}
            {i.divergent && (
              <span className="divergence-badge" title="意見分歧：同時有人看多、有人看空">
                ⚠️ 分歧
              </span>
            )}
          </span>
          <div className="industry-bar-track" style={{ flex: maxTotal }}>
            <div
              className="industry-bar-track-inner"
              style={{ width: `${(i.total / maxTotal) * 100}%` }}
            >
              {i.bullish > 0 && (
                <div
                  className="industry-bar-seg bullish"
                  style={{ flex: i.bullish }}
                  title={`看多 ${i.bullish}`}
                />
              )}
              {i.neutral > 0 && (
                <div
                  className="industry-bar-seg neutral"
                  style={{ flex: i.neutral }}
                  title={`中性 ${i.neutral}`}
                />
              )}
              {i.bearish > 0 && (
                <div
                  className="industry-bar-seg bearish"
                  style={{ flex: i.bearish }}
                  title={`看空 ${i.bearish}`}
                />
              )}
            </div>
          </div>
          <span className="industry-counts">
            <span className="count-bullish">多{i.bullish}</span>
            {" / "}
            <span className="count-bearish">空{i.bearish}</span>
            {" / "}
            <span className="count-neutral">中性{i.neutral}</span>
          </span>
        </div>
      ))}
    </div>
  );
}
