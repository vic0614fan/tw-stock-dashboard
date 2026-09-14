import { useEffect, useState } from "react";
import "./App.css";
import SentimentBars from "./components/SentimentBars";
import IndustryFlowBars from "./components/IndustryFlowBars";
import ShareholdingFlowBars from "./components/ShareholdingFlowBars";
import ConsensusFeed from "./components/ConsensusFeed";
import InfluencerList from "./components/InfluencerList";
import InfluencerProfile from "./components/InfluencerProfile";
import Modal from "./components/Modal";
import IndustryStockList from "./components/IndustryStockList";
import StockDetailModal from "./components/StockDetailModal";
import {
  fetchChipData,
  fetchIndustry,
  fetchInstitutionalFlow,
  fetchNews,
  fetchShareholding,
  getConsensus,
  getIndustryFlow,
  getInfluencerTimeline,
  getShareholdingFlow,
  listInfluencers,
  scrapeInfluencer,
} from "./api";

function todayStr() {
  return new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD
}

// 日期型欄位（資金流向/籌碼面/大戶持股）後端直接回 "YYYY-MM-DD"；有時間的（意見領袖/新聞）
// 回 ISO datetime，這裡只在真的有時間資訊時才顯示到分鐘，避免顯示假的「00:00」
function formatUpdatedAt(value) {
  if (!value) return "尚無資料";
  if (value.includes("T")) return value.slice(0, 16).replace("T", " ");
  return value;
}

const NAV_SECTIONS = [
  { id: "section-consensus", label: "今日多空共識" },
  { id: "section-industry-flow", label: "主力資金流向" },
  { id: "section-shareholding", label: "大戶持股" },
  { id: "section-feed", label: "最新意見／新聞" },
  { id: "section-influencers", label: "意見領袖" },
  { id: "section-maintenance", label: "資料維護" },
  { id: "section-search", label: "查詢個股" },
];

