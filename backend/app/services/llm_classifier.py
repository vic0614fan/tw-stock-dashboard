import anthropic

from app.config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-4-5"

_CLASSIFY_TOOL = {
    "name": "classify_opinion",
    "description": "分析一篇台股意見領袖的貼文，判斷多空立場、摘要理由、標記提到的股票代號",
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["多", "空", "中性"],
                "description": "整篇貼文對台股後市／提到個股的整體多空立場",
            },
            "summary": {
                "type": "string",
                "description": "一句話摘要這篇貼文的理由或論點（繁體中文，30字以內）",
            },
            "stocks": {
                "type": "array",
                "description": "貼文中明確提到的台股個股，只列有講到具體公司/股票的，不要列大盤指數或產業名稱",
                "items": {
                    "type": "object",
                    "properties": {
                        "stock_id": {"type": "string", "description": "股票代號，例如 2330"},
                        "name": {"type": "string", "description": "股票名稱，例如 台積電"},
                    },
                    "required": ["stock_id", "name"],
                },
            },
        },
        "required": ["sentiment", "summary", "stocks"],
    },
}


class LLMNotConfiguredError(Exception):
    """尚未設定 ANTHROPIC_API_KEY。"""


def classify_opinion(content: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise LLMNotConfiguredError("尚未設定 ANTHROPIC_API_KEY，請在 backend/.env 中設定")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[_CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_opinion"},
        messages=[{"role": "user", "content": content}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_opinion":
            return block.input

    raise RuntimeError("LLM 未回傳預期的分類結果")
