from pydantic import BaseModel, Field
from typing import Optional, Any

class DeliverySchema(BaseModel):
    recipient_name: str
    recipient_phone: str
    delivery_city: Optional[str]
    delivery_date: Optional[str]
    delivery_address: Optional[str]
    location_type: Optional[str]
    delivery_instructions: Optional[str]

