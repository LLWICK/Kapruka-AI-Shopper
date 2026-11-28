from pydantic import BaseModel
from typing import Literal


class SupervisorOutput(BaseModel):
    intent: Literal[
        "search",
        "details",
        "cart",
        "checkout",
        "track",
        "chat"
    ]

    cart_action: Literal[
        "add",
        "remove",
        "update",
        "view"
    ] | None = None