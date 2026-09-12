import SentimentBadge from "./SentimentBadge";

function formatDate(iso) {
  if (!iso) return "";
  return iso.slice(0, 16).replace("T", " ");
}

export default function OpinionList({ opinions }) {
  if (opinions.length === 0) {
    return <p className="empty-hint">尚無相關意見資料</p>;
  }

  return (
    <ul className="card-list">
      {opinions.map((o) => (
        <li key={o.id} className="card">
          <div className="card-header">
            <span className="card-source">{o.influencer_name}</span>
            <SentimentBadge sentiment={o.sentiment} />
            <span className="card-date">{formatDate(o.published_at)}</span>
          </div>
          <p className="card-summary">{o.summary}</p>
          <a href={o.source_url} target="_blank" rel="noreferrer" className="card-link">
            查看原文
          </a>
        </li>
      ))}
    </ul>
  );
}
