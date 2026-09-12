import { useEffect, useState } from "react";
import "./App.css";
import InstitutionalFlowChart from "./components/InstitutionalFlowChart";
import ChipDataChart from "./components/ChipDataChart";
import ShareholdingChart from "./components/ShareholdingChart";
import OpinionList from "./components/OpinionList";
import NewsList from "./components/NewsList";
import SentimentBars from "./components/SentimentBars";
import ConsensusFeed from "./components/ConsensusFeed";
import InfluencerList from "./components/InfluencerList";
import InfluencerProfile from "./components/InfluencerProfile";
import {
  fetchChipData,
  fetchIndustry,
  fetchInstitutionalFlow,
  fetchNews,
  fetchShareholding,
  getChipData,
  getConsensus,
  getInfluencerTimeline,
  getInstitutionalFlow,
  getNews,
  getOpinions,
  getShareholding,
  getStockConsensus,
  listInfluencers,
  scrapeInfluencer,
} from "./api";

function todayStr() {
  return new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD
}

// 404（查無資料）視為「這檔股票還沒有資料」而不是失敗，讓每個區塊可以各自獨立顯示
async function settleAsEmptyOn404(promise) {
  try {
    return await promise;
  } catch (e) {
    if (e.status === 404) return [];
    throw e;
  }
}

function formatUpdatedAt(iso) {
  if (!iso) return "尚無資料";
  return iso.slice(0, 16).replace("T", " ");
}

