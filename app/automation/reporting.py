"""سرویس گزارش‌دهی و آمار"""

import asyncio
from collections import deque
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import utcms_config
from app.core.database import engine
from app.models import BotStats


class ReportService:
    """سرویس جمع‌آوری و ارائه گزارش‌های عملکرد با ذخیره‌سازی پایدار"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._op_lock = asyncio.Lock()
        self._latency_samples = deque(maxlen=max(100, utcms_config.LATENCY_SAMPLE_MAX))
        self._mode_counters = {
            "safe": {"requests": 0, "success": 0, "failure": 0},
            "full": {"requests": 0, "success": 0, "failure": 0},
        }
        self._error_categories = {
            "auth": 0,
            "map": 0,
            "captcha": 0,
            "network": 0,
            "form": 0,
            "unknown": 0,
        }

    async def _get_today_stats(self, session: AsyncSession) -> BotStats:
        today = date.today()
        statement = select(BotStats).where(BotStats.report_date == today)
        result = await session.execute(statement)
        stats = result.scalars().first()

        if not stats:
            stats = BotStats(report_date=today)
            session.add(stats)

        return stats

    async def _update_today_stats(self, updater) -> None:
        today = date.today()
        async with self._lock:
            async with AsyncSession(engine) as session:
                stats = await self._get_today_stats(session)
                updater(stats)
                session.add(stats)
                try:
                    await session.commit()
                    return
                except IntegrityError:
                    await session.rollback()

                statement = select(BotStats).where(BotStats.report_date == today)
                result = await session.execute(statement)
                existing_stats = result.scalars().first()
                if not existing_stats:
                    raise

                updater(existing_stats)
                session.add(existing_stats)
                await session.commit()

    async def _record_mode_event(
        self,
        mode: str,
        event: str,
        latency_ms: Optional[float] = None,
        category: Optional[str] = None,
    ) -> None:
        normalized_mode = "full" if mode == "full" else "safe"

        async with self._op_lock:
            if event in self._mode_counters[normalized_mode]:
                self._mode_counters[normalized_mode][event] += 1

            if latency_ms is not None:
                self._latency_samples.append(float(latency_ms))

            if category:
                normalized_category = category if category in self._error_categories else "unknown"
                self._error_categories[normalized_category] += 1

    async def record_request(self, mode: str = "safe"):
        await self._record_mode_event(mode=mode, event="requests")
        await self._update_today_stats(lambda stats: setattr(stats, "total_requests", stats.total_requests + 1))

    async def record_success(self, mode: str = "safe", latency_ms: Optional[float] = None):
        await self._record_mode_event(mode=mode, event="success", latency_ms=latency_ms)
        await self._update_today_stats(
            lambda stats: setattr(stats, "successful_waybills", stats.successful_waybills + 1)
        )

    async def record_failure(self, mode: str = "safe", category: str = "unknown"):
        await self._record_mode_event(mode=mode, event="failure", category=category)
        await self._update_today_stats(
            lambda stats: setattr(stats, "failed_attempts", stats.failed_attempts + 1)
        )

    async def record_map_usage(self, map_type: str):
        def _updater(stats: BotStats):
            if map_type == "google_maps":
                stats.map_google += 1
            elif map_type == "openlayers":
                stats.map_openlayers += 1
            elif map_type == "leaflet":
                stats.map_leaflet += 1
            elif map_type == "mapbox":
                stats.map_mapbox += 1
            elif map_type == "none":
                stats.map_none += 1
            else:
                stats.map_unknown += 1

        await self._update_today_stats(_updater)

    async def get_summary(self) -> Dict[str, Any]:
        async with AsyncSession(engine) as session:
            statement = select(BotStats)
            result = await session.execute(statement)
            all_stats = result.scalars().all()

            total_requests = sum(s.total_requests for s in all_stats)
            successful_waybills = sum(s.successful_waybills for s in all_stats)
            failed_attempts = sum(s.failed_attempts for s in all_stats)

            map_usage = {
                "google_maps": sum(s.map_google for s in all_stats),
                "openlayers": sum(s.map_openlayers for s in all_stats),
                "leaflet": sum(s.map_leaflet for s in all_stats),
                "mapbox": sum(s.map_mapbox for s in all_stats),
                "unknown": sum(s.map_unknown for s in all_stats),
                "none": sum(s.map_none for s in all_stats),
            }

            return {
                "total_requests": total_requests,
                "successful_waybills": successful_waybills,
                "failed_attempts": failed_attempts,
                "success_rate": self._calculate_rate(successful_waybills, failed_attempts),
                "map_usage_distribution": map_usage,
            }

    async def get_daily_report(self) -> Dict[str, Any]:
        async with AsyncSession(engine) as session:
            statement = select(BotStats).order_by(BotStats.report_date)
            result = await session.execute(statement)
            all_stats = result.scalars().all()

            daily_stats = {}
            for stat in all_stats:
                day_str = stat.report_date.isoformat()
                daily_stats[day_str] = {
                    "success": stat.successful_waybills,
                    "fail": stat.failed_attempts,
                }
            return daily_stats

    async def get_operational_report(self) -> Dict[str, Any]:
        async with self._op_lock:
            latencies = list(self._latency_samples)
            mode_counters = {
                mode: values.copy()
                for mode, values in self._mode_counters.items()
            }
            error_categories = self._error_categories.copy()

        return {
            "latency_ms": {
                "count": len(latencies),
                "p50": self._percentile(latencies, 50),
                "p95": self._percentile(latencies, 95),
                "max": round(max(latencies), 2) if latencies else 0.0,
            },
            "mode_counters": mode_counters,
            "error_categories": error_categories,
        }

    def get_mode_counters(self) -> Dict[str, Dict[str, int]]:
        return {
            mode: values.copy()
            for mode, values in self._mode_counters.items()
        }

    def _calculate_rate(self, success: int, total_failed: int) -> str:
        total = success + total_failed
        if total == 0:
            return "0%"
        rate = (success / total) * 100
        return f"{rate:.1f}%"

    @staticmethod
    def _percentile(samples: list[float], percentile: int) -> float:
        if not samples:
            return 0.0

        sorted_values = sorted(samples)
        index = int(round((percentile / 100) * (len(sorted_values) - 1)))
        index = min(max(index, 0), len(sorted_values) - 1)
        return round(sorted_values[index], 2)


report_service = ReportService()
