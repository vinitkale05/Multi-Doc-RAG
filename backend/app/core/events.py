import asyncio
from typing import Dict, Set, AsyncGenerator
import json
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """In-memory pub-sub event bus for streaming document ingestion events via SSE."""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def subscribe(self, channel: str) -> asyncio.Queue:
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        queue = asyncio.Queue()
        self._subscribers[channel].add(queue)
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        if channel in self._subscribers:
            self._subscribers[channel].discard(queue)
            if not self._subscribers[channel]:
                del self._subscribers[channel]

    async def publish(self, channel: str, data: dict):
        if channel in self._subscribers:
            msg = json.dumps(data)
            for queue in list(self._subscribers[channel]):
                try:
                    await queue.put(msg)
                except Exception as e:
                    logger.warning(f"Error publishing to queue on channel {channel}: {e}")

    async def sse_stream(self, channel: str) -> AsyncGenerator[str, None]:
        queue = self.subscribe(channel)
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
                parsed = json.loads(data)
                # Terminate stream on terminal states
                if parsed.get("status") in ["READY", "FAILED"]:
                    break
        finally:
            self.unsubscribe(channel, queue)


event_bus = EventBus()
