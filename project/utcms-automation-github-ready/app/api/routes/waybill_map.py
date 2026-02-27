"""مسیرهای API برای عملیات بارنامه مبتنی بر نقشه"""

import math
from typing import Optional

from fastapi import APIRouter, Depends

from app.automation.reporting import report_service
from app.automation.traffic_control import waybill_traffic_controller
from app.core.config import utcms_config
from app.core.security import require_sensitive_auth
from app.schemas.waybill import (
    CargoModel,
    FinancialModel,
    GeoCoordinateModel,
    LocationModel,
    OperationMode,
    ReceiverModel,
    SenderModel,
    VehicleModel,
    WaybillMapRequest,
)
from app.services.waybill_service import waybill_service

router = APIRouter(prefix="/waybill", tags=["waybill-map"])


@router.post("/create-with-map", dependencies=[Depends(require_sensitive_auth)])
async def create_waybill_with_map(request: WaybillMapRequest):
    """ایجاد بارنامه با حالت safe/full."""
    return await waybill_service.create_waybill_with_map(request)


@router.post("/detect-map", dependencies=[Depends(require_sensitive_auth)])
async def detect_map(session_id: Optional[str] = None):
    """تشخیص وجود نقشه و نوع آن در صفحه."""
    return await waybill_service.detect_map(session_id=session_id)


@router.get("/traffic-status", dependencies=[Depends(require_sensitive_auth)])
async def get_traffic_status():
    """نمایش وضعیت صف و محدودسازی بار برای پایش عملیاتی."""
    snapshot = waybill_traffic_controller.snapshot()
    mode_counters = report_service.get_mode_counters()

    return {
        "active_requests": snapshot.active_requests,
        "queued_requests": snapshot.queued_requests,
        "next_allowed_in_seconds": round(snapshot.next_allowed_in_seconds, 2),
        "blocked_for_seconds": round(snapshot.blocked_for_seconds, 2),
        "max_concurrent": utcms_config.WAYBILL_MAX_CONCURRENT,
        "min_gap_seconds": utcms_config.WAYBILL_MIN_GAP_SECONDS,
        "active_by_mode": {
            "safe": snapshot.active_safe,
            "full": snapshot.active_full,
        },
        "queued_by_mode": {
            "safe": snapshot.queued_safe,
            "full": snapshot.queued_full,
        },
        "mode_counters": mode_counters,
    }


@router.post("/calculate-route")
async def calculate_route(origin: GeoCoordinateModel, destination: GeoCoordinateModel):
    """محاسبه مسیر بین دو مختصات جغرافیایی."""
    earth_radius_km = 6371

    lat1 = math.radians(origin.lat)
    lat2 = math.radians(destination.lat)
    dlat = math.radians(destination.lat - origin.lat)
    dlon = math.radians(destination.lng - origin.lng)

    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(lat1) * math.cos(
        lat2
    ) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius_km * c

    duration_min = (distance / 60) * 60

    return {
        "distance_km": round(distance, 2),
        "duration_min": round(duration_min),
        "origin": origin.model_dump(),
        "destination": destination.model_dump(),
        "method": "haversine",
    }


__all__ = [
    "GeoCoordinateModel",
    "LocationModel",
    "SenderModel",
    "ReceiverModel",
    "CargoModel",
    "VehicleModel",
    "FinancialModel",
    "OperationMode",
    "WaybillMapRequest",
    "create_waybill_with_map",
]
