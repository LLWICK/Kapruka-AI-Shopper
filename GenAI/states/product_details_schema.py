from pydantic import BaseModel, Field
from typing import Optional
from states.product_schema import Product

class Product_details(BaseModel):
    product_id: str
    details: str

class DetailsAgentOutput(BaseModel):
    message: str
    referenced_product_ids: list[str] = Field(default_factory=list)
    information_sources: list[str] = Field(default_factory=list)