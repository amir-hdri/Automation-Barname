import unittest
from unittest.mock import patch
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, select
from app.automation.reporting import ReportService
from app.models import BotStats

class TestReportingPersistence(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use in-memory SQLite for testing
        self.test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

        # Create tables
        async with self.test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Patch the engine in the reporting module
        self.patcher = patch("app.automation.reporting.engine", self.test_engine)
        self.mock_engine = self.patcher.start()

        self.service = ReportService()

    async def asyncTearDown(self):
        self.patcher.stop()
        await self.test_engine.dispose()

    async def test_record_and_persist(self):
        """Test that statistics are recorded and persisted to the database."""
        # Record stats
        await self.service.record_request()
        await self.service.record_success()
        await self.service.record_map_usage("google_maps")
        await self.service.record_map_usage("openlayers")

        # Verify via service summary
        summary = await self.service.get_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertEqual(summary["successful_waybills"], 1)
        self.assertEqual(summary["map_usage_distribution"]["google_maps"], 1)
        self.assertEqual(summary["map_usage_distribution"]["openlayers"], 1)
        self.assertEqual(summary["map_usage_distribution"]["leaflet"], 0)

        # Verify DB directly to ensure persistence
        async with AsyncSession(self.test_engine) as session:
            result = await session.execute(select(BotStats))
            stats = result.scalars().first()
            self.assertIsNotNone(stats)
            self.assertEqual(stats.total_requests, 1)
            self.assertEqual(stats.successful_waybills, 1)
            self.assertEqual(stats.map_google, 1)
            self.assertEqual(stats.map_openlayers, 1)
            self.assertEqual(stats.report_date, date.today())

    async def test_daily_report(self):
        """Test that daily reports are correctly generated."""
        await self.service.record_failure()
        await self.service.record_failure()

        daily = await self.service.get_daily_report()
        today = date.today().isoformat()

        self.assertIn(today, daily)
        self.assertEqual(daily[today]["fail"], 2)
        self.assertEqual(daily[today]["success"], 0)

    async def test_calculate_rate(self):
        """Test success rate calculation logic."""
        rate = self.service._calculate_rate(5, 5)
        self.assertEqual(rate, "50.0%")

        rate_zero = self.service._calculate_rate(0, 0)
        self.assertEqual(rate_zero, "0%")
