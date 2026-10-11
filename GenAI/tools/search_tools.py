import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class SearchArgs(BaseModel):
    q: str = Field(description="Head noun only, e.g. 'birthday cake'. No budget words.")
    max_price: Optional[float] = Field(None, description="Upper budget. 'under/below/less than/within X' => max_price=X")
    min_price: Optional[float] = Field(None, description="Lower bound. ONLY for 'over/above/at least X'")
    in_stock_only: bool = True
    sort: str = Field("relevance", description="relevance | price_asc | price_desc | newest | bestseller. 'newest' only if the customer asks for latest/new.")
    limit: int = Field(10, ge=1, le=50)
    currency: str = "LKR"


def _text(raw) -> str:
    """MCP adapters may return a str or a list of content blocks."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in raw)
    return str(raw)


def make_search_tool(mcp_search_tool):
    async def search_products(q, max_price=None, min_price=None, in_stock_only=True,
                              sort="relevance", limit=10, currency="LKR"):
        params = dict(q=q, max_price=max_price, min_price=min_price,
                      in_stock_only=in_stock_only, sort=sort, limit=limit, currency=currency)
        params = {k: v for k, v in params.items() if v is not None}
        params["response_format"] = "json"          # forced, never left to the model

        text = _text(await mcp_search_tool.ainvoke({"params": params}))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text, []                          # "No products found..." / "Error: ..."

        products = [{
            "id": r["id"],
            "name": r["name"],
            "price": (r.get("price") or {}).get("amount"),
            "currency": (r.get("price") or {}).get("currency", currency),
            "in_stock": r["in_stock"],
            "stock_level": r.get("stock_level"),
            "product_url": r["url"],                 # copied verbatim
            "image_url": r.get("image_url"),
        } for r in data.get("results", [])]

        facets = [f["name"] for f in data.get("facets", {}).get("categories", [])]
        content = json.dumps({"products": products, "category_facets": facets})
        return content, products                     # (what the LLM sees, exact data)

    return StructuredTool.from_function(
        coroutine=search_products,
        name="search_products",
        description="Search Kapruka products by keyword with price/stock/sort filters.",
        args_schema=SearchArgs,
        response_format="content_and_artifact",
    )