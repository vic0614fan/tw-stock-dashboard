import { useState } from "react";
import "./App.css";
import InstitutionalFlowChart from "./components/InstitutionalFlowChart";
import ChipDataChart from "./components/ChipDataChart";
import {
  fetchChipData,
  fetchInstitutionalFlow,
  getChipData,
  getInstitutionalFlow,
} from "./api";

function todayStr() {
  return new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD
}

function App() {
  const [fetchDate, setFetchDate] = useState(todayStr());
  const [stockId, setStockId] = useState("2330");
  const [flowData, setFlowData] = useState(null);
  const [chipData, setChipData] = useState(null);
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

  async function handleSearch() {
    if (!stockId.trim()) return;
    setLoading(true);
    setStatus("查詢中...");
    setFlowData(null);
    setChipData(null);
    try {
      const [flow, chip] = await Promise.all([
        getInstitutionalFlow(stockId.trim()),
        getChipData(stockId.trim()),
      ]);
      setFlowData(flow);
      setChipData(chip);
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
        <h2>抓取盤後資料</h2>
        <div className="controls">
          <input
            type="date"
            value={fetchDate}
            onChange={(e) => setFetchDate(e.target.value)}
          />
          <button onClick={handleFetchToday} disabled={loading}>
            抓取該日資料
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
            <p>尚無資料</p>
          )}
        </section>
      )}

      {chipData && (
        <section className="panel">
          <h2>融資融券餘額（{stockId}）</h2>
          {chipData.length > 0 ? (
            <ChipDataChart data={chipData} />
          ) : (
            <p>尚無資料</p>
          )}
        </section>
      )}
    </div>
  );
}

export default App;
