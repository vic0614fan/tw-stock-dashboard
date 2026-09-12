import SentimentBadge from "./SentimentBadge";

const PLATFORM_LABEL = { threads: "Threads", youtube: "YouTube", blog: "部落格" };

function formatDate(iso) {
  if (!iso) return "";
  return iso.slice(0, 16).replace("T", " ");
}

export default function InfluencerProfile({ timeline, onBack }) {
  const { influencer, stocks } = timeline;

  return (
    <div>
      <button className="back-link" onClick={onBack}>
        ← 回到今日多空共識
      </button>

      <div className="influencer-profile-header">
        <h2>{influencer.name}</h2>
        <p className="section-meta">
          {PLATFORM_LABEL[influencer.platform] || influencer.platform}
          {influencer.category && ` · ${influencer.category}`} ·{" "}
          <a href={influencer.profile_url} target="_blank" rel="noreferrer">
            前往原始頁面
          </a>
        </p>
      </div>

      {stocks.length === 0 ? (
        <p className="empty-hint">這位意見領袖還沒有標記過任何個股的意見</p>
      ) : (
        stocks.map((s) => (
          <div key={s.stock_id} className="timeline-stock-group">
            <h3>
              {s.stock_name || s.stock_id}（{s.stock_id}）
            </h3>
            <ul className="card-list">
              {s.opinions.map((o, idx) => (
                <li key={idx} className="card">
                  <div className="card-header">
                    <SentimentBadge sentiment={o.sentiment} />
                    {o.trend && (
                      <span
                        className={`trend-badge ${o.trend === "反轉" ? "reversed" : "continued"}`}
                      >
                        {o.trend}
                      </span>
                    )}
                    <span className="card-date">{formatDate(o.published_at)}</span>
                  </div>
                  <p className="card-summary">{o.summary}</p>
                  <a href={o.url} target="_blank" rel="noreferrer" className="card-link">
                    查看原文
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}
