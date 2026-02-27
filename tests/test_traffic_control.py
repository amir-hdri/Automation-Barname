import unittest

from app.automation.traffic_control import WaybillTrafficController


class TestWaybillTrafficController(unittest.IsolatedAsyncioTestCase):
    async def test_slot_tracks_active_requests(self):
        controller = WaybillTrafficController()

        before = controller.snapshot()
        self.assertEqual(before.active_requests, 0)

        async with controller.slot():
            during = controller.snapshot()
            self.assertEqual(during.active_requests, 1)

        after = controller.snapshot()
        self.assertEqual(after.active_requests, 0)

    async def test_mark_temporary_block_sets_backoff(self):
        controller = WaybillTrafficController()
        await controller.mark_temporary_block(multiplier=1.0)
        snapshot = controller.snapshot()
        self.assertGreaterEqual(snapshot.blocked_for_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
