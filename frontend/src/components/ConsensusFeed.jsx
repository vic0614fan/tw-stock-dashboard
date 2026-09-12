import SentimentBadge from "./SentimentBadge";

function formatDate(iso) {
  if (!iso) return "";
  return iso.slice(0, 16).replace("T", " ");
}

export default function ConsensusFeed({ items }) {
  if (items.length === 0) {
    return <p className="empty-hint">最近沒有相關意見／新聞</p>;
  }

  return (
    <ul className="card-list">
      {items.map((item, idx) => (
        <li key={idx} className="card">
          <div className="card-header">
            <span className="card-type-tag">{item.type === "opinion" ? "意見" : "新聞"}</span>
            <span className="card-source">{item.source}</span>
            <SentimentBadge sentiment={item.sentiment} />
            <span className="card-date">{formatDate(item.published_at)}</span>
          </div>
          <p className="card-summary">
            {item.stock_name && (
              <span className="card-stock-tag">
                {item.stock_name}（{item.stock_id}）
              </span>
            )}
            {item.summary}
          </p>
          <a href={item.url} target="_blank" rel="noreferrer" className="card-link">
            查看原文
          </a>
        </li>
      ))}
    </ul>
  );
}
