from pydantic import BaseModel, Field
from typing import Dict, Any

class OrderCreate(BaseModel):
    client_id: int
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderResponse(BaseModel):
    order_id: int
    client_id: int
    product_id: int
    quantity: int
    status: str

class DemoResponse(BaseModel):
    mode: str
    execution_time_seconds: float
    result: Dict[str, Any]
