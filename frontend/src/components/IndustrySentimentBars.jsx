export default function IndustrySentimentBars({ industries }) {
  if (industries.length === 0) {
    return <p className="empty-hint">最近沒有可統計的意見／新聞資料</p>;
  }

  const maxTotal = Math.max(...industries.map((i) => i.total));

  return (
    <div className="industry-bars">
      {industries.map((i) => (
        <div className="industry-row" key={i.industry}>
          <span className="industry-name">{i.industry}</span>
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
