
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_groq import ChatGroq

from states.agent_state import AgentState
from prompts.delivery_agent_prompt import DELIVERY_AGENT_PROMPT
from utills.loggers import get_logger

# Change this import to the location of your existing MCP client.
from tools.mcp_servers.kapruka_mcp import McpClient


logger = get_logger("Delivery Agent")


# --------------------------------------------------
# LLM CONFIGURATION
# --------------------------------------------------

delivery_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=3000,
    reasoning_effort="low",
)


# --------------------------------------------------
# MCP TOOL CACHE
# --------------------------------------------------

_delivery_agent = None


async def get_delivery_agent():
    """
    Create and cache a LangChain agent with only delivery tools.
    """

    global _delivery_agent

    if _delivery_agent is not None:
        return _delivery_agent

    all_tools = await McpClient()

    required_tool_names = {
        "kapruka_list_delivery_cities",
        "kapruka_check_delivery",
    }

    delivery_tools = [
        tool
        for tool in all_tools
        if tool.name in required_tool_names
    ]

    available_names = {tool.name for tool in delivery_tools}
    missing_tools = required_tool_names - available_names

    if missing_tools:
        raise RuntimeError(
            f"Missing delivery MCP tools: {missing_tools}"
        )

    _delivery_agent = create_agent(
        model=delivery_llm,
        tools=delivery_tools,
        system_prompt=DELIVERY_AGENT_PROMPT,
    )

    logger.info("Delivery agent initialized.")

    return _delivery_agent


# --------------------------------------------------
# GENERAL HELPERS
# --------------------------------------------------

def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def parse_tool_content(content: Any) -> Any:
    """
    Convert a LangChain ToolMessage content value into Python data.
    """

    if isinstance(content, (dict, list)):
        return content

    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, dict) and block.get("text"):
                text_parts.append(block["text"])

        if text_parts:
            combined = "\n".join(text_parts)

            try:
                return json.loads(combined)
            except json.JSONDecodeError:
                return {"raw_response": combined}

    return {"raw_response": str(content)}


def unwrap_payload(data: Any) -> Any:
    """
    Unwrap common MCP response wrappers without discarding raw data.
    """

    if not isinstance(data, dict):
        return data

    for key in ("result", "data", "response"):
        value = data.get(key)

        if isinstance(value, (dict, list)):
            return value

    return data


def flatten_arguments(arguments: dict) -> dict:
    """
    Handle MCP tools whose arguments are wrapped in a params object.
    """

    if not isinstance(arguments, dict):
        return {}

    params = arguments.get("params")

    if isinstance(params, dict):
        return params

    return arguments


def find_value(data: Any, key: str) -> Any:
    """
    Find a field recursively in nested tool responses.
    """

    if isinstance(data, dict):

        if key in data:
            return data[key]

        for value in data.values():
            result = find_value(value, key)

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_value(item, key)

            if result is not None:
                return result

    return None


def extract_agent_tool_results(messages: list) -> list[dict]:
    """
    Pair agent tool calls with their corresponding ToolMessages.

    This allows Python to validate the actual tool responses rather
    than trusting the LLM's final natural-language answer.
    """

    calls_by_id = {}

    for message in messages:

        tool_calls = getattr(message, "tool_calls", None) or []

        for call in tool_calls:
            calls_by_id[call.get("id")] = {
                "name": call.get("name"),
                "args": flatten_arguments(call.get("args", {})),
            }

    results = []

    for message in messages:

        if not isinstance(message, ToolMessage):
            continue

        call = calls_by_id.get(message.tool_call_id, {})

        results.append({
            "name": call.get("name") or message.name,
            "args": call.get("args", {}),
            "result": unwrap_payload(
                parse_tool_content(message.content)
            ),
        })

    return results


# --------------------------------------------------
# INPUT VALIDATION
# --------------------------------------------------

def validate_delivery_inputs(
    cart: list,
    delivery_details: dict,
) -> str | None:

    if not cart:
        return "Your cart is empty. Please add products before checking delivery."

    required_fields = [
        "recipient_name",
        "recipient_phone",
        "address",
        "city",
        "delivery_date",
    ]

    for field in required_fields:

        if not normalize_text(delivery_details.get(field)):
            return (
                f"Please provide your delivery "
                f"{field.replace('_', ' ')}."
            )

    try:
        requested_date = date.fromisoformat(
            delivery_details["delivery_date"]
        )
    except (ValueError, TypeError):
        return "Please provide a valid delivery date in YYYY-MM-DD format."

    if requested_date < date.today():
        return "The requested delivery date is in the past."

    for item in cart:

        if not isinstance(item, dict):
            return "An item in your cart has invalid information."

        if not item.get("product_id"):
            return "A product in your cart has an invalid product ID."

        try:
            quantity = int(item.get("quantity", 0))
        except (ValueError, TypeError):
            return "A product in your cart has an invalid quantity."

        if quantity < 1 or quantity > 30:
            return "Cart quantities must be between 1 and 30."

    return None


# --------------------------------------------------
# TOOL EVIDENCE VALIDATION
# --------------------------------------------------

