
from pydantic import BaseModel, Field
from typing import Optional


class Product(BaseModel):
    id: str                                   # needed later for cart / create_order
    name: str
    price: int
    currency: str = "LKR"
    in_stock: bool
    stock_level: Optional[str] = None
    product_url: str
    image_url: Optional[str] = None

class ProductSearchResponse(BaseModel):
    query: str
    products: list[Product]
    total_results: int
    message: Optional[str] = None