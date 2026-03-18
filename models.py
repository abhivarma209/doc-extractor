from pydantic import BaseModel
from typing import Optional, Literal

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

class ExtractionRequest(BaseModel):
    document: str
    question: str

class ExtractionResponse(BaseModel):
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    items: list[LineItem]
    total_amount: float
    confidence: Literal["high", "medium", "low"]
    truncated: bool