def validate_tool_evidence(
    tool_results: list[dict],
    cart: list,
) -> dict:
    """
    Verify that the agent called the required tools and that the
    responses establish delivery availability.

    Expected check calls:
      - One check per distinct product, with product_id.
      - One final full-cart check, without product_id.
    """

    city_results = [
        item for item in tool_results
        if item["name"] == "kapruka_list_delivery_cities"
    ]

    check_results = [
        item for item in tool_results
        if item["name"] == "kapruka_check_delivery"
    ]

    if not city_results:
        return {
            "valid": False,
            "error": "The destination city was not verified.",
        }

    if not check_results:
        return {
            "valid": False,
            "error": "Delivery availability was not checked.",
        }

    # Require the latest city lookup result to be interpretable.
    city_data = city_results[-1]["result"]

    if isinstance(city_data, dict) and city_data.get("isError"):
        return {
            "valid": False,
            "error": "The destination city lookup failed.",
        }

    distinct_product_ids = {
        str(item["product_id"]) for item in cart
    }

    product_results = {}
    full_cart_results = []

    for item in check_results:

        args = item.get("args", {})
        result = item.get("result")

        product_id = args.get("product_id")

        if product_id is not None:
            product_results[str(product_id)] = result
        else:
            full_cart_results.append(result)

    # Every distinct cart product needs its own eligibility check.
    missing_products = (
        distinct_product_ids - set(product_results.keys())
    )

    if missing_products:
        return {
            "valid": False,
            "error": (
                "Delivery eligibility was not checked for every "
                f"product: {', '.join(sorted(missing_products))}."
            ),
        }

    if not full_cart_results:
        return {
            "valid": False,
            "error": "The complete cart delivery fee was not checked.",
        }

    # Validate individual products.
    for product_id, result in product_results.items():

        if not isinstance(result, dict):
            return {
                "valid": False,
                "error": f"Could not verify product {product_id}.",
            }

        if result.get("item_deliverable") is False:
            return {
                "valid": False,
                "status": "unavailable",
                "error": (
                    f"Product {product_id} cannot be delivered "
                    "to the requested destination."
                ),
                "product_results": product_results,
            }

        if result.get("available") is False:
            return {
                "valid": False,
                "status": "unavailable",
                "error": (
                    f"Delivery is unavailable for product {product_id}."
                ),
                "product_results": product_results,
            }

        if result.get("item_deliverable") is not True:
            return {
                "valid": False,
                "error": (
                    f"The tool did not confirm delivery eligibility "
                    f"for product {product_id}."
                ),
            }

    # Use the final full-cart response.
    final_result = full_cart_results[-1]

    if not isinstance(final_result, dict):
        return {
            "valid": False,
            "error": "The complete cart delivery result is invalid.",
        }

    if final_result.get("available") is False:
        return {
            "valid": False,
            "status": "unavailable",
            "error": "Delivery is unavailable for the complete cart.",
            "final_result": final_result,
        }

    if final_result.get("available") is not True:
        return {
            "valid": False,
            "error": (
                "The complete cart delivery availability "
                "could not be confirmed."
            ),
        }

    return {
        "valid": True,
        "status": "validated",
        "product_results": product_results,
        "final_result": final_result,
    }


# --------------------------------------------------
# DELIVERY FEE
# --------------------------------------------------

def parse_delivery_fee(value: Any) -> float | None:
    if value is None:
        return None

    try:
        cleaned = re.sub(r"[^0-9.]", "", str(value).replace(",", ""))

        if not cleaned:
            return None

        fee = Decimal(cleaned)

        if not fee.is_finite() or fee < 0:
            return None

        return float(fee)

    except (InvalidOperation, ValueError, TypeError):
        return None


# --------------------------------------------------
# DELIVERY AGENT NODE
# --------------------------------------------------

