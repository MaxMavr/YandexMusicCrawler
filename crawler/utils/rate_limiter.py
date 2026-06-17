from time import monotonic
import asyncio


class RateLimiter:
    def __init__(self, rate: float):
        self.interval = 1 / rate
        self.next_time = 0.0

    async def wait(self):
        now = monotonic()

        if now < self.next_time:
            await asyncio.sleep(self.next_time - now)

        self.next_time = monotonic() + self.interval
