from typing import TypedDict

class CartItem(TypedDict):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: str
    product_url: str