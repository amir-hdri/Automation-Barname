import unittest
import asyncio
import uuid
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add app to path
sys.path.append(os.getcwd())

from app.automation.browser import BrowserManager

class TestBrowserSecurity(unittest.IsolatedAsyncioTestCase):
    async def test_secure_context_creation(self):
        """Test that contexts are created with secure, unique session IDs"""
        manager = BrowserManager()
        # Mock browser and context
        manager.browser = AsyncMock()
        mock_context = AsyncMock()
        manager.browser.new_context.return_value = mock_context

        # Create first context
        session_id_1, context_1 = await manager.create_context()

        # Verify return type
        self.assertIsInstance(session_id_1, str)
        self.assertEqual(context_1, mock_context)

        # Verify it's a valid UUID
        try:
            uuid_obj = uuid.UUID(session_id_1, version=4)
        except ValueError:
            self.fail("session_id is not a valid UUIDv4")

        # Verify storage
        self.assertIn(session_id_1, manager._contexts)
        self.assertEqual(manager._contexts[session_id_1], context_1)

        # Create second context
        session_id_2, context_2 = await manager.create_context()

        # Verify uniqueness
        self.assertNotEqual(session_id_1, session_id_2)
        self.assertIn(session_id_2, manager._contexts)

        # Verify close_context
        await manager.close_context(session_id_1)
        self.assertNotIn(session_id_1, manager._contexts)
        self.assertIn(session_id_2, manager._contexts)

        mock_context.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
