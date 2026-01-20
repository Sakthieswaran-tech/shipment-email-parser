from typing import Optional
from pydantic import BaseModel
from pydantic import field_validator
class Shipment(BaseModel):
    id: str
    product_line: str
    origin_port_code: Optional[str] = None
    origin_port_name: Optional[str] = None
    destination_port_code: Optional[str] = None
    destination_port_name: Optional[str] = None
    incoterm: Optional[str] = None
    cargo_weight_kg: Optional[float] = None
    cargo_cbm: Optional[float] = None
    is_dangerous: Optional[bool] = False

    @field_validator("origin_port_code", "destination_port_code")
    def validate_port_code(cls, v):
        if v is None:
            return None
        # if len(v) != 5 or not v.isalpha():
        #     raise ValueError("port code must be 5 letters")
        return v.upper()

    @field_validator("incoterm")
    def validate_incoterm(cls, v):
        if v is None:
            return None
        v = v.upper()
        if v not in ["FOB", "CIF", "CFR", "EXW", "DDP", "DAP", "FCA", "CPT", "CIP", "DPU"]:
            return "FOB"   # fallback rule
        return v

    @field_validator("cargo_weight_kg", "cargo_cbm")
    def validate_numbers(cls, v):
        if v is None:
            return None
        if v < 0:
            raise ValueError("must be positive")
        return round(float(v), 2)