async def delivery_agent(state: AgentState) -> dict:

    logger.info("Executing Delivery Agent...")

    cart = state.get("cart", [])
    delivery_details = state.get("delivery_details") or {}

    currency = state.get("currency", "LKR")
    gift_message = state.get("gift_message") or ""

    # --------------------------------------------------
    # 1. VALIDATE REQUIRED INPUTS
    # --------------------------------------------------

    validation_error = validate_delivery_inputs(
        cart,
        delivery_details,
    )

    if validation_error:

        logger.warning(
            "Delivery input validation failed: %s",
            validation_error,
        )

        return {
            "delivery_validated": False,
            "delivery_confirmed": False,
            "delivery_validation": None,
            "delivery_error": validation_error,
            "delivery_fee": None,
            "response": {
                "message": validation_error,
                "agent": "delivery_agent",
            },
        }

    # Build a safe cart representation for the agent.
    checkout_cart = [
        {
            "product_id": str(item["product_id"]),
            "quantity": int(item["quantity"]),
        }
        for item in cart
    ]

    context = {
        "cart": checkout_cart,
        "delivery_details": delivery_details,
        "currency": currency,
        "gift_message": gift_message,
    }

    # --------------------------------------------------
    # 2. RUN THE AGENT
    # --------------------------------------------------

    try:

        agent = await get_delivery_agent()

        result = await agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Validate delivery for the following order.\n\n"
                        f"{json.dumps(context, ensure_ascii=False, default=str)}\n\n"
                        "Follow your mandatory workflow. Verify the city, "
                        "check every distinct product, and perform one "
                        "final complete-cart delivery check. "
                        "Do not create an order."
                    ),
                }
            ]
        })

        messages = result.get("messages", [])

        tool_results = extract_agent_tool_results(messages)

        # --------------------------------------------------
        # 3. VERIFY ACTUAL TOOL RESPONSES
        # --------------------------------------------------

        evidence = validate_tool_evidence(
            tool_results,
            checkout_cart,
        )

        if not evidence["valid"]:

            error = evidence["error"]

            logger.warning(
                "Delivery evidence validation failed: %s",
                error,
            )

            return {
                "delivery_validated": False,
                "delivery_confirmed": False,
                "delivery_validation": {
                    "tool_results": tool_results,
                    "evidence": evidence,
                },
                "delivery_error": error,
                "delivery_fee": None,
                "response": {
                    "message": (
                        error
                        if evidence.get("status") == "unavailable"
                        else (
                            "I couldn't reliably verify delivery "
                            "availability. Please try again."
                        )
                    ),
                    "agent": "delivery_agent",
                },
            }

        # --------------------------------------------------
        # 4. EXTRACT TRUSTED FINAL RESULT
        # --------------------------------------------------

        final_result = evidence["final_result"]

        delivery_fee = parse_delivery_fee(
            final_result.get("delivery_fee")
        )

        economy = final_result.get("economy")
        perishable_warning = final_result.get("perishable_warning")

        # Use the city result and final MCP result as evidence.
        validation = {
            "city": delivery_details["city"],
            "delivery_date": delivery_details["delivery_date"],
            "available": True,
            "delivery_fee": delivery_fee,
            "currency": currency,
            "product_results": evidence["product_results"],
            "perishable_warning": perishable_warning,
            "economy": economy,
            "final_result": final_result,
        }

        # --------------------------------------------------
        # 5. HANDLE ECONOMY DELIVERY
        # --------------------------------------------------

        economy_forced = (
            isinstance(economy, dict)
            and economy.get("forced") is True
        )

        economy_optional = (
            isinstance(economy, dict)
            and economy.get("forced") is False
        )

        # Delivery is eligible, but the customer still needs to
        # explicitly accept the forced economy option.
        if economy_forced:

            message = (
                "Delivery is available, but Kapruka requires "
                "economy delivery for this order. "
                "Would you like to continue with economy delivery?"
            )

            return {
                "delivery_details": delivery_details,
                "delivery_validated": True,
                "delivery_confirmed": False,
                "delivery_validation": validation,
                "delivery_fee": delivery_fee,
                "delivery_type": "economy",
                "delivery_error": None,
                "response": {
                    "message": message,
                    "delivery": validation,
                    "requires_confirmation": True,
                    "agent": "delivery_agent",
                },
            }

        # Optional economy must not be selected automatically.
        if economy_optional:

            message = (
                "Delivery is available. An economy delivery option "
                "is also available. Would you like to use economy "
                "delivery or continue with standard delivery?"
            )

            return {
                "delivery_details": delivery_details,
                "delivery_validated": True,
                "delivery_confirmed": False,
                "delivery_validation": validation,
                "delivery_fee": delivery_fee,
                "delivery_type": None,
                "delivery_error": None,
                "response": {
                    "message": message,
                    "delivery": validation,
                    "requires_confirmation": True,
                    "agent": "delivery_agent",
                },
            }

        # --------------------------------------------------
        # 6. SUCCESSFUL DELIVERY VALIDATION
        # --------------------------------------------------

        message = (
            f"Delivery is available to {delivery_details['city']} "
            f"on {delivery_details['delivery_date']}."
        )

        if delivery_fee is not None:
            message += (
                f" The delivery fee is {currency} {delivery_fee:,.2f}."
            )

        if perishable_warning:
            message += f" Note: {perishable_warning}"

        logger.info("Delivery validation completed successfully.")

        return {
            "delivery_details": delivery_details,
            "delivery_validated": True,
            "delivery_confirmed": False,
            "delivery_validation": validation,
            "delivery_fee": delivery_fee,
            "delivery_type": "standard",
            "delivery_error": None,
            "response": {
                "message": message,
                "delivery": validation,
                "requires_confirmation": True,
                "agent": "delivery_agent",
            },
        }

    except Exception as exc:

        logger.exception(
            "Delivery Agent execution failed: %s",
            exc,
        )

        return {
            "delivery_validated": False,
            "delivery_confirmed": False,
            "delivery_validation": None,
            "delivery_error": (
                "Delivery verification failed. Please try again."
            ),
            "delivery_fee": None,
            "response": {
                "message": (
                    "I encountered an issue while checking delivery "
                    "availability. Please try again."
                ),
                "agent": "delivery_agent",
            },
        }
