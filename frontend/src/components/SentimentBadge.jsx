import { sentimentColor } from "../sentiment";

export default function SentimentBadge({ sentiment }) {
  const { bg, fg } = sentimentColor(sentiment);
  return (
    <span
      style={{
        background: bg,
        color: fg,
        borderRadius: 4,
        padding: "2px 8px",
        fontSize: "0.8rem",
        fontWeight: 600,
        whiteSpace: "nowrap",
      }}
    >
      {sentiment}
    </span>
  );
}
