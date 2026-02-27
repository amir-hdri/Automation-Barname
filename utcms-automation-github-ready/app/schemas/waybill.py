from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class OperationMode(str, Enum):
    SAFE = "safe"
    FULL = "full"


class GeoCoordinateModel(BaseModel):
    lat: float = Field(..., description="عرض جغرافیایی")
    lng: float = Field(..., description="طول جغرافیایی")


class LocationModel(BaseModel):
    province: str
    city: str
    district: Optional[str] = None
    address: str
    coordinates: Optional[GeoCoordinateModel] = None


class SenderModel(BaseModel):
    name: str = Field(..., description="نام فرستنده")
    phone: str = Field(..., description="تلفن فرستنده")
    address: str = Field(..., description="آدرس فرستنده")
    national_code: str = Field(..., description="کد ملی فرستنده")


class ReceiverModel(BaseModel):
    name: str = Field(..., description="نام گیرنده")
    phone: str = Field(..., description="تلفن گیرنده")
    address: str = Field(..., description="آدرس گیرنده")


class CargoModel(BaseModel):
    type: Optional[str] = Field(None, description="نوع کالا")
    weight: Union[str, int, float] = Field(..., description="وزن کالا")
    count: Union[str, int] = Field(default="1", description="تعداد کالا")
    description: Optional[str] = Field(None, description="توضیحات کالا")


class VehicleModel(BaseModel):
    driver_national_code: Optional[str] = Field(None, description="کد ملی راننده")
    driver_phone: Optional[str] = Field(None, description="تلفن راننده")
    plate: Optional[str] = Field(None, description="پلاک خودرو")
    type: Optional[str] = Field(None, description="نوع خودرو")


class FinancialModel(BaseModel):
    cost: Optional[Union[str, int, float]] = Field(None, description="هزینه حمل")
    payment_method: Optional[str] = Field(None, description="روش پرداخت")


class WaybillMapRequest(BaseModel):
    session_id: Optional[str] = None
    operation_mode: OperationMode = Field(default=OperationMode.SAFE)
    sender: SenderModel
    receiver: ReceiverModel
    origin: LocationModel
    destination: LocationModel
    cargo: CargoModel
    vehicle: VehicleModel
    financial: FinancialModel
