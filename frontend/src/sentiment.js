// 台股慣例：紅漲綠跌，所以多/正面用紅色、空/負面用綠色，中性用灰色
const POSITIVE = new Set(["多", "正面"]);
const NEGATIVE = new Set(["空", "負面"]);

export function sentimentColor(sentiment) {
  if (POSITIVE.has(sentiment)) return { bg: "#fee2e2", fg: "#b91c1c" };
  if (NEGATIVE.has(sentiment)) return { bg: "#dcfce7", fg: "#15803d" };
  return { bg: "#f3f4f6", fg: "#4b5563" };
}
