import asyncio
import json
import logging
from typing import AsyncGenerator

# Deferred import to avoid hard dependency at module level if installed without extra
try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger(__name__)

class WebSocketConnection:
    """Class representing a persistent WebSocket connection for receiving events."""

    def __init__(self, url: str) -> None:
        if websockets is None:
            raise ImportError(
                "The 'websockets' library is required for WebSocket support. "
                "Please install it using 'pip install videodb[websockets]' or 'pip install websockets'."
            )
        self.url = url
        self._connection = None
        self.connection_id = None

    async def connect(self) -> "WebSocketConnection":
        """Establish the WebSocket connection."""
        logger.debug(f"Connecting to WebSocket URL: {self.url}")
        self._connection = await websockets.connect(self.url)
        
        # Expect the first message to be the connection init containing the ID
        try:
            init_msg = await self._connection.recv()
            data = json.loads(init_msg)
            self.connection_id = data.get("connection_id")
            logger.info(f"WebSocket connected with ID: {self.connection_id}")
        except Exception as e:
            logger.error(f"Failed to receive initialization message: {e}")
            await self.close()
            raise e
            
        return self

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def receive(self) -> AsyncGenerator[dict, None]:
        """Async generator that yields received messages."""
        if not self._connection:
            raise ConnectionError("WebSocket is not connected. Call connect() first.")
            
        async for message in self._connection:
            try:
                yield json.loads(message)
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message: {message}")
                yield {"raw": message}

    async def send(self, message: dict) -> None:
        """Send a message over the WebSocket."""
        if not self._connection:
            raise ConnectionError("WebSocket is not connected.")
        await self._connection.send(json.dumps(message))

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
