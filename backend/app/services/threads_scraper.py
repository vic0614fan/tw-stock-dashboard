import re
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

# 每篇貼文的文字容器是用 DOM 結構「往上爬到剛好只包住這一篇貼文」的方式找出來的，
# 而不是用 class name（Threads 的 class 是自動產生的亂碼，改版就失效），細節見 _EXTRACT_JS。
_EXTRACT_JS = """
() => {
  const allTimeAnchors = Array.from(document.querySelectorAll('a[href*="/post/"] time'));
  const seen = new Set();
  const results = [];
  allTimeAnchors.forEach(t => {
    const anchor = t.closest('a');
    const href = anchor.getAttribute('href');
    const postId = href.split('/post/')[1]?.split('?')[0];
    if (!postId || seen.has(postId)) return;
    seen.add(postId);

    let el = anchor;
    let prevEl = anchor;
    for (let i = 0; i < 20 && el.parentElement; i++) {
      prevEl = el;
      el = el.parentElement;
      if (el.querySelectorAll('a[href*="/post/"] time').length > 1) { el = prevEl; break; }
    }
    results.push({
      postId,
      url: location.origin + href,
      datetime: t.getAttribute('datetime'),
      text: el.innerText,
    });
  });
  return results;
}
"""

# 貼文文字最前面通常是「帳號\n相對時間」、最後面常跟著「翻譯」按鈕文字和讚數/留言數這些數字，
# 屬於畫面雜訊，分類給 LLM 前先盡量濾掉
_NOISE_LINE_PATTERNS = [
    re.compile(r"^翻譯$"),
    re.compile(r"^\d+$"),
    re.compile(r"^Add LINE friend$"),
    re.compile(r"^reurl\.cc$"),
]


def _clean_text(raw: str, handle: str) -> str:
    lines = raw.split("\n")
    if lines and lines[0].strip() == handle:
        lines = lines[1:]
    if lines and re.match(r"^\d+(分鐘|小時|天|週|個月|年)$", lines[0].strip()):
        lines = lines[1:]
    while lines and any(p.match(lines[-1].strip()) for p in _NOISE_LINE_PATTERNS):
        lines.pop()
    return "\n".join(lines).strip()


def scrape_threads_posts(handle: str, limit: int = 10) -> list[dict]:
    """抓取 Threads 公開個人頁面最近的貼文（不需登入）。

    Threads 未登入狀態下公開頁面只會顯示最近幾篇貼文，這是平台本身的限制，不是抓取邏輯的問題。
    """
    url = f"https://www.threads.net/@{handle}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="zh-TW",
            )
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector('a[href*="/post/"] time', timeout=15000)
            raw_posts = page.evaluate(_EXTRACT_JS)
        finally:
            browser.close()

    posts = []
    for p in raw_posts[:limit]:
        published_at = None
        if p["datetime"]:
            published_at = datetime.fromisoformat(p["datetime"].replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        posts.append(
            {
                "post_id": p["postId"],
                "url": p["url"],
                "published_at": published_at,
                "content": _clean_text(p["text"], handle),
            }
        )
    return posts
