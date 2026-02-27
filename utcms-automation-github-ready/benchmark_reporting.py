
import asyncio
import time
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, select
from app.automation.reporting import ReportService
from app.models import BotStats
from unittest.mock import patch

async def run_benchmark():
    # Setup in-memory DB
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Patch engine
    patcher = patch("app.automation.reporting.engine", test_engine)
    patcher.start()

    service = ReportService()

    # Populate DB with a significant number of records
    # Note: BotStats has report_date as unique, so we can't have multiple rows effectively for the same day
    # However, the current code sums up ALL BotStats rows.
    # To benchmark this properly, we need multiple BotStats rows.
    # We will simulate multiple days of data.

    num_days = 1000
    print(f"Populating DB with {num_days} days of stats...")

    async with AsyncSession(test_engine) as session:
        for i in range(num_days):
            stats = BotStats(
                report_date=date.fromordinal(date.today().toordinal() - i),
                total_requests=100 + i,
                successful_waybills=50 + i,
                failed_attempts=50,
                map_google=10,
                map_openlayers=10,
                map_leaflet=10,
                map_mapbox=10,
                map_unknown=5,
                map_none=5
            )
            session.add(stats)
        await session.commit()

    print("Starting benchmark for get_summary()...")
    start_time = time.time()
    iterations = 100
    for _ in range(iterations):
        await service.get_summary()
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Average time per call: {avg_time:.6f} seconds")
    print(f"Total time for {iterations} calls: {end_time - start_time:.4f} seconds")

    patcher.stop()
    await test_engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
