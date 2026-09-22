from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from typing import Optional, List

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    reserved_stock: int = Field(0, ge=0)

    @model_validator(mode="after")
    def check_reserved_stock(self) -> "ProductCreate":
        if self.reserved_stock > self.stock:
            raise ValueError("El stock reservado no puede superar al stock total.")
        return self

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    reserved_stock: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def check_reserved_stock(self) -> "ProductUpdate":
        if self.stock is not None and self.reserved_stock is not None:
            if self.reserved_stock > self.stock:
                raise ValueError("El stock reservado no puede superar al stock total.")
        return self

class ProductRead(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int
    reserved_stock: int

class PaginatedProductResponse(BaseModel):
    items: List[ProductRead]
    total: int
