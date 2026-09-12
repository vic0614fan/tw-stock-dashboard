// 台股慣例：紅漲綠跌，所以多/正面用紅色、空/負面用綠色，中性用灰色
const POSITIVE = new Set(["多", "正面"]);
const NEGATIVE = new Set(["空", "負面"]);

export function sentimentColor(sentiment) {
  if (POSITIVE.has(sentiment)) return { bg: "#f7e3dd", fg: "#b8452f" };
  if (NEGATIVE.has(sentiment)) return { bg: "#e3ebe4", fg: "#3f7d52" };
  return { bg: "#f0eee5", fg: "#8a8578" };
}
