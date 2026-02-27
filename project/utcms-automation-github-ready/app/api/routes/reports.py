from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.automation.reporting import report_service
from app.core.security import require_sensitive_auth

router = APIRouter(prefix="/reports", tags=["گزارشات"])


@router.get(
    "/summary",
    summary="خلاصه آمار ربات",
    dependencies=[Depends(require_sensitive_auth)],
)
async def get_summary_report() -> Dict[str, Any]:
    """دریافت آمار کلی عملکرد ربات"""
    return await report_service.get_summary()


@router.get(
    "/daily",
    summary="گزارش روزانه فعالیت",
    dependencies=[Depends(require_sensitive_auth)],
)
async def get_daily_report() -> Dict[str, Any]:
    """دریافت گزارش تفکیکی روزانه (موفقیت/شکست)"""
    return await report_service.get_daily_report()


@router.get(
    "/operational",
    summary="شاخص‌های عملیاتی",
    dependencies=[Depends(require_sensitive_auth)],
)
async def get_operational_report() -> Dict[str, Any]:
    """دریافت شاخص‌های latency/error/mode برای پایش عملیاتی."""
    return await report_service.get_operational_report()
