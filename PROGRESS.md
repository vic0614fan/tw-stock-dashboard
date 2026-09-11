# 開發進度

更新時間：2026-09-12

## 目前完成到哪個模組

1. ✅ 資金流向 — TWSE OpenAPI (T86) 三大法人買賣超，FastAPI + SQLite，端點：
   `POST/GET /api/institutional-flow`
2. ✅ 籌碼面 — TWSE OpenAPI (MI_MARGN) 融資融券餘額，端點：`POST/GET /api/chip-data`
   （大戶持股比例尚未做，需另外爬蟲或 FinMind，先跳過）
3. ✅ React 前端 MVP — 日期抓取＋股票查詢＋兩張圖表，本機可跑（`frontend/`，
   `npm run dev`）
4. ✅ 意見領袖模組（Chris／Threads）— Playwright 爬蟲＋Claude API 分類，
   端點：`POST /api/influencers/{id}/scrape`、`GET /api/influencers/{id}/opinions`、
   `GET /api/opinions?stock_id=`
5. ⬜ 新聞模組（尚未開始）
6. ⬜ 整合單一 Dashboard（搜尋框輸入股票代號 → 四合一報告，尚未開始）
7. ⬜ 老王／股乾爹／股海老牛 三位意見領袖尚未加入（架構已支援，用
   `POST /api/influencers` 建新的人物主檔即可）

## 下一步

照開發順序，下一步是「⑤ 新聞模組」：財經新聞 RSS（鉅亨網、Yahoo 股市等）
＋ LLM 正負面標記＋一句話摘要＋卡片式列表呈現。

## 這次 session 的關鍵技術決策

- **TWSE T86 API 的 `selectType` 要用 `ALLBUT0999`**，不能用 `ALL`——`ALL`
  會把上萬檔權證、牛熊證也一起抓進來（一天變 15000+ 筆），`ALLBUT0999`
  才是正確的「上市股票＋ETF」範圍（約 1200~1300 檔）。
- **MI_MARGN 的融資／融券欄位名稱是重複的**（買進/賣出/前日餘額/今日餘額
  兩邊都同名），沒辦法用欄位名稱對應，改用固定 index，並加一個欄位清單比對，
  格式一旦跟預期不同就直接報錯，避免 TWSE 改格式時默默解析出錯資料。
- **這台機器的 npm 有嚴重的環境問題**：npm 內部 DNS 查詢多傳了 `ADDRCONFIG`
  選項會導致查詢失敗（`ENOTFOUND`/`ENOENT`），跟 IPv6 開關無關（原本懷疑
  IPv6、繞了一圈是錯的）。已經用一個 Node 啟動腳本永久修好（`NODE_OPTIONS`
  環境變數 + `C:\Users\Vic_Fan\.node-fix\force-ipv4-dns.cjs`），以後
  `npm install` 不會再卡住。
- **Threads 沒有可用的公開 API**，發文內容要靠 JS 動態渲染，且背後的
  GraphQL 端點有簽章防護抓不到。改用 Playwright 開真的無頭瀏覽器載入頁面，
  再用「DOM 結構往上爬到剛好只包住一篇貼文」的方式擷取文字（不依賴
  Threads 會變動的 class name），未登入狀態下可以抓到最近 5 篇貼文。
- **意見資料用 `opinion_data` + `opinion_stocks` 兩張表**（一對多），因為
  一篇貼文常常提到好幾檔股票，這樣才能乾淨地做「查某檔股票被哪些人在
  哪些時間點提到」的查詢。
- **LLM 分類用 Claude 的 tool use（結構化輸出）**而不是要求它輸出 JSON
  文字再自己 parse，避免格式跑掉的問題；實測連公司名對應股票代號都能
  正確判斷（例如「金居」→ 8358）。
- **API 金鑰管理**：`backend/.env.example` 放假的佔位符（會被 git 追蹤），
  真正的金鑰放 `backend/.env`（已被 `.gitignore` 排除）。
