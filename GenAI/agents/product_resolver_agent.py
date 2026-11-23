from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from states.ProductResolution_Structure import ProductResolution
from langchain_groq import ChatGroq
from utills.loggers import get_logger


logger = get_logger("Product Resolver")


resolver_llm = llm = ChatGroq(model="openai/gpt-oss-120b"
    ).with_structured_output(ProductResolution)


PRODUCT_RESOLVER_PROMPT = """
You are a product reference resolution assistant for Kapruka.

Your task is to identify which product the customer is referring to.

You will receive:
1. The customer's latest message.
2. Previous conversation history.
3. Products previously returned by the search agent.
4. The customer's currently selected product.
5. Products already in the customer's cart.

IMPORTANT RULES:

1. You MUST select a product only from the supplied candidate products.

2. Never invent or modify a product ID.

3. Understand natural-language references, including:
   - Product names.
   - Product numbers and positions.
   - Partial product names.
   - Descriptions and attributes.
   - References such as "it", "that one", "the previous one".
   - References to products discussed earlier.

4. Use conversation history to resolve follow-up references.

5. If multiple products could match the request, return:
   status = "ambiguous"

6. If no candidate product matches, return:
   status = "not_found"

7. If exactly one product is identified, return:
   status = "resolved"
   and its exact product_id.

8. Extract the requested quantity.
   If no quantity is specified, use 1.

9. Never assume the first product is selected unless the
   conversation or user message indicates that.

10. If the customer asks for the cheapest or most expensive
    product, compare the supplied prices rather than guessing.

11. Do not execute any cart operation or retrieve product details.
    Your ONLY task is resolving the product reference.

Return the structured output.
"""


def normalize_product(product):
    if isinstance(product, dict):
        return product

    if hasattr(product, "model_dump"):
        return product.model_dump()

    return {}


async def product_resolver_agent(state: dict) -> dict:

    logger.info("Executing Product Resolver Agent...")

    query = state.get("query", "")

    products = [
        normalize_product(p)
        for p in state.get("last_search_results", [])
    ]

    selected_product = state.get("selected_product")

    if selected_product:
        selected_product = normalize_product(selected_product)

    cart = [
        normalize_product(item)
        for item in state.get("cart", [])
    ]

    # Build a compact candidate list.
    candidates = {}

    for product in products:
        product_id = str(product.get("id", ""))

        if product_id:
            candidates[product_id] = {
                "id": product_id,
                "name": (
                    product.get("name")
                    or product.get("title")
                    or ""
                ),
                "price": (
                    product.get("price")
                    or product.get("displayed_price")
                ),
                "description": product.get("description", ""),
            }

    # Include previously selected product.
    if selected_product:
        product_id = str(selected_product.get("id", ""))

        if product_id:
            candidates[product_id] = {
                "id": product_id,
                "name": (
                    selected_product.get("name")
                    or selected_product.get("title")
                    or ""
                ),
                "price": selected_product.get("price"),
                "description": selected_product.get("description", ""),
            }

    # Include cart products for references to existing cart items.
    for item in cart:
        product_id = str(item.get("product_id", ""))

        if product_id and product_id not in candidates:
            candidates[product_id] = {
                "id": product_id,
                "name": item.get("name", ""),
                "price": item.get("price"),
                "description": "",
            }

    # Conversation history.
    history = state.get("messages", [])

    recent_history = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in history[-10:]
    )

    resolver_input = f"""
CUSTOMER'S LATEST MESSAGE:
{query}

PREVIOUS CONVERSATION:
{recent_history}

AVAILABLE PRODUCT CANDIDATES:
{list(candidates.values())}

CURRENTLY SELECTED PRODUCT:
{selected_product}

CURRENT CART:
{cart}
"""

    result = await resolver_llm.ainvoke([
        SystemMessage(content=PRODUCT_RESOLVER_PROMPT),
        HumanMessage(content=resolver_input),
    ])

    print(result)

    # Validate the LLM's returned ID against backend candidates.
    if (
        result.status == "resolved"
        and result.product_id not in candidates
    ):
        logger.warning(
            "Resolver returned an unknown product ID: %s",
            result.product_id
        )

        result.status = "not_found"
        result.product_id = None
        result.reason = "The returned product was not in the candidate list."

    if result.status != "resolved":
        return {
            "product_resolution": result.model_dump(),
            "selected_product": None,
            "selected_product_id": None,
        }

    selected = candidates[result.product_id]

    # Retrieve the complete trusted product object.
    full_product = next(
        (
            normalize_product(p)
            for p in products
            if str(normalize_product(p).get("id")) == result.product_id
        ),
        None
    )

    if not full_product and selected_product:
        if str(selected_product.get("id")) == result.product_id:
            full_product = selected_product

    return {
        "product_resolution": result.model_dump(),
        "selected_product": full_product or selected,
        "selected_product_id": result.product_id,
        "cart_quantity": result.quantity,
    }