function App() {
  const [fetchDate, setFetchDate] = useState(todayStr());
  const [stockIdInput, setStockIdInput] = useState("2330");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [consensus, setConsensus] = useState(null);
  const [consensusError, setConsensusError] = useState("");

  const [industryFlow, setIndustryFlow] = useState(null);
  const [industryFlowError, setIndustryFlowError] = useState("");
  const [flowWindowDays, setFlowWindowDays] = useState(1);

  const [shareholdingFlow, setShareholdingFlow] = useState(null);
  const [shareholdingFlowError, setShareholdingFlowError] = useState("");

  const [influencers, setInfluencers] = useState([]);
  const [activeInfluencerId, setActiveInfluencerId] = useState(null);
  const [influencerTimeline, setInfluencerTimeline] = useState(null);

  // modal: null | {type:"stock", stockId} | {type:"industry", industry}
  const [modal, setModal] = useState(null);

  async function loadConsensus() {
    try {
      const data = await getConsensus(7);
      setConsensus(data);
      setConsensusError("");
    } catch (e) {
      setConsensusError(`今日多空共識載入失敗：${e.message}`);
    }
  }

  async function loadIndustryFlow(days = flowWindowDays) {
    try {
      const data = await getIndustryFlow(days);
      setIndustryFlow(data);
      setIndustryFlowError("");
    } catch (e) {
      setIndustryFlowError(`主力資金流向載入失敗：${e.message}`);
    }
  }

  async function loadShareholdingFlow() {
    try {
      const data = await getShareholdingFlow();
      setShareholdingFlow(data);
      setShareholdingFlowError("");
    } catch (e) {
      setShareholdingFlowError(`大戶持股載入失敗：${e.message}`);
    }
  }

  function handleFlowWindowChange(e) {
    const days = Number(e.target.value);
    setFlowWindowDays(days);
    loadIndustryFlow(days);
  }

  async function refreshHome() {
    await Promise.all([loadConsensus(), loadIndustryFlow(), loadShareholdingFlow()]);
  }

  useEffect(() => {
    refreshHome();
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
      await refreshHome();
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
      await refreshHome();
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
      await refreshHome();
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
      await refreshHome();
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
      await refreshHome();
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  function openStockModal(id) {
    setModal({ type: "stock", stockId: id });
  }

  function openIndustryModal(industry) {
    setModal({ type: "industry", industry });
  }

  function handleSearchSubmit() {
    const id = stockIdInput.trim();
    if (!id) return;
    openStockModal(id);
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
    <div className="app-shell">
      <nav className="side-nav">
        {NAV_SECTIONS.map((s) => (
          <a key={s.id} href={`#${s.id}`}>
            {s.label}
          </a>
        ))}
      </nav>

      <div className="page">
        <header>
          <h1>台股盤後分析工具</h1>
          <p className="disclaimer">僅供公開資訊整理，非投資建議</p>
        </header>

        <section className="panel" id="section-consensus">
          <div className="home-header">
            <h2>今日多空共識</h2>
            <button onClick={refreshHome} disabled={loading}>
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
        </section>

        {consensus && (
          <div className="grid-2col">
            <section className="panel">
              <h3>依產業別的多空分布（點產業看類股）</h3>
              <SentimentBars items={industryItems} onItemClick={(item) => openIndustryModal(item.key)} />
            </section>

            <section className="panel">
              <h3>熱門個股的多空分布（點股票看細節）</h3>
              <SentimentBars
                items={stockItems}
                onItemClick={(item) => openStockModal(item.stock_id)}
                emptyHint="最近沒有被意見領袖／新聞明確點名的個股"
              />
            </section>
          </div>
        )}

        <section className="panel" id="section-industry-flow">
          <div className="home-header">
            <h3 style={{ margin: 0 }}>主力資金流向（依產業，點產業看類股）</h3>
            <div className="controls">
              <span className="section-meta" style={{ margin: 0 }}>
                三大法人買賣超合計
              </span>
              <select value={flowWindowDays} onChange={handleFlowWindowChange}>
                <option value={1}>當日</option>
                <option value={3}>最近 3 個交易日</option>
                <option value={5}>最近 5 個交易日</option>
                <option value={10}>最近 10 個交易日</option>
                <option value={20}>最近 20 個交易日</option>
              </select>
            </div>
          </div>
          {industryFlow && industryFlow.trading_dates.length > 0 && (
            <p className="section-meta">
              {industryFlow.trading_dates.length === 1
                ? `資料日期：${industryFlow.trading_dates[0]}`
                : `資料範圍：${industryFlow.trading_dates[0]} ~ ${
                    industryFlow.trading_dates[industryFlow.trading_dates.length - 1]
                  }（共 ${industryFlow.trading_dates.length} 個交易日）`}
            </p>
          )}
          {industryFlowError && <p className="status">{industryFlowError}</p>}
          {industryFlow && (
            <IndustryFlowBars industries={industryFlow.industries} onItemClick={openIndustryModal} />
          )}
        </section>

        <section className="panel" id="section-shareholding">
          <h3>大戶持股比例（依產業，點產業看類股）</h3>
          {shareholdingFlow && (
            <p className="section-meta">
              {shareholdingFlow.mode === "level"
                ? `資料日期：${shareholdingFlow.latest_date}（TDCC 每週更新一次，目前只有一週快照，
                   顯示目前比例；累積兩週以上後會自動改顯示週對週增減）`
                : `${shareholdingFlow.previous_date} → ${shareholdingFlow.latest_date} 的週對週變化`}
            </p>
          )}
          {shareholdingFlowError && <p className="status">{shareholdingFlowError}</p>}
          <ShareholdingFlowBars data={shareholdingFlow} onItemClick={openIndustryModal} />
        </section>

        <section className="panel" id="section-feed">
          <h3>最新意見／新聞</h3>
          <div className="scroll-panel">
            {consensus && <ConsensusFeed items={consensus.recent_items} />}
          </div>
        </section>

        <section className="panel" id="section-influencers">
          <h2>意見領袖</h2>
          <InfluencerList influencers={influencers} onSelect={handleSelectInfluencer} />
        </section>

        <details className="panel panel-collapsible" id="section-maintenance">
          <summary>資料維護／手動抓取</summary>
          <div className="controls">
            <input type="date" value={fetchDate} onChange={(e) => setFetchDate(e.target.value)} />
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

        <section className="panel" id="section-search">
          <h2>查詢個股</h2>
          <div className="controls">
            <input
              type="text"
              placeholder="股票代號，例如 2330"
              value={stockIdInput}
              onChange={(e) => setStockIdInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
            />
            <button onClick={handleSearchSubmit} disabled={loading}>
              查詢
            </button>
          </div>
        </section>
      </div>

      {modal?.type === "stock" && (
        <StockDetailModal stockId={modal.stockId} onClose={() => setModal(null)} />
      )}

      {modal?.type === "industry" && (
        <Modal title={`${modal.industry}｜類股列表`} onClose={() => setModal(null)}>
          <IndustryStockList industry={modal.industry} onSelectStock={openStockModal} />
        </Modal>
      )}
    </div>
  );
}

export default App;
