const PLATFORM_LABEL = { threads: "Threads", youtube: "YouTube", blog: "部落格" };

export default function InfluencerList({ influencers, onSelect }) {
  if (influencers.length === 0) {
    return <p className="empty-hint">尚無意見領袖資料</p>;
  }

  return (
    <div className="influencer-grid">
      {influencers.map((i) => (
        <button key={i.id} className="influencer-card" onClick={() => onSelect(i.id)}>
          <div className="influencer-card-name">{i.name}</div>
          <div className="influencer-card-meta">
            {PLATFORM_LABEL[i.platform] || i.platform}
            {i.category && ` · ${i.category}`}
          </div>
        </button>
      ))}
    </div>
  );
}
