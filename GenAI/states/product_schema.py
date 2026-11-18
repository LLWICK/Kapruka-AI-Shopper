from pydantic import BaseModel, Field
from typing import Optional


class Product(BaseModel):
    id: str                           # needed later for cart / create_order
    name: str
    price: int
    currency: str = "LKR"
    in_stock: bool
    stock_level: Optional[str] = None
    summary: str
    product_url: str
    image_url: str