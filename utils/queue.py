from config import QUEUE_FILE, TEMP_PATH
import json
from collections import deque


class Queue:
    def save(self):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self.queue), f, ensure_ascii=False, indent=4)

    def __init__(self, initial_queue: list[int], save_frequency: int = 100):
        self.queue = deque(initial_queue)
        self.save_frequency = save_frequency
        self.steps_since_last_save = 0

        if not QUEUE_FILE.exists():
            self.save()
            return

        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            self.queue.extend(json.load(f))

    def __len__(self):
        return len(self.queue)

    def _check_save(self):
        self.steps_since_last_save += 1
        if self.steps_since_last_save >= self.save_frequency:
            self.save()
            self.steps_since_last_save = 0

    def popleft(self):
        self._check_save()
        return self.queue.popleft()

    def extend(self, extend_queue: list[int]):
        self._check_save()
        return self.queue.extend(extend_queue)

