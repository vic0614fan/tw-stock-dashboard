import { useEffect, useState } from "react";
import InstitutionalFlowChart from "./InstitutionalFlowChart";
import ChipDataChart from "./ChipDataChart";
import ShareholdingChart from "./ShareholdingChart";
import OpinionList from "./OpinionList";
import NewsList from "./NewsList";
import Modal from "./Modal";
import {
  getChipData,
  getInstitutionalFlow,
  getNews,
  getOpinions,
  getShareholding,
  getStockConsensus,
} from "../api";

async function settleAsEmptyOn404(promise) {
  try {
    return await promise;
  } catch (e) {
    if (e.status === 404) return [];
    throw e;
  }
}

export default function StockDetailModal({ stockId, onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [flowData, setFlowData] = useState(null);
  const [chipData, setChipData] = useState(null);
  const [shareholding, setShareholding] = useState(null);
  const [opinions, setOpinions] = useState(null);
  const [news, setNews] = useState(null);
  const [stockConsensus, setStockConsensus] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([
      settleAsEmptyOn404(getInstitutionalFlow(stockId)),
      settleAsEmptyOn404(getChipData(stockId)),
      settleAsEmptyOn404(getShareholding(stockId)),
      settleAsEmptyOn404(getOpinions(stockId)),
      settleAsEmptyOn404(getNews(stockId)),
      getStockConsensus(stockId),
    ])
      .then(([flow, chip, shareholdingList, opinionList, newsList, consensusResult]) => {
        if (cancelled) return;
        setFlowData(flow);
        setChipData(chip);
        setShareholding(shareholdingList);
        setOpinions(opinionList);
        setNews(newsList);
        setStockConsensus(consensusResult);
      })
      .catch((e) => !cancelled && setError(`查詢失敗：${e.message}`))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [stockId]);

  return (
    <Modal title={`股票細節：${stockId}`} onClose={onClose}>
      {loading && <p className="empty-hint">查詢中...</p>}
      {error && <p className="status">{error}</p>}

      {stockConsensus && (
        <>
          {stockConsensus.summary ? (
            <div className="stock-consensus-card">
              <strong>
                {stockConsensus.summary.stock_name || stockId}（{stockId}）
                最近 {stockConsensus.window_days} 天共識：
              </strong>
              <span className="count-bullish">看多 {stockConsensus.summary.bullish}</span>
              <span className="count-bearish">看空 {stockConsensus.summary.bearish}</span>
              <span className="count-neutral">中性 {stockConsensus.summary.neutral}</span>
              {stockConsensus.summary.has_divergence && (
                <span className="divergence-badge">⚠️ 意見分歧</span>
              )}
            </div>
          ) : (
            <p className="empty-hint">最近沒有意見領袖或新聞明確提到這檔股票</p>
          )}
        </>
      )}

      {(flowData || chipData) && (
        <div className="grid-2col">
          {flowData && (
            <section className="panel">
              <h2>三大法人買賣超</h2>
              {flowData.length > 0 ? (
                <InstitutionalFlowChart data={flowData} />
              ) : (
                <p className="empty-hint">尚無資料</p>
              )}
            </section>
          )}

          {chipData && (
            <section className="panel">
              <h2>融資融券餘額</h2>
              {chipData.length > 0 ? (
                <ChipDataChart data={chipData} />
              ) : (
                <p className="empty-hint">尚無資料</p>
              )}
            </section>
          )}
        </div>
      )}

      {shareholding && (
        <section className="panel">
          <h2>大戶持股比例</h2>
          {shareholding.length > 0 ? (
            <ShareholdingChart data={shareholding} />
          ) : (
            <p className="empty-hint">尚無資料</p>
          )}
        </section>
      )}

      {(opinions || news) && (
        <div className="grid-2col">
          {opinions && (
            <section className="panel">
              <h2>意見領袖怎麼看</h2>
              <div className="scroll-panel">
                <OpinionList opinions={opinions} />
              </div>
            </section>
          )}

          {news && (
            <section className="panel">
              <h2>相關新聞</h2>
              <div className="scroll-panel">
                <NewsList news={news} />
              </div>
            </section>
          )}
        </div>
      )}
    </Modal>
  );
}
