from pydantic import BaseModel, Field
from typing import Optional, Any

class DeliverySchema(BaseModel):
    delivery_city: Optional[str]
    delivery_date: Optional[str]
    delivery_address: Optional[str]
    location_type: Optional[str]
    delivery_instructions: Optional[str]
    delivery_type: Optional[str]
    delivery_check: Optional[dict[str, Any]]