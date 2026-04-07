from pydantic import BaseModel


class WarehouseResponse(BaseModel):
    id: int
    code: str
    name: str
    address: str | None
    inn: str | None
    kpp: str | None
    is_active: bool


class CreateWarehouseRequest(BaseModel):
    code: str
    name: str
    address: str | None = None
    inn: str | None = None
    kpp: str | None = None


class UpdateWarehouseRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    address: str | None = None
    inn: str | None = None
    kpp: str | None = None
    is_active: bool | None = None
