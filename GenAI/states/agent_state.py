from __future__ import annotations
 
from typing import Annotated, Literal, Optional, Any
from typing_extensions import TypedDict
 
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, field_validator
from states.search_structure import ProductSearchResponse
from states.product_schema import Product
from states.cartItem_Structure import CartItem
from states.delivery_structure import DeliverySchema
from states.ProductResolution_Structure import ProductResolution

 
 
# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------
 
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    query: str

    response: dict


    #product search
    search_agent_output: ProductSearchResponse
    last_search_results: list[Product]

    intent: str

    next_agent: str

    # Product selection
    selected_product: dict
    selected_product_id: str

    #cart
    cart: list  [CartItem]
    cart_action: Optional[
        Literal["add", "remove", "update", "view"]
    ]
    cart_quantity: Optional[int]

    #delivery information
    delivery_details: DeliverySchema
    delivery_validated: bool
    delivery_validation: Optional[dict[str, Any]]
    delivery_error: Optional[str]
    delivery_fee: Optional[float]
    delivery_type: Optional[Literal["standard", "economy"]]
    delivery_confirmed: bool


    #sender information
    recipient: Optional[dict[str, Any]]
    sender: Optional[dict[str, Any]]
    gift_message: Optional[str]
    currency: str

    # Checkout
    checkout_confirmed: bool
    checkout_result: Optional[dict[str, Any]]

    #product resolution

    product_resolution: ProductResolution



    

    ref_map: dict                             # "3" -> product dict; a ref always means the same product
                          # [{ref, product_id, name, price, currency, quantity, icing_text}]
    checkout: dict                            # flat dict of details collected so far
    delivery_ok: bool                         # city+date verified for the CURRENT cart + details
    awaiting_confirmation: bool               # summary shown, waiting for an explicit "yes"
    delivery_fee: Optional[float]
    pending_order: Optional[dict]             # checkout_url / order_ref / expires_at after create_order
    card_url: Optional[str]                   # options-card image for the last search
    shown: list                               # products shown this search turn, each with its `ref`
    reply: str   

