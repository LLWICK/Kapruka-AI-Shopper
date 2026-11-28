
from typing import Any
from decimal import Decimal, InvalidOperation
import re

from states.agent_state import AgentState
from utills.loggers import get_logger


def _get_quantity(value: Any, default: int = 1) -> int:
    """Validate a requested cart quantity."""
    try:
        quantity = int(value)
        if quantity < 1 or quantity > 30:
            return default
        return quantity
    except (ValueError, TypeError):
        return default


def _parse_price(value: Any) -> Decimal | None:
    """Extract a valid non-negative price from trusted product data."""
    if value is None:
        return None

    try:
        # Handles values such as Rs. 1,500.00 and LKR 1,500.
        cleaned = re.sub(r"[^0-9.]", "", str(value).replace(",", ""))

        if not cleaned:
            return None

        price = Decimal(cleaned)

        if not price.is_finite() or price < 0:
            return None

        return price

    except (InvalidOperation, ValueError, TypeError):
        return None


def _build_cart_summary(cart: list, currency: str) -> dict:
    """Calculate cart totals."""
    subtotal = sum(
        Decimal(str(item["price"])) * int(item["quantity"])
        for item in cart
    )

    item_count = sum(int(item["quantity"]) for item in cart)

    return {
        "items": cart,
        "item_count": item_count,
        "subtotal": float(subtotal),
        "currency": currency,
    }


async def cart_agent(state: AgentState) -> dict:

    logger = get_logger("Cart Agent")
    logger.info("Executing Cart Agent...")

    cart = [dict(item) for item in state.get("cart", [])]

    cart_action = state.get("cart_action", "add")
    cart_quantity = state.get("cart_quantity", 1)
    currency = state.get("currency", "LKR")

    logger.info("Cart action: %s", cart_action)

    # --------------------------------------------------
    # 1. VIEW CART
    # --------------------------------------------------
    if cart_action == "view":

        summary = _build_cart_summary(cart, currency)

        if not cart:
            message = "Your cart is currently empty."
        else:
            message = "Here is your current cart."

        return {
            "response": {
                "message": message,
                "cart": summary,
                "agent": "cart_agent",
            }
        }

    # --------------------------------------------------
    # 2. VALIDATE CART ACTION
    # --------------------------------------------------
    if cart_action not in {"add", "remove", "update"}:
        return {
            "response": {
                "message": "I couldn't identify the requested cart operation.",
                "agent": "cart_agent",
            }
        }

    # --------------------------------------------------
    # 3. VALIDATE PRODUCT RESOLUTION
    # --------------------------------------------------
    resolution = state.get("product_resolution") or {}

    # Support both dictionaries and Pydantic models.
    if hasattr(resolution, "model_dump"):
        resolution = resolution.model_dump()

    if resolution.get("status") != "resolved":

        return {
            "response": {
                "message": (
                    resolution.get("clarification_question")
                    or resolution.get("reason")
                    or "Please specify which product you mean."
                ),
                "agent": "cart_agent",
            }
        }

    selected_product = state.get("selected_product")

    if not selected_product:
        return {
            "response": {
                "message": "I couldn't identify the requested product.",
                "agent": "cart_agent",
            }
        }

    product_id = (
        selected_product.get("id")
        or selected_product.get("product_id")
    )

    if not product_id:
        return {
            "response": {
                "message": "The selected product has an invalid product ID.",
                "agent": "cart_agent",
            }
        }

    product_id = str(product_id)

    # Find the product in the current cart.
    existing_item = next(
        (
            item for item in cart
            if str(item.get("product_id")) == product_id
        ),
        None,
    )

    # --------------------------------------------------
    # 4. REMOVE PRODUCT
    # --------------------------------------------------
    if cart_action == "remove":

        if not existing_item:
            return {
                "response": {
                    "message": "This product is not currently in your cart.",
                    "cart": _build_cart_summary(cart, currency),
                    "agent": "cart_agent",
                }
            }

        cart = [
            item for item in cart
            if str(item.get("product_id")) != product_id
        ]

        summary = _build_cart_summary(cart, currency)

        return {
            "cart": cart,
            "response": {
                "message": (
                    f"{existing_item.get('name', 'Product')} "
                    "has been removed from your cart."
                ),
                "cart": summary,
                "agent": "cart_agent",
            },
        }

    # --------------------------------------------------
    # 5. VALIDATE QUANTITY
    # --------------------------------------------------
    if cart_action == "add":
        quantity = _get_quantity(
            resolution.get("quantity", cart_quantity)
        )
    else:
        quantity = _get_quantity(cart_quantity, default=0)

        if quantity == 0:
            return {
                "response": {
                    "message": "Please provide a valid quantity between 1 and 30.",
                    "agent": "cart_agent",
                }
            }

    # --------------------------------------------------
    # 6. UPDATE PRODUCT QUANTITY
    # --------------------------------------------------
    if cart_action == "update":

        if not existing_item:
            return {
                "response": {
                    "message": "This product is not currently in your cart.",
                    "cart": _build_cart_summary(cart, currency),
                    "agent": "cart_agent",
                }
            }

        existing_item["quantity"] = quantity

        summary = _build_cart_summary(cart, currency)

        return {
            "cart": cart,
            "response": {
                "message": (
                    f"Updated {existing_item.get('name', 'product')} "
                    f"quantity to {quantity}."
                ),
                "cart": summary,
                "agent": "cart_agent",
            },
        }

    # --------------------------------------------------
    # 7. ADD PRODUCT
    # --------------------------------------------------
    price_value = selected_product.get("price")

    if price_value is None:
        price_value = selected_product.get("displayed_price")

    price = _parse_price(price_value)

    if price is None:
        return {
            "response": {
                "message": (
                    "I couldn't verify the price of this product. "
                    "Please check its product page before adding it."
                ),
                "agent": "cart_agent",
            }
        }

    product_name = (
        selected_product.get("name")
        or selected_product.get("title")
        or "Product"
    )

    if existing_item:
        existing_item["quantity"] = (
            int(existing_item["quantity"]) + quantity
        )
        existing_item["price"] = float(price)

    else:
        cart.append({
            "product_id": product_id,
            "name": product_name,
            "price": float(price),
            "quantity": quantity,
            "image_url": selected_product.get("image_url", ""),
            "product_url": selected_product.get("product_url", ""),
        })

    summary = _build_cart_summary(cart, currency)

    return {
        "cart": cart,
        "response": {
            "message": (
                f"Successfully added {quantity} x {product_name} "
                "to your cart!"
            ),
            "cart": summary,
            "agent": "cart_agent",
        },
    }
