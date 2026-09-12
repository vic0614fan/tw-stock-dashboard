import SentimentBadge from "./SentimentBadge";

function formatDate(iso) {
  if (!iso) return "";
  return iso.slice(0, 16).replace("T", " ");
}

export default function NewsList({ news }) {
  if (news.length === 0) {
    return <p className="empty-hint">尚無相關新聞</p>;
  }

  return (
    <ul className="card-list">
      {news.map((n) => (
        <li key={n.id} className="card">
          <div className="card-header">
            <span className="card-source">{n.source}</span>
            <SentimentBadge sentiment={n.sentiment} />
            <span className="card-date">{formatDate(n.published_at)}</span>
          </div>
          <p className="card-title">{n.title}</p>
          <p className="card-summary">{n.summary}</p>
          <a href={n.url} target="_blank" rel="noreferrer" className="card-link">
            查看原文
          </a>
        </li>
      ))}
    </ul>
  );
}
