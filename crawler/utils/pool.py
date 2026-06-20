import asyncio
import aiofiles
import json
from typing import Set, Optional, List

from config import PoolConfig


class Pool:
    def __init__(self, config: PoolConfig):
        self.pool: Set[int] = set()
        self.save_frequency = config.save_frequency
        self.steps_since_last_save = 0
        self.file = config.file

        self._lock = asyncio.Lock()
        self._save_task: Optional[asyncio.Task] = None
        self._running = False
        self._dirty = False

    async def _load(self):
        if not self.file.exists():
            async with aiofiles.open(self.file, "w", encoding="utf-8") as f:
                await f.write(json.dumps([], ensure_ascii=False, indent=4))
            return

        async with aiofiles.open(self.file, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            self.pool.update(data)

    async def start_background_save(self):
        if self._running:
            return

        self._running = True
        self._save_task = asyncio.create_task(self._background_save_loop())

    async def _background_save_loop(self):
        while self._running:
            await asyncio.sleep(5)

            if self._dirty:
                async with self._lock:
                    await self._save()
                    self._dirty = False

    async def _save(self):
        data_to_save = list(self.pool)
        async with aiofiles.open(self.file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data_to_save, ensure_ascii=False, indent=4))

    async def save(self):
        async with self._lock:
            await self._save()
            self._dirty = False

    def __len__(self):
        return len(self.pool)

    async def next(self) -> int:
        async with self._lock:
            if not self.pool:
                raise ValueError("Pool is empty")

            result = self.pool.pop()
            self.steps_since_last_save += 1

            if self.steps_since_last_save >= self.save_frequency:
                self._dirty = True
                self.steps_since_last_save = 0

            return result

    async def update(self, extend_queue: List[int]):
        async with self._lock:
            if not extend_queue:
                return

            self.pool.update(extend_queue)
            self.steps_since_last_save += 1

            if self.steps_since_last_save >= self.save_frequency:
                self._dirty = True
                self.steps_since_last_save = 0

    async def close(self):
        self._running = False

        if self._save_task and not self._save_task.done():
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

        await self.save()

    async def __aenter__(self):
        await self._load()
        await self.start_background_save()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
