from __future__ import annotations
 
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
 
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, field_validator
from states.search_structure import ProductSearchResponse
 
 
# ---------------------------------------------------------------------------
# Pydantic models — mirror Kapruka's own tool schemas so validation happens
# on our side before we ever call kapruka_create_order.
# ---------------------------------------------------------------------------
 
class CartItem(BaseModel):
    product_id: str = Field(..., min_length=3, max_length=80)
    quantity: int = Field(default=1, ge=1, le=99)
    icing_text: Optional[str] = Field(default=None, max_length=120)
 
 
class Recipient(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    phone: str = Field(..., min_length=7, max_length=30)
 
    @field_validator("phone")
    @classmethod
    def looks_like_sl_phone(cls, v: str) -> str:
        digits = v.replace(" ", "").replace("-", "")
        if not (digits.startswith("+94") or digits.startswith("0")):
            raise ValueError("Phone must be E.164 (+9477...) or local (077...) format")
        return digits
 
 
class Delivery(BaseModel):
    address: str = Field(..., min_length=3, max_length=250)
    city: str = Field(..., min_length=2, max_length=100)
    location_type: Literal["house", "apartment", "office", "other"] = "house"
    date: str  # YYYY-MM-DD — validate via kapruka_check_delivery, not regex, since
    # feasibility (not just format) is what actually matters here.
    instructions: Optional[str] = Field(default=None, max_length=250)
 
 
class Sender(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    anonymous: bool = False
 
 
class CheckoutDraft(BaseModel):
    """Accumulates checkout fields across turns. Nothing here is sent to
    Kapruka until `is_complete()` is true and delivery has been confirmed
    feasible."""
 
    recipient: Optional[Recipient] = None
    delivery: Optional[Delivery] = None
    sender: Optional[Sender] = None
    gift_message: Optional[str] = Field(default=None, max_length=300)
    currency: str = "LKR"
    delivery_confirmed: bool = False  # set True only after kapruka_check_delivery
    # returns available=True for this exact city+date
 
    def is_complete(self) -> bool:
        return bool(self.recipient and self.delivery and self.sender)
 
    def missing_fields(self) -> list[str]:
        missing = []
        if not self.recipient:
            missing.append("recipient")
        if not self.delivery:
            missing.append("delivery")
        if not self.sender:
            missing.append("sender")
        return missing
 
 
# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------
 
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    query: str

    response: dict

    search_agent_output: ProductSearchResponse

    intent: str

    next_agent: str

    ref_map: dict                             # "3" -> product dict; a ref always means the same product
    cart: list                                # [{ref, product_id, name, price, currency, quantity, icing_text}]
    checkout: dict                            # flat dict of details collected so far
    delivery_ok: bool                         # city+date verified for the CURRENT cart + details
    awaiting_confirmation: bool               # summary shown, waiting for an explicit "yes"
    delivery_fee: Optional[float]
    pending_order: Optional[dict]             # checkout_url / order_ref / expires_at after create_order
    card_url: Optional[str]                   # options-card image for the last search
    shown: list                               # products shown this search turn, each with its `ref`
    reply: str   


 
    
 
 
""" def new_state() -> AgentState:
    return AgentState(
        messages=[],
        cart=[],
        checkout=CheckoutDraft(),
        last_search_results=[],
        ref_counter=0,
        pending_order=None,
        next_step="search",
    ) """