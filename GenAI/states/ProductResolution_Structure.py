from typing import Optional, Literal
from pydantic import BaseModel, Field


class ProductResolution(BaseModel):
    status: Literal["resolved", "ambiguous", "not_found"] = Field(
        description="Whether the requested product was identified."
    )

    product_id: Optional[str] = Field(
        default=None,
        description="Exact ID of the matching candidate product."
    )

    quantity: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Quantity requested by the customer."
    )

    reason: str = Field(
        description="Short explanation of the resolution."
    )

    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask if the product reference is ambiguous."
    )