function App() {
  const [fetchDate, setFetchDate] = useState(todayStr());
  const [stockId, setStockId] = useState("2330");
  const [flowData, setFlowData] = useState(null);
  const [chipData, setChipData] = useState(null);
  const [shareholding, setShareholding] = useState(null);
  const [opinions, setOpinions] = useState(null);
  const [news, setNews] = useState(null);
  const [stockConsensus, setStockConsensus] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [consensus, setConsensus] = useState(null);
  const [consensusError, setConsensusError] = useState("");

  const [influencers, setInfluencers] = useState([]);
  const [activeInfluencerId, setActiveInfluencerId] = useState(null);
  const [influencerTimeline, setInfluencerTimeline] = useState(null);

  async function loadConsensus() {
    try {
      const data = await getConsensus(7);
      setConsensus(data);
      setConsensusError("");
    } catch (e) {
      setConsensusError(`今日多空共識載入失敗：${e.message}`);
    }
  }

  useEffect(() => {
    loadConsensus();
    listInfluencers().then(setInfluencers).catch(() => {});
  }, []);

  async function handleFetchToday() {
    setLoading(true);
    setStatus("正在向 TWSE 抓取資料...");
    try {
      const [flowResult, chipResult] = await Promise.all([
        fetchInstitutionalFlow(fetchDate),
        fetchChipData(fetchDate),
      ]);
      setStatus(
        `抓取完成：資金流向 ${flowResult.records_saved} 檔、籌碼面 ${chipResult.records_saved} 檔`
      );
      await loadConsensus();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchOpinions() {
    setLoading(true);
    setStatus("正在抓取意見領袖最新貼文...");
    try {
      const list = await listInfluencers();
      const results = await Promise.all(list.map((i) => scrapeInfluencer(i.id)));
      const saved = results.reduce((sum, r) => sum + r.opinions_saved, 0);
      setStatus(`抓取完成：新增 ${saved} 則意見`);
      await loadConsensus();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchNews() {
    setLoading(true);
    setStatus("正在抓取財經新聞...");
    try {
      const result = await fetchNews();
      setStatus(`抓取完成：新增 ${result.items_saved} 則新聞`);
      await loadConsensus();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchShareholding() {
    setLoading(true);
    setStatus("正在抓取大戶持股比例...");
    try {
      const result = await fetchShareholding();
      setStatus(`抓取完成：${result.date} 共 ${result.records_saved} 檔`);
      await loadConsensus();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchIndustry() {
    setLoading(true);
    setStatus("正在抓取股票產業別...");
    try {
      const result = await fetchIndustry();
      setStatus(`抓取完成：補上 ${result.stocks_updated} 檔股票的產業別`);
      await loadConsensus();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(idOverride) {
    const id = (idOverride ?? stockId).trim();
    if (!id) return;
    setActiveInfluencerId(null);
    setStockId(id);
    setLoading(true);
    setStatus("查詢中...");
    setFlowData(null);
    setChipData(null);
    setShareholding(null);
    setOpinions(null);
    setNews(null);
    setStockConsensus(null);
    try {
      const [flow, chip, shareholdingList, opinionList, newsList, consensusResult] = await Promise.all([
        settleAsEmptyOn404(getInstitutionalFlow(id)),
        settleAsEmptyOn404(getChipData(id)),
        settleAsEmptyOn404(getShareholding(id)),
        settleAsEmptyOn404(getOpinions(id)),
        settleAsEmptyOn404(getNews(id)),
        getStockConsensus(id),
      ]);
      setFlowData(flow);
      setChipData(chip);
      setShareholding(shareholdingList);
      setOpinions(opinionList);
      setNews(newsList);
      setStockConsensus(consensusResult);
      setStatus("");
    } catch (e) {
      setStatus(`查詢失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectInfluencer(id) {
    setActiveInfluencerId(id);
    setInfluencerTimeline(null);
    try {
      const data = await getInfluencerTimeline(id);
      setInfluencerTimeline(data);
    } catch (e) {
      setStatus(`載入意見領袖資料失敗：${e.message}`);
    }
  }

  const industryItems = (consensus?.industry_sentiment || []).map((i) => ({
    key: i.industry,
    label: i.industry,
    bullish: i.bullish,
    bearish: i.bearish,
    neutral: i.neutral,
    total: i.total,
  }));

  const stockItems = (consensus?.stock_sentiment || []).map((s) => ({
    key: s.stock_id,
    label: `${s.stock_name || s.stock_id}（${s.stock_id}）`,
    bullish: s.bullish,
    bearish: s.bearish,
    neutral: s.neutral,
    total: s.total,
    divergent: s.has_divergence,
    stock_id: s.stock_id,
  }));

  if (activeInfluencerId && influencerTimeline) {
    return (
      <div className="page">
        <header>
          <h1>台股盤後分析工具</h1>
          <p className="disclaimer">僅供公開資訊整理，非投資建議</p>
        </header>
        <section className="panel">
          <InfluencerProfile
            timeline={influencerTimeline}
            onBack={() => setActiveInfluencerId(null)}
          />
        </section>
      </div>
    );
  }

  return (
    <div className="page">
      <header>
        <h1>台股盤後分析工具</h1>
        <p className="disclaimer">僅供公開資訊整理，非投資建議</p>
      </header>

      <section className="panel">
        <div className="home-header">
          <h2>今日多空共識</h2>
          <button onClick={loadConsensus} disabled={loading}>
            重新整理
          </button>
        </div>

        {consensus && (
          <p className="section-meta">
            統計最近 {consensus.window_days} 天｜資金流向更新於{" "}
            {formatUpdatedAt(consensus.last_updated.institutional_flow)}｜籌碼面更新於{" "}
            {formatUpdatedAt(consensus.last_updated.chip_data)}｜大戶持股更新於{" "}
            {formatUpdatedAt(consensus.last_updated.shareholding)}｜意見領袖更新於{" "}
            {formatUpdatedAt(consensus.last_updated.opinions)}｜新聞更新於{" "}
            {formatUpdatedAt(consensus.last_updated.news)}
          </p>
        )}

        {consensusError && <p className="status">{consensusError}</p>}

        {consensus && (
          <>
            <h3>依產業別的多空分布</h3>
            <SentimentBars items={industryItems} />

            <h3 style={{ marginTop: 20 }}>熱門個股的多空分布</h3>
            <SentimentBars
              items={stockItems}
              onItemClick={(item) => handleSearch(item.stock_id)}
              emptyHint="最近沒有被意見領袖／新聞明確點名的個股"
            />

            <h3 style={{ marginTop: 20 }}>最新意見／新聞</h3>
            <ConsensusFeed items={consensus.recent_items} />
          </>
        )}
      </section>

      <section className="panel">
        <h2>意見領袖</h2>
        <InfluencerList influencers={influencers} onSelect={handleSelectInfluencer} />
      </section>

      <details className="panel panel-collapsible">
        <summary>資料維護／手動抓取</summary>
        <div className="controls">
          <input
            type="date"
            value={fetchDate}
            onChange={(e) => setFetchDate(e.target.value)}
          />
          <button onClick={handleFetchToday} disabled={loading}>
            抓取該日盤後資料
          </button>
          <button onClick={handleFetchOpinions} disabled={loading}>
            抓意見領袖新貼文
          </button>
          <button onClick={handleFetchNews} disabled={loading}>
            抓新聞
          </button>
          <button onClick={handleFetchShareholding} disabled={loading}>
            抓大戶持股比例
          </button>
          <button onClick={handleFetchIndustry} disabled={loading}>
            抓股票產業別
          </button>
        </div>
      </details>

      {status && <p className="status">{status}</p>}

      <section className="panel">
        <h2>查詢單一股票細節</h2>
        <div className="controls">
          <input
            type="text"
            placeholder="股票代號，例如 2330"
            value={stockId}
            onChange={(e) => setStockId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button onClick={() => handleSearch()} disabled={loading}>
            查詢
          </button>
        </div>
      </section>

      {stockConsensus && (
        <section className="panel">
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
        </section>
      )}

      {flowData && (
        <section className="panel">
          <h2>三大法人買賣超（{stockId}）</h2>
          {flowData.length > 0 ? (
            <InstitutionalFlowChart data={flowData} />
          ) : (
            <p className="empty-hint">尚無資料</p>
          )}
        </section>
      )}

      {chipData && (
        <section className="panel">
          <h2>融資融券餘額（{stockId}）</h2>
          {chipData.length > 0 ? (
            <ChipDataChart data={chipData} />
          ) : (
            <p className="empty-hint">尚無資料</p>
          )}
        </section>
      )}

      {shareholding && (
        <section className="panel">
          <h2>大戶持股比例（{stockId}）</h2>
          {shareholding.length > 0 ? (
            <ShareholdingChart data={shareholding} />
          ) : (
            <p className="empty-hint">尚無資料</p>
          )}
        </section>
      )}

      {opinions && (
        <section className="panel">
          <h2>意見領袖怎麼看（{stockId}）</h2>
          <OpinionList opinions={opinions} />
        </section>
      )}

      {news && (
        <section className="panel">
          <h2>相關新聞（{stockId}）</h2>
          <NewsList news={news} />
        </section>
      )}
    </div>
  );
}

export default App;
