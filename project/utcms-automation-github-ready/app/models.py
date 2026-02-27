from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field


class BotStats(SQLModel, table=True):
    """مدل آمار روزانه عملکرد ربات"""

    id: Optional[int] = Field(default=None, primary_key=True)
    report_date: date = Field(
        index=True, unique=True
    )  # Using report_date to avoid conflict with 'date' type

    # آمار کلی
    total_requests: int = Field(default=0)
    successful_waybills: int = Field(default=0)
    failed_attempts: int = Field(default=0)

    # آمار استفاده از نقشه
    map_google: int = Field(default=0)
    map_openlayers: int = Field(default=0)
    map_leaflet: int = Field(default=0)
    map_mapbox: int = Field(default=0)
    map_unknown: int = Field(default=0)
    map_none: int = Field(default=0)
