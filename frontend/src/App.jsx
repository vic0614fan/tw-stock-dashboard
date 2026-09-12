import { useState } from "react";
import "./App.css";
import InstitutionalFlowChart from "./components/InstitutionalFlowChart";
import ChipDataChart from "./components/ChipDataChart";
import OpinionList from "./components/OpinionList";
import NewsList from "./components/NewsList";
import {
  fetchChipData,
  fetchInstitutionalFlow,
  fetchNews,
  getChipData,
  getInstitutionalFlow,
  getNews,
  getOpinions,
  listInfluencers,
  scrapeInfluencer,
} from "./api";

function todayStr() {
  return new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD
}

// 404（查無資料）視為「這檔股票還沒有資料」而不是失敗，讓四塊報告可以各自獨立顯示
async function settleAsEmptyOn404(promise) {
  try {
    return await promise;
  } catch (e) {
    if (e.status === 404) return [];
    throw e;
  }
}

function App() {
  const [fetchDate, setFetchDate] = useState(todayStr());
  const [stockId, setStockId] = useState("2330");
  const [flowData, setFlowData] = useState(null);
  const [chipData, setChipData] = useState(null);
  const [opinions, setOpinions] = useState(null);
  const [news, setNews] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

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
      const influencers = await listInfluencers();
      const results = await Promise.all(influencers.map((i) => scrapeInfluencer(i.id)));
      const saved = results.reduce((sum, r) => sum + r.opinions_saved, 0);
      setStatus(`抓取完成：新增 ${saved} 則意見`);
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
    } catch (e) {
      setStatus(`抓取失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    const id = stockId.trim();
    if (!id) return;
    setLoading(true);
    setStatus("查詢中...");
    setFlowData(null);
    setChipData(null);
    setOpinions(null);
    setNews(null);
    try {
      const [flow, chip, opinionList, newsList] = await Promise.all([
        settleAsEmptyOn404(getInstitutionalFlow(id)),
        settleAsEmptyOn404(getChipData(id)),
        settleAsEmptyOn404(getOpinions(id)),
        settleAsEmptyOn404(getNews(id)),
      ]);
      setFlowData(flow);
      setChipData(chip);
      setOpinions(opinionList);
      setNews(newsList);
      setStatus("");
    } catch (e) {
      setStatus(`查詢失敗：${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header>
        <h1>台股盤後分析工具</h1>
        <p className="disclaimer">僅供公開資訊整理，非投資建議</p>
      </header>

      <section className="panel">
        <h2>抓取資料</h2>
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
        </div>
      </section>

      <section className="panel">
        <h2>查詢個股</h2>
        <div className="controls">
          <input
            type="text"
            placeholder="股票代號，例如 2330"
            value={stockId}
            onChange={(e) => setStockId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading}>
            查詢
          </button>
        </div>
      </section>

      {status && <p className="status">{status}</p>}

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
