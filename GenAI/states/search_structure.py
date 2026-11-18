
from pydantic import BaseModel, Field
from typing import Optional
from states.product_schema import Product



class ProductSearchResponse(BaseModel):
    query: str
    products: list[Product]
    total_results: int
    message: Optional[str] = None