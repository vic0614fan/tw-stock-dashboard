import { useEffect, useState } from "react";
import { getStocksByIndustry } from "../api";

export default function IndustryStockList({ industry, onSelectStock }) {
  const [stocks, setStocks] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setStocks(null);
    setError("");
    getStocksByIndustry(industry)
      .then(setStocks)
      .catch((e) => setError(`載入失敗：${e.message}`));
  }, [industry]);

  if (error) return <p className="status">{error}</p>;
  if (!stocks) return <p className="empty-hint">載入中...</p>;
  if (stocks.length === 0) return <p className="empty-hint">這個產業目前沒有已知股票</p>;

  return (
    <div className="stock-list-grid">
      {stocks.map((s) => (
        <button key={s.stock_id} className="stock-list-item" onClick={() => onSelectStock(s.stock_id)}>
          {s.name}（{s.stock_id}）
        </button>
      ))}
    </div>
  );
}
