
from states.agent_state import AgentState
from utills.loggers import get_logger


async def cart_agent(state: AgentState) -> dict:

    logger = get_logger("Cart Agent")
    logger.info("Executing Cart Agent...")

    products = state.get("last_search_results", [])
    selected_product_id = state.get("selected_product_id")
    cart = list(state.get("cart", []))

    selected_product = next(
        (
            product for product in products
            if str(product.get("product_id")) == str(selected_product_id)
        ),
        None
    )

    if not selected_product:
        return {
            "response": {
                "message": (
                    "I couldn't identify that product. "
                    "Please search for it again."
                ),
                "agent": "cart_agent"
            }
        }

    product_id = str(selected_product["product_id"])

    # Extract the price from trusted backend search data.
    price = selected_product.get("price")

    if price is None:
        price = selected_product.get("displayed_price")

    if price is None:
        return {
            "response": {
                "message": (
                    "I couldn't verify the price of this product. "
                    "Please check its product page before adding it."
                ),
                "agent": "cart_agent"
            }
        }

    try:
        price = float(str(price).replace(",", "").replace("Rs.", "").strip())
    except (ValueError, TypeError):
        return {
            "response": {
                "message": "The product price could not be verified.",
                "agent": "cart_agent"
            }
        }

    if price < 0:
        return {
            "response": {
                "message": "The product has an invalid price.",
                "agent": "cart_agent"
            }
        }

    # Increment quantity if product is already in cart.
    existing_item = next(
        (item for item in cart
         if str(item["product_id"]) == product_id),
        None
    )

    if existing_item:
        existing_item["quantity"] += 1
    else:
        cart.append({
            "product_id": product_id,
            "name": selected_product.get(
                "name",
                selected_product.get("title", "Product")
            ),
            "price": price,
            "quantity": 1,
            "image_url": selected_product.get("image_url", ""),
            "product_url": selected_product.get("product_url", "")
        })

    subtotal = sum(
        item["price"] * item["quantity"]
        for item in cart
    )

    item_count = sum(item["quantity"] for item in cart)

    return {
        "cart": cart,
        "response": {
            "message": "Product successfully added to your cart!",
            "cart": {
                "items": cart,
                "item_count": item_count,
                "subtotal": subtotal,
                "currency": "LKR"
            },
            "agent": "cart_agent"
        }
    }
