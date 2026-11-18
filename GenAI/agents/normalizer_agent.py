
from typing import Any

from schemas.chat_response import ChatResponse


def normalize_response(
    state: dict[str, Any],
    thread_id: str,
) -> ChatResponse:

    """
    Converts agent-specific outputs into a common API response.

    The frontend does not need to know which agent executed.
    """

    query = state.get("query", "")

    intent = state.get("intent", "")
    next_agent = state.get("next_agent", "")

    # Get the agent that actually handled the request.
    agent = next_agent or intent

    # Default response structure.
    response = {
        "thread_id": thread_id,
        "query": query,
        "answer": "How can I help you with your shopping?",
        "products": [],
        "total_results": 0,
        "comparison": None,
        "cart": None,
        "checkout": None,
        "agent": agent,
        "intent": intent,
        "metadata": {},
    }

    # --------------------------------------------------
    # SEARCH AGENT
    # --------------------------------------------------

    search = state.get("search_agent_output")

    if search:

        response["answer"] = search.message
        response["products"] = search.products
        response["total_results"] = search.total_results

        response["agent"] = "search_agent"

    # --------------------------------------------------
    # COMPARISON AGENT
    # --------------------------------------------------

    comparison = state.get("comparison_agent_output")

    if comparison:

        response["answer"] = comparison.message

        response["comparison"] = {
            "criteria": comparison.criteria,
            "products": comparison.comparison,
            "recommendation": comparison.recommendation,
        }

        response["agent"] = "comparison_agent"

    # --------------------------------------------------
    # GIFT RECOMMENDATION AGENT
    # --------------------------------------------------

    gift = state.get("gift_agent_output")

    if gift:

        response["answer"] = gift.message
        response["products"] = gift.products

        response["metadata"]["recommendation_reason"] = (
            gift.recommendation_reason
        )

        response["agent"] = "gift_agent"

    # --------------------------------------------------
    # FOLLOW-UP AGENT
    # --------------------------------------------------

    followup = state.get("followup_agent_output")

    if followup:

        response["answer"] = followup.message

        response["metadata"]["referenced_product_ids"] = (
            followup.referenced_product_ids
        )

        response["agent"] = "followup_agent"

    # --------------------------------------------------
    # CART AGENT
    # --------------------------------------------------

    cart = state.get("cart_agent_output")

    if cart:

        response["answer"] = cart.message

        response["cart"] = {
            "items": cart.items,
            "item_count": cart.item_count,
            "subtotal": cart.subtotal,
            "currency": cart.currency,
        }

        response["agent"] = "cart_agent"

    # --------------------------------------------------
    # CHECKOUT AGENT
    # --------------------------------------------------

    checkout = state.get("checkout_agent_output")

    if checkout:

        response["answer"] = checkout.message

        response["checkout"] = {
            "status": checkout.status,
            "missing_fields": checkout.missing_fields,
            "checkout_url": checkout.checkout_url,
            "order_ref": checkout.order_ref,
        }

        response["agent"] = "checkout_agent"

    # --------------------------------------------------
    # RETURN NORMALIZED RESPONSE
    # --------------------------------------------------

    return ChatResponse(**response)
