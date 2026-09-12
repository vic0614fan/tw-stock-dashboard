# 開發進度

更新時間：2026-09-12

## 目前完成到哪個模組

1. ✅ 資金流向 — TWSE OpenAPI (T86)，端點：`POST/GET /api/institutional-flow`
2. ✅ 籌碼面 — TWSE OpenAPI (MI_MARGN)，端點：`POST/GET /api/chip-data`
   （大戶持股比例尚未做，需另外爬蟲或 FinMind，先跳過）
3. ✅ React 前端 — 已整合成單一 Dashboard
4. ✅ 意見領袖模組（Chris／Threads）— Playwright + Claude API 分類
5. ✅ 新聞模組 — Yahoo 股市 RSS + LLM 篩選個股相關性、正負面標記、摘要
6. ✅ 整合單一 Dashboard — 搜尋框輸入股票代號 → 四合一報告（資金流向／籌碼面／
   意見領袖／新聞），任一區塊沒資料不影響其他區塊顯示
7. ⬜ 老王／股乾爹／股海老牛 三位意見領袖尚未加入（架構已支援，用
   `POST /api/influencers` 建新的人物主檔即可）
8. ⬜ 鉅亨網新聞來源尚未加入（目前只有 Yahoo 股市，找不到穩定公開 RSS）

## 下一步

CLAUDE.md 列的四大核心方向（資金流向、籌碼面、意見領袖、新聞）都已經有 MVP，
整合 Dashboard 也做完了。可以考慮的方向：
- 大戶持股比例（集保股權分散表，週更）
- 新增第二、三位意見領袖
- 排程自動化（APScheduler 每日盤後自動抓取，不用手動按按鈕）
- 免責聲明／法遵文字加到前端頁面上

## 這次 session 的關鍵技術決策

- **新聞篩選策略**：不做假新聞偵測，靠來源白名單（Yahoo 股市正規財經媒體）
  保證真實性；用「標題相似度去重」（difflib，門檻 0.75，比對近 3 天）過濾
  重複報導；LLM 判斷「是否明確跟具體股票有關」，不相關的直接不存，解決
  「新聞太多、雜訊高」的問題。這是先做的簡單版本，代價是同一批不相關新聞
  每次重抓都會重新問一次 LLM（不會重複存，只是重複判斷），之後真的在意
  花費可以再加一張「已檢查但不相關」的記錄表。
- **前端四合一整合用 Promise.all + 每支 API 各自 catch 404**：資金流向／
  籌碼面用 `/{stock_id}` 端點，查無資料時後端回 404；如果四支 API 全部包在
  同一個 try/catch，任一支 404 就會讓整頁查詢「失敗」、什麼都不顯示。改成
  幫 404 單獨包一層轉成空陣列，四個區塊才能各自獨立顯示「尚無資料」而不會
  互相拖累。
- **`GET /api/opinions` 要額外組 influencer_name**：Pydantic 的
  `from_attributes=True` 沒辦法直接抓到跨表 join 的欄位，要在 router 裡手動
  組出帶 `influencer_name` 的物件（沿用資金流向/籌碼面查詢已经用過的
  `WithNameOut` 命名習慣）。
